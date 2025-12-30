"""
Phase 6 Resilience Module Tests.

Tests for production hardening:
- RetryHandler with exponential backoff
- CircuitBreaker pattern
- RateLimiter with token bucket
- FallbackHandler for multi-provider
- ResilienceMixin integration
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.resilience import (
    RetryHandler,
    RetryConfig,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
    RateLimitConfig,
    TokenBucket,
    FallbackHandler,
    FallbackConfig,
    ResilienceMixin,
    ErrorCategory,
    TransientError,
    PermanentError,
    RateLimitError,
    CircuitOpenError,
)
from core.resilience.types import CircuitBreakerConfig


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self) -> None:
        """Default config has sensible values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.jitter > 0

    def test_calculate_delay_exponential(self) -> None:
        """Delay increases exponentially."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=0)
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0

    def test_calculate_delay_max_cap(self) -> None:
        """Delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=10.0, jitter=0)
        assert config.calculate_delay(10) == 10.0

    def test_calculate_delay_retry_after(self) -> None:
        """Respects Retry-After header."""
        config = RetryConfig(respect_retry_after=True)
        assert config.calculate_delay(0, retry_after=5.0) == 5.0


class TestRetryHandler:
    """Tests for RetryHandler."""

    @pytest.mark.asyncio
    async def test_successful_call(self) -> None:
        """Successful call returns immediately."""
        handler = RetryHandler()

        async def success_func() -> str:
            return "success"

        result = await handler.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self) -> None:
        """Retries on transient errors."""
        handler = RetryHandler(config=RetryConfig(max_retries=3, base_delay=0.01))
        attempts = 0

        async def flaky_func() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise TransientError("Connection timeout")
            return "success"

        result = await handler.execute(flaky_func)
        assert result == "success"
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self) -> None:
        """Does not retry permanent errors."""
        handler = RetryHandler()

        async def permanent_fail() -> str:
            raise PermanentError("Invalid API key")

        with pytest.raises(PermanentError):
            await handler.execute(permanent_fail)

        stats = handler.get_stats()
        assert stats["retries"] == 0

    def test_classify_error_transient(self) -> None:
        """Classifies transient errors correctly."""
        handler = RetryHandler()
        assert handler.classify_error(TimeoutError("timeout")) == ErrorCategory.TRANSIENT
        assert handler.classify_error(ConnectionError("conn")) == ErrorCategory.TRANSIENT

    def test_classify_error_permanent(self) -> None:
        """Classifies permanent errors correctly."""
        handler = RetryHandler()
        assert handler.classify_error(ValueError("invalid")) == ErrorCategory.PERMANENT
        assert handler.classify_error(TypeError("wrong type")) == ErrorCategory.PERMANENT

    def test_classify_error_rate_limit(self) -> None:
        """Classifies rate limit errors correctly."""
        handler = RetryHandler()
        assert handler.classify_error(Exception("rate limit exceeded")) == ErrorCategory.RATE_LIMIT
        assert handler.classify_error(Exception("429 Too Many Requests")) == ErrorCategory.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_retry_decorator(self) -> None:
        """Decorator wraps function with retry logic."""
        handler = RetryHandler(config=RetryConfig(max_retries=2, base_delay=0.01))
        attempts = 0

        @handler.retry
        async def flaky() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TransientError("Temporary failure")
            return "ok"

        result = await flaky()
        assert result == "ok"
        assert attempts == 2


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_initial_state_closed(self) -> None:
        """Circuit starts in closed state."""
        circuit = CircuitBreaker(name="test")
        assert circuit.state == CircuitState.CLOSED
        assert circuit.is_closed

    @pytest.mark.asyncio
    async def test_opens_after_failures(self) -> None:
        """Opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=1.0)
        circuit = CircuitBreaker(name="test", config=config)

        async def fail() -> None:
            raise Exception("error")

        for _ in range(2):
            try:
                await circuit.execute(fail)
            except Exception:
                pass

        assert circuit.state == CircuitState.OPEN
        assert circuit.is_open

    @pytest.mark.asyncio
    async def test_blocks_when_open(self) -> None:
        """Blocks requests when open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=10.0)
        circuit = CircuitBreaker(name="test", config=config)

        async def fail() -> None:
            raise Exception("error")

        try:
            await circuit.execute(fail)
        except Exception:
            pass

        with pytest.raises(CircuitOpenError):
            await circuit.execute(fail)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self) -> None:
        """Transitions to half-open after timeout."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        circuit = CircuitBreaker(name="test", config=config)

        async def fail() -> None:
            raise Exception("error")

        try:
            await circuit.execute(fail)
        except Exception:
            pass

        await asyncio.sleep(0.02)

        # Next attempt should be allowed (half-open probe)
        async def success() -> str:
            return "ok"

        result = await circuit.execute(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self) -> None:
        """Closes after successes in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1, success_threshold=1, timeout=0.01
        )
        circuit = CircuitBreaker(name="test", config=config)

        async def fail() -> None:
            raise Exception("error")

        async def success() -> str:
            return "ok"

        try:
            await circuit.execute(fail)
        except Exception:
            pass

        await asyncio.sleep(0.02)
        await circuit.execute(success)

        assert circuit.state == CircuitState.CLOSED

    def test_get_stats(self) -> None:
        """Returns statistics."""
        circuit = CircuitBreaker(name="test")
        stats = circuit.get_stats()
        assert "state" in stats
        assert "failures" in stats
        assert "successes" in stats


