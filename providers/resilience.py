"""
MAXIMUS Resilience Patterns.

Production-ready resilience for MAXIMUS provider with:
- Tenacity retry with exponential backoff
- Circuit breaker for fail-fast
- Connection pooling settings

Based on 2025 best practices:
- Tenacity for async retry logic
- Circuit breaker pattern for resilience
- HTTPX with HTTP/2 and connection pooling

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration.

    Attributes:
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before attempting recovery
        half_open_requests: Requests allowed in half-open state
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_requests: int = 3


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff.

    Attributes:
        max_attempts: Maximum retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        jitter: Add randomness to prevent thundering herd
    """

    max_attempts: int = 3
    initial_wait: float = 1.0
    max_wait: float = 10.0
    jitter: float = 0.5


@dataclass
class ConnectionPoolConfig:
    """HTTPX connection pool configuration.

    Attributes:
        max_connections: Maximum total connections
        max_keepalive: Maximum keepalive connections
        keepalive_expiry: Keepalive expiry in seconds
    """

    max_connections: int = 100
    max_keepalive: int = 20
    keepalive_expiry: float = 5.0


class CircuitBreaker:
    """Circuit breaker for MAXIMUS provider.

    Implements the circuit breaker pattern:
    - CLOSED: Normal operation, track failures
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Recovery test, allow limited requests

    Example:
        >>> breaker = CircuitBreaker()
        >>> async with breaker.call():
        ...     await client.post("/api/endpoint")
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration.
        """
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return self._state

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.config.recovery_timeout

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.half_open_requests:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN

    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self.state == CircuitState.OPEN

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time,
        }


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""


T = TypeVar("T")


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async retry with exponential backoff.

    Uses Tenacity for production-ready retry logic with:
    - Exponential backoff with jitter
    - Retry on transient HTTP errors
    - Configurable attempts and wait times

    Args:
        config: Retry configuration.

    Returns:
        Decorator function.

    Example:
        >>> @with_retry(RetryConfig(max_attempts=3))
        ... async def fetch_data():
        ...     return await client.get("/api/data")
    """
    cfg = config or RetryConfig()

    def decorator(
        func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        """Decorator that wraps function with retry logic."""
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            """Execute function with exponential backoff retry."""
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(cfg.max_attempts),
                wait=wait_exponential_jitter(
                    initial=cfg.initial_wait,
                    max=cfg.max_wait,
                    jitter=cfg.jitter,
                ),
                retry=retry_if_exception_type(
                    (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
                ),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)
            raise RuntimeError("Retry exhausted")

        return wrapper

    return decorator


def create_http_client(
    base_url: str,
    timeout: float = 30.0,
    pool_config: Optional[ConnectionPoolConfig] = None,
) -> httpx.AsyncClient:
    """Create HTTPX client with production settings.

    Features:
    - HTTP/2 enabled
    - Connection pooling
    - Configurable timeout

    Args:
        base_url: Base URL for requests.
        timeout: Request timeout in seconds.
        pool_config: Connection pool configuration.

    Returns:
        Configured HTTPX async client.
    """
    cfg = pool_config or ConnectionPoolConfig()

    limits = httpx.Limits(
        max_connections=cfg.max_connections,
        max_keepalive_connections=cfg.max_keepalive,
        keepalive_expiry=cfg.keepalive_expiry,
    )

    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout, connect=10.0),
        limits=limits,
        http2=True,
    )


async def call_with_resilience(
    func: Callable[[], Awaitable[T]],
    breaker: CircuitBreaker,
    retry_config: Optional[RetryConfig] = None,
) -> T:
    """Call function with circuit breaker and retry.

    Combines circuit breaker pattern with retry logic:
    1. Check if circuit is open (fail-fast)
    2. Call function with retry logic
    3. Record success/failure to circuit breaker

    Args:
        func: Async function to call (no-arg callable).
        breaker: Circuit breaker instance.
        retry_config: Retry configuration.

    Returns:
        Function result.

    Raises:
        CircuitBreakerOpen: If circuit is open.
    """
    if breaker.is_open():
        raise CircuitBreakerOpen("Circuit breaker is open")

    cfg = retry_config or RetryConfig()

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(cfg.max_attempts),
            wait=wait_exponential_jitter(
                initial=cfg.initial_wait,
                max=cfg.max_wait,
                jitter=cfg.jitter,
            ),
            retry=retry_if_exception_type(
                (httpx.TimeoutException, httpx.ConnectError)
            ),
            reraise=True,
        ):
            with attempt:
                result = await func()
                breaker.record_success()
                return result
    except Exception:
        breaker.record_failure()
        raise
    raise RuntimeError("Retry exhausted")
