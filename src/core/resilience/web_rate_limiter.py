"""
Web Rate Limiter - Pre-configured rate limiting for web tools.
==============================================================

Provides global rate limiters for web operations:
- WebFetch: 10 req/min (conservative for content fetching)
- WebSearch: 5 req/min (conservative for search APIs)

Features:
- Token bucket algorithm with burst support
- Exponential backoff on rate limit hits
- Adaptive adjustment based on response codes
- Global singleton pattern for tool sharing

Best Practices (2025):
- Token bucket for handling traffic bursts
- Async-safe with asyncio.Lock
- Per-domain rate limiting option
- Jitter to prevent thundering herd

References:
- https://dev.to/zuplo/10-best-practices-for-api-rate-limiting-in-2025-358n
- https://aiolimiter.readthedocs.io/

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any

from .rate_limiter import TokenBucket
from .types import RateLimitError

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class WebRateLimitConfig:
    """Configuration for web rate limiting.

    Attributes:
        requests_per_minute: Max requests per minute
        burst_size: Max burst requests
        max_retries: Max retries on rate limit
        base_backoff: Initial backoff delay (seconds)
        max_backoff: Maximum backoff delay (seconds)
        jitter: Add random jitter to backoff
    """

    requests_per_minute: int = 10
    burst_size: int = 3
    max_retries: int = 3
    base_backoff: float = 1.0
    max_backoff: float = 30.0
    jitter: bool = True


# Default configurations per tool type
WEB_FETCH_CONFIG = WebRateLimitConfig(
    requests_per_minute=10,  # 10 req/min for URL fetching
    burst_size=3,
    max_retries=3,
    base_backoff=1.0,
    max_backoff=30.0,
)

WEB_SEARCH_CONFIG = WebRateLimitConfig(
    requests_per_minute=5,  # 5 req/min for search (more conservative)
    burst_size=2,
    max_retries=3,
    base_backoff=2.0,
    max_backoff=60.0,
)


# =============================================================================
# WEB RATE LIMITER
# =============================================================================


class WebRateLimiter:
    """Rate limiter optimized for web tools.

    Features:
    - Exponential backoff with jitter
    - Per-domain tracking (optional)
    - Adaptive rate adjustment
    - Stats and monitoring

    Example:
        limiter = WebRateLimiter.get_fetch_limiter()
        await limiter.acquire("example.com")
        response = await fetch_url(url)
        limiter.record_success()
    """

    def __init__(
        self,
        config: WebRateLimitConfig,
        name: str = "web",
    ) -> None:
        """Initialize web rate limiter.

        Args:
            config: Rate limit configuration
            name: Identifier for this limiter
        """
        self.config = config
        self.name = name

        # Main token bucket
        self._bucket = TokenBucket(
            capacity=config.burst_size,
            refill_rate=config.requests_per_minute / 60.0,
        )

        # Per-domain buckets (optional)
        self._domain_buckets: Dict[str, TokenBucket] = {}
        self._domain_lock = asyncio.Lock()

        # Stats
        self._stats = {
            "requests": 0,
            "rate_limited": 0,
            "retries": 0,
            "total_wait_time": 0.0,
        }

        # Backoff state
        self._consecutive_failures = 0
        self._last_rate_limit: Optional[float] = None

    async def acquire(
        self,
        domain: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Acquire permission to make a web request.

        Args:
            domain: Optional domain for per-domain limiting
            timeout: Maximum time to wait

        Raises:
            RateLimitError: If timeout exceeded
        """
        start = time.monotonic()

        # Check if we need backoff from previous rate limits
        if self._consecutive_failures > 0:
            backoff = self._calculate_backoff()
            logger.debug(
                f"[{self.name}] Backoff {backoff:.2f}s "
                f"(failures: {self._consecutive_failures})"
            )
            await asyncio.sleep(backoff)

        # Acquire from main bucket
        acquired = await self._bucket.acquire(timeout=timeout)
        if not acquired:
            self._stats["rate_limited"] += 1
            raise RateLimitError(
                f"Web rate limit exceeded for '{self.name}'",
                retry_after=self._bucket.time_until_available(),
            )

        # Acquire from domain bucket if specified
        if domain:
            domain_bucket = await self._get_domain_bucket(domain)
            remaining = timeout - (time.monotonic() - start)
            acquired = await domain_bucket.acquire(timeout=max(0, remaining))
            if not acquired:
                self._stats["rate_limited"] += 1
                raise RateLimitError(
                    f"Domain rate limit exceeded for '{domain}'",
                    retry_after=domain_bucket.time_until_available(),
                )

        self._stats["requests"] += 1
        self._stats["total_wait_time"] += time.monotonic() - start

    async def _get_domain_bucket(self, domain: str) -> TokenBucket:
        """Get or create per-domain bucket."""
        async with self._domain_lock:
            if domain not in self._domain_buckets:
                # Per-domain limits are more relaxed
                self._domain_buckets[domain] = TokenBucket(
                    capacity=self.config.burst_size * 2,
                    refill_rate=self.config.requests_per_minute / 30.0,
                )
            return self._domain_buckets[domain]

    def _calculate_backoff(self) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(
            self.config.base_backoff * (2 ** self._consecutive_failures),
            self.config.max_backoff,
        )

        if self.config.jitter:
            # Add 0-25% jitter
            delay += delay * random.uniform(0, 0.25)

        return delay

    def record_success(self) -> None:
        """Record successful request."""
        # Reset failure counter on success
        if self._consecutive_failures > 0:
            self._consecutive_failures = max(0, self._consecutive_failures - 1)

    def record_rate_limit(self, retry_after: Optional[float] = None) -> None:
        """Record rate limit hit for backoff adjustment.

        Args:
            retry_after: Suggested retry delay from server
        """
        self._consecutive_failures += 1
        self._stats["rate_limited"] += 1
        self._last_rate_limit = time.time()

        logger.warning(
            f"[{self.name}] Rate limit hit "
            f"(consecutive: {self._consecutive_failures})"
        )

    def record_retry(self) -> None:
        """Record retry attempt."""
        self._stats["retries"] += 1

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        domain: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute function with rate limiting and retries.

        Args:
            func: Async function to execute
            domain: Optional domain for limiting
            *args, **kwargs: Arguments for func

        Returns:
            Result from func

        Raises:
            Exception: If all retries exhausted
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                await self.acquire(domain=domain)
                result = await func(*args, **kwargs)
                self.record_success()
                return result

            except RateLimitError:
                self.record_rate_limit()
                if attempt < self.config.max_retries:
                    self.record_retry()
                    backoff = self._calculate_backoff()
                    logger.info(
                        f"[{self.name}] Retry {attempt + 1}/{self.config.max_retries} "
                        f"after {backoff:.2f}s"
                    )
                    await asyncio.sleep(backoff)
                else:
                    raise

            except Exception as e:
                last_error = e
                # Check if it's a rate limit response (429)
                if "429" in str(e) or "rate" in str(e).lower():
                    self.record_rate_limit()
                    if attempt < self.config.max_retries:
                        self.record_retry()
                        await asyncio.sleep(self._calculate_backoff())
                        continue
                raise

        if last_error:
            raise last_error
        raise RateLimitError(f"Rate limit retries exhausted for '{self.name}'")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "name": self.name,
            "requests": self._stats["requests"],
            "rate_limited": self._stats["rate_limited"],
            "retries": self._stats["retries"],
            "total_wait_time": round(self._stats["total_wait_time"], 2),
            "consecutive_failures": self._consecutive_failures,
            "available_tokens": self._bucket.available_tokens,
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "burst_size": self.config.burst_size,
            },
        }

    async def reset(self) -> None:
        """Reset rate limiter state."""
        self._bucket = TokenBucket(
            capacity=self.config.burst_size,
            refill_rate=self.config.requests_per_minute / 60.0,
        )
        self._domain_buckets.clear()
        self._consecutive_failures = 0
        self._stats = {
            "requests": 0,
            "rate_limited": 0,
            "retries": 0,
            "total_wait_time": 0.0,
        }
        logger.info(f"[{self.name}] Rate limiter reset")


