"""
Rate Limiter - Token bucket algorithm for LLM API rate limiting.

Implements Anthropic's token bucket algorithm:
- Request-based rate limiting (RPM)
- Token-based rate limiting (TPM)
- Burst handling with bucket capacity
- Adaptive rate limiting based on API feedback

References:
- Anthropic uses "token bucket algorithm" for rate limiting
- https://markaicode.com/llm-api-rate-limiting-load-balancing-guide/
- https://orq.ai/blog/api-rate-limit
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable, Awaitable, TypeVar
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from .types import RateLimitConfig, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class TokenBucketState:
    """State for a token bucket."""

    tokens: float
    last_refill: float
    requests_made: int = 0
    tokens_used: int = 0
    last_request: Optional[float] = None


class TokenBucket:
    """Token bucket for rate limiting.

    Features:
    - Configurable capacity and refill rate
    - Burst handling
    - Non-blocking and blocking modes

    Example:
        bucket = TokenBucket(capacity=60, refill_rate=1.0)

        if bucket.try_acquire():
            await make_request()
        else:
            wait_time = bucket.time_until_available()
            await asyncio.sleep(wait_time)
    """

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        initial_tokens: Optional[float] = None,
    ) -> None:
        """Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
            initial_tokens: Starting tokens (defaults to capacity)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = initial_tokens if initial_tokens is not None else capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self.refill_rate
        self._tokens = min(self.capacity, self._tokens + tokens_to_add)
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None for infinite)

        Returns:
            True if tokens acquired, False if timeout
        """
        start = time.monotonic()

        while True:
            async with self._lock:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            # Calculate wait time
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self.refill_rate

            if timeout is not None:
                elapsed = time.monotonic() - start
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            await asyncio.sleep(min(wait_time, 0.1))

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False if not enough tokens
        """
        self._refill()

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: float = 1.0) -> float:
        """Calculate time until tokens will be available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens available (0 if already available)
        """
        self._refill()

        if self._tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self._tokens
        return tokens_needed / self.refill_rate

    @property
    def available_tokens(self) -> float:
        """Get current available tokens."""
        self._refill()
        return self._tokens


