"""
Tests for Web Rate Limiter.

Tests rate limiting for web tools (fetch, search).

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import time

import pytest

from core.resilience.web_rate_limiter import (
    WebRateLimitConfig,
    WebRateLimiter,
    WebRateLimiterRegistry,
    get_fetch_limiter,
    get_search_limiter,
    WEB_FETCH_CONFIG,
    WEB_SEARCH_CONFIG,
)
from core.resilience import RateLimitError


# =============================================================================
# CONFIG TESTS
# =============================================================================


class TestWebRateLimitConfig:
    """Tests for WebRateLimitConfig."""

    def test_default_config(self) -> None:
        """Default config values."""
        config = WebRateLimitConfig()

        assert config.requests_per_minute == 10
        assert config.burst_size == 3
        assert config.max_retries == 3
        assert config.jitter is True

    def test_custom_config(self) -> None:
        """Custom config values."""
        config = WebRateLimitConfig(
            requests_per_minute=20,
            burst_size=5,
            max_retries=5,
            base_backoff=2.0,
        )

        assert config.requests_per_minute == 20
        assert config.burst_size == 5
        assert config.base_backoff == 2.0

    def test_fetch_config(self) -> None:
        """Fetch config preset."""
        assert WEB_FETCH_CONFIG.requests_per_minute == 10
        assert WEB_FETCH_CONFIG.burst_size == 3

    def test_search_config(self) -> None:
        """Search config preset."""
        assert WEB_SEARCH_CONFIG.requests_per_minute == 5
        assert WEB_SEARCH_CONFIG.burst_size == 2


# =============================================================================
# WEB RATE LIMITER TESTS
# =============================================================================


class TestWebRateLimiter:
    """Tests for WebRateLimiter."""

    @pytest.fixture
    def limiter(self) -> WebRateLimiter:
        """Create test limiter."""
        config = WebRateLimitConfig(
            requests_per_minute=60,  # 1 per second for fast tests
            burst_size=3,
            max_retries=2,
            base_backoff=0.1,
            jitter=False,
        )
        return WebRateLimiter(config, name="test")

    @pytest.mark.asyncio
    async def test_acquire_success(self, limiter: WebRateLimiter) -> None:
        """Single acquire succeeds."""
        await limiter.acquire()
        stats = limiter.get_stats()

        assert stats["requests"] == 1
        assert stats["rate_limited"] == 0

    @pytest.mark.asyncio
    async def test_acquire_burst(self, limiter: WebRateLimiter) -> None:
        """Burst requests within limit."""
        for _ in range(3):  # burst_size = 3
            await limiter.acquire()

        stats = limiter.get_stats()
        assert stats["requests"] == 3

    @pytest.mark.asyncio
    async def test_acquire_with_domain(self, limiter: WebRateLimiter) -> None:
        """Acquire with domain tracking."""
        await limiter.acquire(domain="example.com")
        await limiter.acquire(domain="example.com")

        stats = limiter.get_stats()
        assert stats["requests"] == 2

    @pytest.mark.asyncio
    async def test_acquire_timeout(self) -> None:
        """Acquire times out when rate limited."""
        config = WebRateLimitConfig(
            requests_per_minute=1,  # Very slow
            burst_size=1,
        )
        limiter = WebRateLimiter(config, name="slow")

        # First request succeeds
        await limiter.acquire(timeout=1.0)

        # Second should timeout
        with pytest.raises(RateLimitError):
            await limiter.acquire(timeout=0.1)

    @pytest.mark.asyncio
    async def test_record_success(self, limiter: WebRateLimiter) -> None:
        """Record success resets failure counter."""
        limiter._consecutive_failures = 3
        limiter.record_success()

        assert limiter._consecutive_failures == 2  # Decrements by 1

    @pytest.mark.asyncio
    async def test_record_rate_limit(self, limiter: WebRateLimiter) -> None:
        """Record rate limit increments failure counter."""
        limiter.record_rate_limit()

        assert limiter._consecutive_failures == 1
        assert limiter._stats["rate_limited"] == 1

    @pytest.mark.asyncio
    async def test_backoff_calculation(self, limiter: WebRateLimiter) -> None:
        """Exponential backoff calculation."""
        limiter._consecutive_failures = 0
        backoff0 = limiter._calculate_backoff()

        limiter._consecutive_failures = 1
        backoff1 = limiter._calculate_backoff()

        limiter._consecutive_failures = 2
        backoff2 = limiter._calculate_backoff()

        # Exponential growth
        assert backoff1 > backoff0
        assert backoff2 > backoff1

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, limiter: WebRateLimiter) -> None:
        """Execute with retry succeeds."""

        async def mock_func() -> str:
            return "success"

        result = await limiter.execute_with_retry(mock_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_retries(self, limiter: WebRateLimiter) -> None:
        """Execute with retry handles transient failures."""
        call_count = 0

        async def mock_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("429 Too Many Requests")
            return "success"

        result = await limiter.execute_with_retry(mock_func)

        assert result == "success"
        assert call_count == 2
        assert limiter._stats["retries"] >= 1

    @pytest.mark.asyncio
    async def test_get_stats(self, limiter: WebRateLimiter) -> None:
        """Get stats returns correct data."""
        await limiter.acquire()
        stats = limiter.get_stats()

        assert stats["name"] == "test"
        assert stats["requests"] == 1
        assert "config" in stats
        assert stats["config"]["requests_per_minute"] == 60

    @pytest.mark.asyncio
    async def test_reset(self, limiter: WebRateLimiter) -> None:
        """Reset clears state."""
        await limiter.acquire()
        limiter._consecutive_failures = 5

        await limiter.reset()

        assert limiter._stats["requests"] == 0
        assert limiter._consecutive_failures == 0


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestWebRateLimiterRegistry:
    """Tests for WebRateLimiterRegistry."""

    def test_singleton(self) -> None:
        """Registry is singleton."""
        registry1 = WebRateLimiterRegistry.get_instance()
        registry2 = WebRateLimiterRegistry.get_instance()

        assert registry1 is registry2

    def test_get_fetch_limiter(self) -> None:
        """Get fetch limiter returns consistent instance."""
        limiter1 = WebRateLimiterRegistry.get_fetch_limiter()
        limiter2 = WebRateLimiterRegistry.get_fetch_limiter()

        assert limiter1 is limiter2
        assert limiter1.name == "web_fetch"

    def test_get_search_limiter(self) -> None:
        """Get search limiter returns consistent instance."""
        limiter1 = WebRateLimiterRegistry.get_search_limiter()
        limiter2 = WebRateLimiterRegistry.get_search_limiter()

        assert limiter1 is limiter2
        assert limiter1.name == "web_search"

    def test_get_custom_limiter(self) -> None:
        """Get custom limiter creates new instance."""
        config = WebRateLimitConfig(requests_per_minute=100)
        limiter = WebRateLimiterRegistry.get_limiter("custom", config)

        assert limiter.name == "custom"
        assert limiter.config.requests_per_minute == 100

    def test_get_all_stats(self) -> None:
        """Get all stats includes all limiters."""
        # Ensure limiters exist
        WebRateLimiterRegistry.get_fetch_limiter()
        WebRateLimiterRegistry.get_search_limiter()

        stats = WebRateLimiterRegistry.get_all_stats()

        assert "web_fetch" in stats
        assert "web_search" in stats

    @pytest.mark.asyncio
    async def test_reset_all(self) -> None:
        """Reset all clears all limiters."""
        fetch = WebRateLimiterRegistry.get_fetch_limiter()
        search = WebRateLimiterRegistry.get_search_limiter()

        await fetch.acquire()
        await search.acquire()

        await WebRateLimiterRegistry.reset_all()

        assert fetch._stats["requests"] == 0
        assert search._stats["requests"] == 0


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_fetch_limiter(self) -> None:
        """get_fetch_limiter returns registry limiter."""
        limiter = get_fetch_limiter()

        assert limiter.name == "web_fetch"
        assert limiter.config.requests_per_minute == 10

    def test_get_search_limiter(self) -> None:
        """get_search_limiter returns registry limiter."""
        limiter = get_search_limiter()

        assert limiter.name == "web_search"
        assert limiter.config.requests_per_minute == 5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestRateLimiterIntegration:
    """Integration tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_burst_then_wait(self) -> None:
        """Burst followed by rate-limited wait."""
        config = WebRateLimitConfig(
            requests_per_minute=60,  # 1/sec
            burst_size=2,
        )
        limiter = WebRateLimiter(config, name="burst_test")

        start = time.monotonic()

        # Burst (instant)
        await limiter.acquire(timeout=0.1)
        await limiter.acquire(timeout=0.1)

        # Third should wait for refill
        await limiter.acquire(timeout=2.0)

        elapsed = time.monotonic() - start
        # Should have waited ~1 second for refill
        assert elapsed > 0.5

    @pytest.mark.asyncio
    async def test_adaptive_backoff(self) -> None:
        """Backoff increases with consecutive failures."""
        config = WebRateLimitConfig(
            requests_per_minute=60,
            base_backoff=0.1,
            max_backoff=1.0,
            jitter=False,
        )
        limiter = WebRateLimiter(config, name="backoff_test")

        # Simulate failures
        limiter.record_rate_limit()
        backoff1 = limiter._calculate_backoff()

        limiter.record_rate_limit()
        backoff2 = limiter._calculate_backoff()

        limiter.record_rate_limit()
        backoff3 = limiter._calculate_backoff()

        # Exponential growth
        assert backoff2 == backoff1 * 2
        assert backoff3 == backoff2 * 2

    @pytest.mark.asyncio
    async def test_success_reduces_backoff(self) -> None:
        """Success gradually reduces backoff."""
        config = WebRateLimitConfig(
            requests_per_minute=60,
            base_backoff=0.1,
            jitter=False,
        )
        limiter = WebRateLimiter(config, name="recovery_test")

        # Build up failures
        for _ in range(5):
            limiter.record_rate_limit()

        assert limiter._consecutive_failures == 5

        # Successes reduce it
        for _ in range(5):
            limiter.record_success()

        assert limiter._consecutive_failures == 0
