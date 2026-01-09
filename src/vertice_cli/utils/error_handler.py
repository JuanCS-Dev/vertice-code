"""Unified Error Handling Utilities following Big 3 patterns (2025-2026).

This module provides production-grade error handling patterns based on
best practices from Anthropic, Google, and OpenAI:

- Exponential backoff with jitter (all 3)
- Circuit breaker pattern (Google/OpenAI)
- Retry-After header honoring (Anthropic)
- Transient vs logic error distinction
- Fallback strategies with degraded mode
- Token bucket rate limiting

References:
    - https://cookbook.openai.com/examples/how_to_handle_rate_limits
    - https://cloud.google.com/blog/products/ai-machine-learning/learn-how-to-handle-429-resource-exhaustion-errors
    - Anthropic API rate limits documentation

Key Features:
    - RetryPolicy with exponential backoff + jitter
    - CircuitBreaker with half-open recovery
    - ErrorClassifier for transient vs permanent errors
    - FallbackChain for graceful degradation
    - Structured error reporting

Design Principles:
    - Never silently swallow exceptions (CODE_CONSTITUTION)
    - Fail fast for permanent errors
    - Retry intelligently for transient errors
    - Provide observability through logging
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Optional,
    Type,
    TypeVar,
)


T = TypeVar("T")


class ErrorCategory(Enum):
    """Error categories for classification.

    Based on HTTP status code patterns from OpenAI/Anthropic/Google.
    """

    TRANSIENT = "transient"  # 429, 500, 502, 503, 504, 529 - retry
    PERMANENT = "permanent"  # 400, 401, 403, 404 - don't retry
    RATE_LIMIT = "rate_limit"  # 429 specifically - backoff
    OVERLOADED = "overloaded"  # 529 (Anthropic) - longer backoff
    TIMEOUT = "timeout"  # Request timeout - retry with backoff
    UNKNOWN = "unknown"  # Unclassified


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast, no requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass(frozen=True)
class ErrorContext:
    """Rich context for error reporting.

    Attributes:
        operation: Name of the operation.
        component: Component or module name.
        attempt: Current retry attempt number.
        max_attempts: Maximum retry attempts.
        elapsed_ms: Time elapsed since first attempt.
        category: Error category classification.
    """

    operation: str
    component: str = ""
    attempt: int = 1
    max_attempts: int = 1
    elapsed_ms: float = 0.0
    category: ErrorCategory = ErrorCategory.UNKNOWN

    def format(self, error: Exception) -> str:
        """Format error with full context."""
        parts = []
        if self.component:
            parts.append(f"[{self.component}]")
        parts.append(f"{self.operation}")
        if self.max_attempts > 1:
            parts.append(f"(attempt {self.attempt}/{self.max_attempts})")
        parts.append(f": {type(error).__name__}: {error}")
        if self.category != ErrorCategory.UNKNOWN:
            parts.append(f"[{self.category.value}]")
        return " ".join(parts)


@dataclass
class RetryPolicy:
    """Configurable retry policy with exponential backoff and jitter.

    Follows the "gold standard" pattern recommended by all Big 3:
    - Exponential backoff: wait doubles each attempt
    - Jitter: random variation prevents thundering herd
    - Max delay cap: prevents excessive waits
    - Retry-After header support

    Attributes:
        max_attempts: Maximum retry attempts (default: 5).
        base_delay: Initial delay in seconds (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 60.0).
        exponential_base: Backoff multiplier (default: 2.0).
        jitter: Jitter factor 0-1 (default: 0.1).
        retry_on: Exception types to retry.
    """

    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    retry_on: tuple[Type[Exception], ...] = (Exception,)

    def calculate_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculate delay for given attempt with jitter.

        Args:
            attempt: Current attempt number (1-based).
            retry_after: Optional Retry-After header value.

        Returns:
            Delay in seconds with jitter applied.
        """
        # Honor Retry-After header if provided (Anthropic pattern)
        if retry_after is not None:
            return min(retry_after, self.max_delay)

        # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))

        # Apply max cap
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if should retry based on attempt and error type."""
        if attempt >= self.max_attempts:
            return False
        return isinstance(error, self.retry_on)


# Pre-configured policies
AGGRESSIVE_RETRY = RetryPolicy(max_attempts=5, base_delay=0.5, max_delay=30.0)
CONSERVATIVE_RETRY = RetryPolicy(max_attempts=3, base_delay=2.0, max_delay=60.0)
API_RETRY = RetryPolicy(max_attempts=5, base_delay=1.0, max_delay=60.0, jitter=0.2)


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern for preventing cascade failures.

    Based on Google/OpenAI recommendations:
    - CLOSED: Normal operation, requests flow through
    - OPEN: Failing fast, no requests for recovery_timeout
    - HALF_OPEN: Testing with limited requests

    Attributes:
        failure_threshold: Failures before opening (default: 5).
        recovery_timeout: Seconds before half-open (default: 30).
        half_open_max_calls: Max calls in half-open state (default: 3).
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)
    _half_open_calls: int = field(default=0, repr=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        state = self.state

        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        else:  # HALF_OPEN
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

    def record_success(self) -> None:
        """Record successful request."""
        if self._state == CircuitState.HALF_OPEN:
            # Successful in half-open, close circuit
            self._state = CircuitState.CLOSED
            self._failure_count = 0
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self) -> None:
        """Record failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Failed in half-open, open circuit again
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            # Threshold reached, open circuit
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0


