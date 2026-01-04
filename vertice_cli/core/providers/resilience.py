"""
MAXIMUS Provider Resilience Patterns.

This module provides Maximus-specific resilience helpers built on top of core.resilience:
- HTTPX async client with HTTP/2 and connection pooling
- Tenacity retry decorators
- Combined circuit breaker + retry utilities

Base classes (CircuitBreaker, CircuitState, etc.) are re-exported from core.resilience
for convenience. Maximus-specific additions are defined here.

Based on 2025 best practices:
- Tenacity for async retry logic
- Circuit breaker pattern for resilience
- HTTPX with HTTP/2 and connection pooling

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

# Re-export base classes from core.resilience for convenience
from core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitOpenError as CircuitBreakerOpen,  # Alias for backward compat
    RetryConfig,
)


# =============================================================================
# MAXIMUS-SPECIFIC ADDITIONS
# =============================================================================


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

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
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
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
            reraise=True,
        ):
            with attempt:
                result = await func()
                breaker.record_success()
                return result
    except (httpx.HTTPError, RuntimeError, OSError, TimeoutError) as e:
        breaker.record_failure()
        raise e
    except Exception as e:
        breaker.record_failure()
        raise e
    raise RuntimeError("Retry exhausted")
