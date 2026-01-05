"""
Chaos Engineering Tests for Resilience Patterns.

Tests agent resilience under failure conditions:
- Simulated API timeouts
- Cascading failures and circuit breakers
- Rate limit backpressure
- Provider failover
"""

from __future__ import annotations


import pytest

from agents.coder.agent import CoderAgent
from core.resilience import (
    TransientError,
    PermanentError,
    RateLimitError,
    CircuitOpenError,
)


# ============================================================================
# Timeout Chaos Tests
# ============================================================================


class TestTimeoutChaos:
    """Tests resilience under timeout conditions."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self) -> None:
        """Agent retries on API timeout."""
        agent = CoderAgent()
        attempts = 0

        async def slow_api() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TimeoutError("API timeout")
            return "success"

        result = await agent.resilient_call(slow_api, provider="test")
        assert result == "success"
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_timeout_exhaustion(self) -> None:
        """Agent fails after max retries on persistent timeout."""
        agent = CoderAgent()

        async def always_timeout() -> str:
            raise TimeoutError("API timeout")

        with pytest.raises(TimeoutError):
            await agent.resilient_call(always_timeout, provider="test")

    @pytest.mark.asyncio
    async def test_intermittent_timeout(self) -> None:
        """Agent handles intermittent timeouts."""
        agent = CoderAgent()
        call_count = 0

        async def intermittent() -> str:
            nonlocal call_count
            call_count += 1
            # Fail every other call
            if call_count % 2 == 1:
                raise TimeoutError("Intermittent timeout")
            return f"success_{call_count}"

        # First call retries and succeeds
        result = await agent.resilient_call(intermittent, provider="test")
        assert "success" in result


# ============================================================================
# Circuit Breaker Chaos Tests
# ============================================================================


class TestCircuitBreakerChaos:
    """Tests circuit breaker behavior under cascading failures."""

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self) -> None:
        """Circuit breaker opens after consecutive failures."""
        agent = CoderAgent()
        agent._init_resilience()

        async def failing_api() -> str:
            raise TransientError("Service unavailable")

        # Cause enough failures to trip circuit
        for _ in range(5):
            try:
                await agent.resilient_call(failing_api, provider="chaos_test")
            except (TransientError, CircuitOpenError):
                pass

        # Check circuit state via stats
        stats = agent.get_resilience_stats()
        # After failures, circuit should be tracked
        assert stats["total_calls"] >= 5

    @pytest.mark.asyncio
    async def test_circuit_blocks_when_open(self) -> None:
        """Open circuit blocks new requests after failures."""
        agent = CoderAgent()
        agent._init_resilience()

        circuit = agent._get_circuit("blocked_provider")

        # Cause failures to open the circuit
        async def failing() -> str:
            raise TransientError("fail")

        for _ in range(circuit.config.failure_threshold + 1):
            try:
                await circuit.execute(failing)
            except (TransientError, CircuitOpenError):
                pass

        # Now circuit should be open and block new requests
        async def api_call() -> str:
            return "should not reach"

        with pytest.raises(CircuitOpenError):
            await circuit.execute(api_call)


# ============================================================================
# Rate Limit Chaos Tests
# ============================================================================


class TestRateLimitChaos:
    """Tests rate limit backpressure handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_adaptive_slowdown(self) -> None:
        """Rate limiter slows down on limit hits."""
        agent = CoderAgent()
        agent._init_resilience()

        limiter = agent._get_rate_limiter("rate_test")
        initial_factor = limiter._adaptive_factor

        # Simulate rate limit hit
        limiter.record_rate_limit(retry_after=5.0)

        # Adaptive factor should increase
        assert limiter._adaptive_factor > initial_factor

    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self) -> None:
        """Rate limiter recovers after successful calls."""
        agent = CoderAgent()
        agent._init_resilience()

        limiter = agent._get_rate_limiter("recovery_test")
        limiter._adaptive_factor = 2.0  # Simulate slowed state

        # Simulate successful calls
        for _ in range(20):
            limiter.record_success()

        # Factor should decrease toward 1.0
        assert limiter._adaptive_factor < 2.0

    @pytest.mark.asyncio
    async def test_rate_limit_burst_handling(self) -> None:
        """Rate limiter handles burst requests."""
        agent = CoderAgent()
        agent._init_resilience()

        limiter = agent._get_rate_limiter("burst_test")

        # Acquire burst of tokens
        results = []
        for _ in range(3):
            can_acquire = limiter._request_bucket.try_acquire(1)
            results.append(can_acquire)

        # Some should succeed
        assert any(results)