class TestTokenBucket:
    """Tests for TokenBucket."""

    def test_initial_tokens(self) -> None:
        """Starts with full capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.available_tokens == 10

    def test_try_acquire_success(self) -> None:
        """Acquires tokens when available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.try_acquire(5)
        assert abs(bucket.available_tokens - 5) < 0.01  # Allow float precision

    def test_try_acquire_fail(self) -> None:
        """Fails when insufficient tokens."""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        assert not bucket.try_acquire(10)

    @pytest.mark.asyncio
    async def test_refill_over_time(self) -> None:
        """Refills tokens over time."""
        bucket = TokenBucket(capacity=10, refill_rate=100.0)  # Fast refill
        bucket.try_acquire(10)  # Empty bucket
        await asyncio.sleep(0.05)  # Wait for refill
        assert bucket.available_tokens > 0


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_acquire_success(self) -> None:
        """Acquires within limits."""
        config = RateLimitConfig(requests_per_minute=60, burst_size=10)
        limiter = RateLimiter(config=config)
        await limiter.acquire()  # Should not raise

    @pytest.mark.asyncio
    async def test_acquire_with_tokens(self) -> None:
        """Acquires with token estimation."""
        config = RateLimitConfig(tokens_per_minute=1000000)
        limiter = RateLimiter(config=config)
        await limiter.acquire(estimated_tokens=1000)

    def test_adaptive_factor_increases_on_limit(self) -> None:
        """Adaptive factor increases on rate limit."""
        limiter = RateLimiter()
        initial = limiter._adaptive_factor
        limiter.record_rate_limit()
        assert limiter._adaptive_factor > initial

    def test_adaptive_factor_decreases_on_success(self) -> None:
        """Adaptive factor decreases on success."""
        limiter = RateLimiter()
        limiter._adaptive_factor = 1.5
        for _ in range(10):
            limiter.record_success()
        assert limiter._adaptive_factor < 1.5

    def test_get_stats(self) -> None:
        """Returns statistics."""
        limiter = RateLimiter(name="test")
        stats = limiter.get_stats()
        assert stats["name"] == "test"
        assert "requests_made" in stats