class ErrorClassifier:
    """Classify errors into categories for appropriate handling.

    Based on HTTP status codes from Anthropic/OpenAI/Google APIs.
    """

    # HTTP status code mappings
    TRANSIENT_CODES = {500, 502, 503, 504}
    RATE_LIMIT_CODES = {429}
    OVERLOADED_CODES = {529}  # Anthropic-specific
    PERMANENT_CODES = {400, 401, 403, 404, 405, 422}

    @classmethod
    def classify(cls, error: Exception) -> ErrorCategory:
        """Classify error into category.

        Args:
            error: The exception to classify.

        Returns:
            ErrorCategory for the error.
        """
        # Check for status code in common exception patterns
        status_code = cls._extract_status_code(error)

        if status_code:
            if status_code in cls.RATE_LIMIT_CODES:
                return ErrorCategory.RATE_LIMIT
            if status_code in cls.OVERLOADED_CODES:
                return ErrorCategory.OVERLOADED
            if status_code in cls.TRANSIENT_CODES:
                return ErrorCategory.TRANSIENT
            if status_code in cls.PERMANENT_CODES:
                return ErrorCategory.PERMANENT

        # Check exception type patterns
        error_name = type(error).__name__.lower()
        error_msg = str(error).lower()

        if "timeout" in error_name or "timeout" in error_msg:
            return ErrorCategory.TIMEOUT
        if "rate" in error_msg and "limit" in error_msg:
            return ErrorCategory.RATE_LIMIT
        if "overload" in error_msg:
            return ErrorCategory.OVERLOADED
        if any(t in error_name for t in ["connection", "network", "temporary"]):
            return ErrorCategory.TRANSIENT
        if any(t in error_name for t in ["validation", "invalid", "notfound"]):
            return ErrorCategory.PERMANENT

        return ErrorCategory.UNKNOWN

    @classmethod
    def _extract_status_code(cls, error: Exception) -> Optional[int]:
        """Extract HTTP status code from exception if available."""
        # Common patterns for HTTP status codes
        for attr in ["status_code", "status", "code", "response"]:
            if hasattr(error, attr):
                val = getattr(error, attr)
                if isinstance(val, int):
                    return val
                if hasattr(val, "status_code"):
                    return val.status_code
        return None

    @classmethod
    def should_retry(cls, error: Exception) -> bool:
        """Check if error is retryable."""
        category = cls.classify(error)
        return category in {
            ErrorCategory.TRANSIENT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.OVERLOADED,
            ErrorCategory.TIMEOUT,
        }

    @classmethod
    def extract_retry_after(cls, error: Exception) -> Optional[float]:
        """Extract Retry-After value from error if available."""
        # Check for Retry-After header in response
        for attr in ["response", "headers"]:
            if hasattr(error, attr):
                obj = getattr(error, attr)
                headers = getattr(obj, "headers", obj) if obj else {}
                if isinstance(headers, dict):
                    retry_after = headers.get("Retry-After") or headers.get("retry-after")
                    if retry_after:
                        try:
                            return float(retry_after)
                        except (ValueError, TypeError):
                            pass
        return None