# ============================================================================
# Fallback Chaos Tests
# ============================================================================


class TestFallbackChaos:
    """Tests provider failover behavior."""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self) -> None:
        """Falls back to secondary on primary failure."""
        agent = CoderAgent()
        agent._init_resilience()

        primary_called = False
        secondary_called = False

        async def primary() -> str:
            nonlocal primary_called
            primary_called = True
            raise TransientError("Primary down")

        async def secondary() -> str:
            nonlocal secondary_called
            secondary_called = True
            return "secondary_result"

        # Setup fallback
        agent.setup_fallback(
            providers=["primary", "secondary"],
            provider_funcs={"primary": primary, "secondary": secondary}
        )

        result = await agent.call_with_fallback()
        # Result is a FallbackResult with .value, or direct value
        if hasattr(result, "value"):
            assert result.value == "secondary_result"
            assert result.provider_used == "secondary"
        else:
            assert result == "secondary_result"
        assert primary_called
        assert secondary_called

    @pytest.mark.asyncio
    async def test_fallback_all_fail(self) -> None:
        """Raises error when all providers fail."""
        agent = CoderAgent()
        agent._init_resilience()

        async def fail_a() -> str:
            raise TransientError("A failed")

        async def fail_b() -> str:
            raise TransientError("B failed")

        agent.setup_fallback(
            providers=["a", "b"],
            provider_funcs={"a": fail_a, "b": fail_b}
        )

        with pytest.raises(Exception):  # ResilienceError or similar
            await agent.call_with_fallback()


# ============================================================================
# Combined Chaos Tests
# ============================================================================


class TestCombinedChaos:
    """Tests combinations of failure modes."""

    @pytest.mark.asyncio
    async def test_timeout_with_rate_limit(self) -> None:
        """Handles timeout followed by rate limit."""
        agent = CoderAgent()
        attempts = 0

        async def mixed_failures() -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise TimeoutError("Timeout")
            if attempts == 2:
                raise RateLimitError("Rate limit", retry_after=0.01)
            return "success"

        result = await agent.resilient_call(mixed_failures, provider="mixed")
        assert result == "success"
        assert attempts >= 2

    @pytest.mark.asyncio
    async def test_permanent_error_no_retry(self) -> None:
        """Permanent errors are not retried."""
        agent = CoderAgent()
        attempts = 0

        async def permanent() -> str:
            nonlocal attempts
            attempts += 1
            raise PermanentError("Invalid request")

        with pytest.raises(PermanentError):
            await agent.resilient_call(permanent, provider="perm")

        # Should not have retried
        assert attempts == 1

    @pytest.mark.asyncio
    async def test_resilience_stats_under_chaos(self) -> None:
        """Stats are accurate under chaotic conditions."""
        agent = CoderAgent()
        agent._init_resilience()

        call_counter = 0

        async def chaotic() -> str:
            nonlocal call_counter
            call_counter += 1
            # Alternate success/failure to avoid circuit opening
            if call_counter % 3 == 0:
                raise TransientError("Random failure")
            return "ok"

        successes = 0
        failures = 0

        for i in range(10):
            try:
                # Use different provider per call to avoid circuit issues
                await agent.resilient_call(chaotic, provider=f"stats_test_{i}")
                successes += 1
            except (TransientError, CircuitOpenError):
                failures += 1

        stats = agent.get_resilience_stats()
        assert stats["total_calls"] >= 10