class TestFallbackHandler:
    """Tests for FallbackHandler."""

    @pytest.mark.asyncio
    async def test_uses_first_provider(self) -> None:
        """Uses first successful provider."""
        handler = FallbackHandler(
            providers=["a", "b"],
            provider_funcs={
                "a": AsyncMock(return_value="result_a"),
                "b": AsyncMock(return_value="result_b"),
            },
        )

        result = await handler.execute()
        assert result.value == "result_a"
        assert result.provider_used == "a"

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self) -> None:
        """Falls back on provider failure."""
        handler = FallbackHandler(
            providers=["a", "b"],
            provider_funcs={
                "a": AsyncMock(side_effect=Exception("fail")),
                "b": AsyncMock(return_value="result_b"),
            },
        )

        result = await handler.execute()
        assert result.value == "result_b"
        assert result.provider_used == "b"
        assert result.total_attempts == 2

    @pytest.mark.asyncio
    async def test_all_fail_raises(self) -> None:
        """Raises when all providers fail."""
        handler = FallbackHandler(
            providers=["a", "b"],
            provider_funcs={
                "a": AsyncMock(side_effect=Exception("fail a")),
                "b": AsyncMock(side_effect=Exception("fail b")),
            },
        )

        with pytest.raises(Exception):  # ResilienceError
            await handler.execute()

    def test_get_healthy_providers(self) -> None:
        """Returns healthy providers."""
        handler = FallbackHandler(providers=["a", "b", "c"])
        handler._provider_status["b"].is_healthy = False

        healthy = handler.get_healthy_providers()
        assert "a" in healthy
        assert "b" not in healthy
        assert "c" in healthy


class TestResilienceMixin:
    """Tests for ResilienceMixin."""

    @pytest.mark.asyncio
    async def test_resilient_call_success(self) -> None:
        """Successful call through resilience stack."""

        class TestAgent(ResilienceMixin):
            pass

        agent = TestAgent()

        async def success() -> str:
            return "ok"

        result = await agent.resilient_call(success, provider="test")
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_resilient_call_with_retry(self) -> None:
        """Retries transient failures."""

        class TestAgent(ResilienceMixin):
            RETRY_CONFIG = RetryConfig(max_retries=3, base_delay=0.01)

        agent = TestAgent()
        attempts = 0

        async def flaky() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TransientError("temp fail")
            return "ok"

        result = await agent.resilient_call(flaky, provider="test")
        assert result == "ok"
        assert attempts == 2

    def test_get_resilience_stats(self) -> None:
        """Returns resilience statistics."""

        class TestAgent(ResilienceMixin):
            pass

        agent = TestAgent()
        agent._init_resilience()

        stats = agent.get_resilience_stats()
        assert "total_calls" in stats
        assert "retry" in stats
        assert "circuits" in stats

    def test_prometheus_metrics(self) -> None:
        """Generates Prometheus metrics."""

        class TestAgent(ResilienceMixin):
            agent_id = "test_agent"

        agent = TestAgent()
        agent._init_resilience()

        metrics = agent.get_prometheus_resilience_metrics()
        assert "resilience_calls_total" in metrics
        assert "test_agent" in metrics


class TestErrorTypes:
    """Tests for error type classifications."""

    def test_transient_error_category(self) -> None:
        """TransientError has correct category."""
        error = TransientError("temp")
        assert error.category == ErrorCategory.TRANSIENT

    def test_permanent_error_category(self) -> None:
        """PermanentError has correct category."""
        error = PermanentError("perm")
        assert error.category == ErrorCategory.PERMANENT

    def test_rate_limit_error_retry_after(self) -> None:
        """RateLimitError stores retry_after."""
        error = RateLimitError("limit", retry_after=30.0)
        assert error.retry_after == 30.0
        assert error.category == ErrorCategory.RATE_LIMIT

    def test_circuit_open_error_reset_time(self) -> None:
        """CircuitOpenError stores reset_time."""
        reset = datetime.utcnow() + timedelta(seconds=30)
        error = CircuitOpenError("open", reset_time=reset)
        assert error.reset_time == reset