@dataclass
class FallbackChain(Generic[T]):
    """Chain of fallback strategies for graceful degradation.

    Google pattern: When all else fails, have a fallback strategy.

    Attributes:
        fallbacks: List of fallback callables.
        default: Default value if all fallbacks fail.
    """

    fallbacks: list[Callable[[], T]] = field(default_factory=list)
    default: Optional[T] = None

    def add(self, fallback: Callable[[], T]) -> FallbackChain[T]:
        """Add a fallback to the chain."""
        self.fallbacks.append(fallback)
        return self

    def execute(self, logger: Optional[logging.Logger] = None) -> Optional[T]:
        """Execute fallbacks in order until one succeeds."""
        for i, fallback in enumerate(self.fallbacks):
            try:
                return fallback()
            except Exception as e:
                if logger:
                    logger.warning(f"Fallback {i+1}/{len(self.fallbacks)} failed: {e}")
                continue
        return self.default


async def retry_with_backoff(
    coro_factory: Callable[[], Awaitable[T]],
    policy: RetryPolicy = API_RETRY,
    circuit_breaker: Optional[CircuitBreaker] = None,
    logger: Optional[logging.Logger] = None,
    context: str = "",
) -> T:
    """Execute async operation with retry, backoff, and circuit breaker.

    The recommended pattern from all Big 3 providers:
    1. Check circuit breaker
    2. Attempt operation
    3. On failure, classify error
    4. If retryable, wait with exponential backoff + jitter
    5. Retry up to max_attempts

    Args:
        coro_factory: Factory that creates the coroutine (called on each attempt).
        policy: Retry policy configuration.
        circuit_breaker: Optional circuit breaker.
        logger: Logger for retry attempts.
        context: Context description for logging.

    Returns:
        Result of successful operation.

    Raises:
        The last exception if all retries exhausted.
        CircuitOpenError if circuit is open.
    """
    last_error: Optional[Exception] = None
    start_time = time.time()

    for attempt in range(1, policy.max_attempts + 1):
        # Check circuit breaker
        if circuit_breaker and not circuit_breaker.allow_request():
            raise CircuitOpenError(f"Circuit breaker open for {context or 'operation'}")

        try:
            result = await coro_factory()

            # Record success
            if circuit_breaker:
                circuit_breaker.record_success()

            return result

        except Exception as e:
            last_error = e
            category = ErrorClassifier.classify(e)

            # Record failure in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_failure()

            # Check if should retry
            if not policy.should_retry(attempt, e) or not ErrorClassifier.should_retry(e):
                if logger:
                    elapsed = (time.time() - start_time) * 1000
                    ctx = ErrorContext(
                        operation=context or "operation",
                        attempt=attempt,
                        max_attempts=policy.max_attempts,
                        elapsed_ms=elapsed,
                        category=category,
                    )
                    logger.error(f"Non-retryable error: {ctx.format(e)}")
                raise

            # Calculate delay
            retry_after = ErrorClassifier.extract_retry_after(e)
            delay = policy.calculate_delay(attempt, retry_after)

            if logger:
                elapsed = (time.time() - start_time) * 1000
                ctx = ErrorContext(
                    operation=context or "operation",
                    attempt=attempt,
                    max_attempts=policy.max_attempts,
                    elapsed_ms=elapsed,
                    category=category,
                )
                logger.warning(f"Retrying after {delay:.2f}s: {ctx.format(e)}")

            await asyncio.sleep(delay)

    # All retries exhausted
    if last_error:
        raise last_error
    raise RuntimeError("Retry loop exited without result or error")


def retry_sync_with_backoff(
    func: Callable[[], T],
    policy: RetryPolicy = API_RETRY,
    circuit_breaker: Optional[CircuitBreaker] = None,
    logger: Optional[logging.Logger] = None,
    context: str = "",
) -> T:
    """Synchronous version of retry_with_backoff."""
    last_error: Optional[Exception] = None
    start_time = time.time()

    for attempt in range(1, policy.max_attempts + 1):
        if circuit_breaker and not circuit_breaker.allow_request():
            raise CircuitOpenError(f"Circuit breaker open for {context or 'operation'}")

        try:
            result = func()
            if circuit_breaker:
                circuit_breaker.record_success()
            return result

        except Exception as e:
            last_error = e
            category = ErrorClassifier.classify(e)

            if circuit_breaker:
                circuit_breaker.record_failure()

            if not policy.should_retry(attempt, e) or not ErrorClassifier.should_retry(e):
                if logger:
                    elapsed = (time.time() - start_time) * 1000
                    logger.error(f"Non-retryable [{category.value}]: {context}: {e}")
                raise

            retry_after = ErrorClassifier.extract_retry_after(e)
            delay = policy.calculate_delay(attempt, retry_after)

            if logger:
                logger.warning(f"Retry {attempt}/{policy.max_attempts} after {delay:.2f}s: {e}")

            time.sleep(delay)

    if last_error:
        raise last_error
    raise RuntimeError("Retry loop exited without result or error")


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