# =============================================================================
# GLOBAL REGISTRY (Singleton Pattern)
# =============================================================================


class WebRateLimiterRegistry:
    """Global registry for web rate limiters.

    Provides singleton access to rate limiters for different web tools.
    This ensures all tool instances share the same rate limits.

    Example:
        # In WebFetchTool
        limiter = WebRateLimiterRegistry.get_fetch_limiter()
        await limiter.acquire()

        # In WebSearchTool
        limiter = WebRateLimiterRegistry.get_search_limiter()
        await limiter.acquire()
    """

    _instance: Optional["WebRateLimiterRegistry"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._fetch_limiter: Optional[WebRateLimiter] = None
        self._search_limiter: Optional[WebRateLimiter] = None
        self._custom_limiters: Dict[str, WebRateLimiter] = {}

    @classmethod
    def get_instance(cls) -> "WebRateLimiterRegistry":
        """Get singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_fetch_limiter(cls) -> WebRateLimiter:
        """Get rate limiter for web fetch operations."""
        registry = cls.get_instance()
        if registry._fetch_limiter is None:
            registry._fetch_limiter = WebRateLimiter(
                config=WEB_FETCH_CONFIG,
                name="web_fetch",
            )
        return registry._fetch_limiter

    @classmethod
    def get_search_limiter(cls) -> WebRateLimiter:
        """Get rate limiter for web search operations."""
        registry = cls.get_instance()
        if registry._search_limiter is None:
            registry._search_limiter = WebRateLimiter(
                config=WEB_SEARCH_CONFIG,
                name="web_search",
            )
        return registry._search_limiter

    @classmethod
    def get_limiter(
        cls,
        name: str,
        config: Optional[WebRateLimitConfig] = None,
    ) -> WebRateLimiter:
        """Get or create a custom rate limiter.

        Args:
            name: Unique limiter name
            config: Optional configuration

        Returns:
            WebRateLimiter instance
        """
        registry = cls.get_instance()
        if name not in registry._custom_limiters:
            registry._custom_limiters[name] = WebRateLimiter(
                config=config or WEB_FETCH_CONFIG,
                name=name,
            )
        return registry._custom_limiters[name]

    @classmethod
    def get_all_stats(cls) -> Dict[str, Any]:
        """Get stats from all registered limiters."""
        registry = cls.get_instance()
        stats = {}

        if registry._fetch_limiter:
            stats["web_fetch"] = registry._fetch_limiter.get_stats()
        if registry._search_limiter:
            stats["web_search"] = registry._search_limiter.get_stats()

        for name, limiter in registry._custom_limiters.items():
            stats[name] = limiter.get_stats()

        return stats

    @classmethod
    async def reset_all(cls) -> None:
        """Reset all rate limiters."""
        registry = cls.get_instance()

        if registry._fetch_limiter:
            await registry._fetch_limiter.reset()
        if registry._search_limiter:
            await registry._search_limiter.reset()

        for limiter in registry._custom_limiters.values():
            await limiter.reset()

        logger.info("All web rate limiters reset")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_fetch_limiter() -> WebRateLimiter:
    """Get the global web fetch rate limiter."""
    return WebRateLimiterRegistry.get_fetch_limiter()


def get_search_limiter() -> WebRateLimiter:
    """Get the global web search rate limiter."""
    return WebRateLimiterRegistry.get_search_limiter()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "WebRateLimitConfig",
    "WebRateLimiter",
    "WebRateLimiterRegistry",
    "WEB_FETCH_CONFIG",
    "WEB_SEARCH_CONFIG",
    "get_fetch_limiter",
    "get_search_limiter",
]