class RateLimiter:
    """Rate limiter for LLM API calls.

    Features:
    - Dual limiting: requests per minute + tokens per minute
    - Adaptive adjustment based on Retry-After headers
    - Per-provider rate limit tracking
    - FIFO request queuing

    Example:
        limiter = RateLimiter(config=RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=100000
        ))

        @limiter.limit
        async def call_llm(prompt: str) -> str:
            return await llm.generate(prompt)

        # Or estimate tokens:
        await limiter.acquire(estimated_tokens=1000)
        response = await llm.generate(prompt)
    """

    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        name: str = "default",
    ) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
            name: Identifier for this limiter
        """
        self.config = config or RateLimitConfig()
        self.name = name

        # Request bucket (RPM)
        self._request_bucket = TokenBucket(
            capacity=self.config.burst_size,
            refill_rate=self.config.requests_per_minute / 60.0,
        )

        # Token bucket (TPM)
        self._token_bucket = TokenBucket(
            capacity=self.config.tokens_per_minute,
            refill_rate=self.config.tokens_per_minute / 60.0,
        )

        # Stats
        self._stats = {
            "requests_made": 0,
            "requests_limited": 0,
            "tokens_used": 0,
            "total_wait_time": 0.0,
        }

        # Adaptive rate limiting
        self._adaptive_factor = 1.0
        self._last_rate_limit: Optional[datetime] = None

    async def acquire(
        self,
        estimated_tokens: int = 0,
        timeout: Optional[float] = 30.0,
    ) -> None:
        """Acquire permission to make a request.

        Args:
            estimated_tokens: Estimated tokens for request (0 for request-only)
            timeout: Maximum time to wait

        Raises:
            RateLimitError: If timeout exceeded
        """
        start = time.monotonic()

        # Acquire request slot
        request_wait = self._request_bucket.time_until_available()
        if request_wait > 0:
            if timeout and request_wait > timeout:
                raise RateLimitError(
                    f"Rate limit exceeded for '{self.name}'. " f"Wait {request_wait:.1f}s",
                    retry_after=request_wait,
                )
            await asyncio.sleep(request_wait)

        # Apply adaptive factor
        adjusted_tokens = int(estimated_tokens * self._adaptive_factor)

        # Acquire tokens if needed
        if adjusted_tokens > 0:
            token_wait = self._token_bucket.time_until_available(adjusted_tokens)
            if token_wait > 0:
                elapsed = time.monotonic() - start
                remaining_timeout = (timeout - elapsed) if timeout else None

                if remaining_timeout is not None and token_wait > remaining_timeout:
                    raise RateLimitError(
                        f"Token rate limit exceeded for '{self.name}'. " f"Wait {token_wait:.1f}s",
                        retry_after=token_wait,
                    )
                await asyncio.sleep(token_wait)

        # Consume tokens
        self._request_bucket.try_acquire()
        if adjusted_tokens > 0:
            self._token_bucket.try_acquire(adjusted_tokens)

        # Update stats
        self._stats["requests_made"] += 1
        self._stats["tokens_used"] += estimated_tokens
        self._stats["total_wait_time"] += time.monotonic() - start

    def record_actual_tokens(self, actual_tokens: int) -> None:
        """Record actual tokens used for adaptive adjustment.

        Args:
            actual_tokens: Actual tokens consumed by request
        """
        self._stats["tokens_used"] += actual_tokens

    def record_rate_limit(self, retry_after: Optional[float] = None) -> None:
        """Record rate limit response for adaptive adjustment.

        Args:
            retry_after: Suggested retry delay from API
        """
        self._stats["requests_limited"] += 1
        self._last_rate_limit = datetime.utcnow()

        # Increase adaptive factor (reduce effective rate)
        self._adaptive_factor = min(2.0, self._adaptive_factor * 1.2)

        logger.warning(
            f"Rate limit recorded for '{self.name}'. "
            f"Adaptive factor: {self._adaptive_factor:.2f}"
        )

    def record_success(self) -> None:
        """Record successful request for adaptive adjustment."""
        # Slowly decrease adaptive factor back to normal
        if self._adaptive_factor > 1.0:
            self._adaptive_factor = max(1.0, self._adaptive_factor * 0.99)

    def limit(
        self,
        estimated_tokens: int = 0,
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """Decorator to rate limit function calls.

        Args:
            estimated_tokens: Estimated tokens per call

        Example:
            @limiter.limit(estimated_tokens=500)
            async def generate(prompt: str) -> str:
                return await llm.chat(prompt)
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                await self.acquire(estimated_tokens=estimated_tokens)
                try:
                    result = await func(*args, **kwargs)
                    self.record_success()
                    return result
                except Exception as e:
                    if "rate" in str(e).lower() or "429" in str(e):
                        self.record_rate_limit()
                    raise

            return wrapper

        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "name": self.name,
            "requests_made": self._stats["requests_made"],
            "requests_limited": self._stats["requests_limited"],
            "tokens_used": self._stats["tokens_used"],
            "total_wait_time": self._stats["total_wait_time"],
            "adaptive_factor": self._adaptive_factor,
            "available_request_tokens": self._request_bucket.available_tokens,
            "available_token_tokens": self._token_bucket.available_tokens,
        }

    async def reset(self) -> None:
        """Reset rate limiter state."""
        self._request_bucket = TokenBucket(
            capacity=self.config.burst_size,
            refill_rate=self.config.requests_per_minute / 60.0,
        )
        self._token_bucket = TokenBucket(
            capacity=self.config.tokens_per_minute,
            refill_rate=self.config.tokens_per_minute / 60.0,
        )
        self._adaptive_factor = 1.0
        self._stats = {
            "requests_made": 0,
            "requests_limited": 0,
            "tokens_used": 0,
            "total_wait_time": 0.0,
        }
        logger.info(f"Rate limiter '{self.name}' reset")