def with_retry(
    policy: RetryPolicy = API_RETRY,
    circuit_breaker: Optional[CircuitBreaker] = None,
    logger: Optional[logging.Logger] = None,
    context: str = "",
):
    """Decorator for automatic retry with backoff.

    Works with both sync and async functions.

    Example:
        >>> @with_retry(policy=API_RETRY, context="API call")
        ... async def call_api():
        ...     return await client.request()
    """

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_with_backoff(
                    lambda: func(*args, **kwargs),
                    policy=policy,
                    circuit_breaker=circuit_breaker,
                    logger=logger or logging.getLogger(func.__module__),
                    context=context or func.__name__,
                )

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_sync_with_backoff(
                    lambda: func(*args, **kwargs),
                    policy=policy,
                    circuit_breaker=circuit_breaker,
                    logger=logger or logging.getLogger(func.__module__),
                    context=context or func.__name__,
                )

            return sync_wrapper

    return decorator


@dataclass
class ErrorAggregator:
    """Collect and report multiple errors.

    Useful for batch operations where you want to continue
    processing even if some items fail.
    """

    _errors: list[tuple[str, Exception, ErrorCategory]] = field(default_factory=list, repr=False)
    _logger: Optional[logging.Logger] = field(default=None, repr=False)

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._errors = []
        self._logger = logger

    @contextmanager
    def collect(self, context: str):
        """Context manager to collect errors."""
        try:
            yield
        except Exception as e:
            category = ErrorClassifier.classify(e)
            self._errors.append((context, e, category))
            if self._logger:
                self._logger.warning(f"[{category.value}] {context}: {e}")

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0

    @property
    def error_count(self) -> int:
        return len(self._errors)

    @property
    def errors_by_category(self) -> dict[ErrorCategory, list[tuple[str, Exception]]]:
        """Group errors by category."""
        result: dict[ErrorCategory, list[tuple[str, Exception]]] = {}
        for ctx, err, cat in self._errors:
            if cat not in result:
                result[cat] = []
            result[cat].append((ctx, err))
        return result

    def to_dict(self) -> dict[str, Any]:
        """Export errors as structured dict for JSON reporting."""
        return {
            "total_errors": len(self._errors),
            "errors": [
                {
                    "context": ctx,
                    "type": type(err).__name__,
                    "message": str(err),
                    "category": cat.value,
                }
                for ctx, err, cat in self._errors
            ],
            "by_category": {cat.value: len(errs) for cat, errs in self.errors_by_category.items()},
        }

    def raise_if_errors(self, message: str = "Multiple errors occurred") -> None:
        """Raise if any errors were collected."""
        if self._errors:
            import json

            raise RuntimeError(f"{message}\n{json.dumps(self.to_dict(), indent=2)}")

    def clear(self) -> None:
        """Clear collected errors."""
        self._errors.clear()


@asynccontextmanager
async def error_boundary(
    context: str,
    logger: logging.Logger,
    reraise: bool = True,
):
    """Async context manager for error boundaries with classification.

    Example:
        >>> async with error_boundary("API call", logger, reraise=False):
        ...     await risky_operation()
    """
    try:
        yield
    except Exception as e:
        category = ErrorClassifier.classify(e)
        logger.error(f"[{category.value}] {context}: {type(e).__name__}: {e}")
        if reraise:
            raise


@contextmanager
def sync_error_boundary(
    context: str,
    logger: logging.Logger,
    reraise: bool = True,
):
    """Sync context manager for error boundaries."""
    try:
        yield
    except Exception as e:
        category = ErrorClassifier.classify(e)
        logger.error(f"[{category.value}] {context}: {type(e).__name__}: {e}")
        if reraise:
            raise


__all__ = [
    # Enums
    "ErrorCategory",
    "CircuitState",
    # Core classes
    "ErrorContext",
    "RetryPolicy",
    "CircuitBreaker",
    "ErrorClassifier",
    "FallbackChain",
    "ErrorAggregator",
    # Pre-configured policies
    "AGGRESSIVE_RETRY",
    "CONSERVATIVE_RETRY",
    "API_RETRY",
    # Functions
    "retry_with_backoff",
    "retry_sync_with_backoff",
    "with_retry",
    # Context managers
    "error_boundary",
    "sync_error_boundary",
    # Exceptions
    "CircuitOpenError",
]
