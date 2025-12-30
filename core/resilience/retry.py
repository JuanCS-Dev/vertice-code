"""
Retry Handler - Exponential backoff with jitter for transient failures.

Implements best practices from 2025:
- Exponential backoff prevents overwhelming recovering services
- Jitter prevents thundering herd problem
- Explicit failure classification for smart retry decisions
- Respects Retry-After headers from APIs

References:
- https://markaicode.com/llm-api-retry-logic-implementation/
- OpenAI Cookbook: How to handle rate limits
- Tenacity library patterns
"""

from __future__ import annotations

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable, Optional, Any
from functools import wraps

from .types import (
    RetryConfig,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    TransientError,
    PermanentError,
    RateLimitError,
    RetryCallback,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter.

    Features:
    - Configurable retry strategies
    - Exponential backoff with jitter
    - Error classification (transient vs permanent)
    - Retry-After header support
    - Callbacks for monitoring

    Example:
        handler = RetryHandler(config=RetryConfig(max_retries=3))

        @handler.retry
        async def call_llm(prompt: str) -> str:
            return await llm.generate(prompt)

        # Or use directly:
        result = await handler.execute(call_llm, "Hello")
    """

    # Error patterns for classification
    TRANSIENT_PATTERNS = [
        "timeout",
        "connection",
        "temporary",
        "overloaded",
        "503",
        "502",
        "504",
        "rate limit",
        "too many requests",
        "429",
        "server error",
        "internal error",
    ]

    PERMANENT_PATTERNS = [
        "invalid",
        "unauthorized",
        "forbidden",
        "not found",
        "authentication",
        "permission",
        "400",
        "401",
        "403",
        "404",
        "malformed",
    ]

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        on_retry: Optional[RetryCallback] = None,
    ) -> None:
        """Initialize retry handler.

        Args:
            config: Retry configuration
            on_retry: Callback invoked on each retry attempt
        """
        self.config = config or RetryConfig()
        self.on_retry = on_retry
        self._stats = {"attempts": 0, "successes": 0, "failures": 0, "retries": 0}

    def classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error for retry decision.

        Args:
            error: The exception to classify

        Returns:
            Error category (transient, permanent, rate_limit, etc.)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Check for rate limit specifically
        if any(p in error_str for p in ["rate limit", "too many requests", "429"]):
            return ErrorCategory.RATE_LIMIT

        # Check for transient errors
        if any(p in error_str or p in error_type for p in self.TRANSIENT_PATTERNS):
            return ErrorCategory.TRANSIENT

        # Check for permanent errors
        if any(p in error_str or p in error_type for p in self.PERMANENT_PATTERNS):
            return ErrorCategory.PERMANENT

        # Check exception types
        if isinstance(error, (TimeoutError, ConnectionError, asyncio.TimeoutError)):
            return ErrorCategory.TRANSIENT

        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorCategory.PERMANENT

        if isinstance(error, TransientError):
            return ErrorCategory.TRANSIENT

        if isinstance(error, PermanentError):
            return ErrorCategory.PERMANENT

        if isinstance(error, RateLimitError):
            return ErrorCategory.RATE_LIMIT

        return ErrorCategory.UNKNOWN

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should be retried.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_retries:
            return False

        category = self.classify_error(error)

        # Never retry permanent errors
        if category == ErrorCategory.PERMANENT:
            return False

        # Always retry rate limits (with backoff)
        if category == ErrorCategory.RATE_LIMIT:
            return True

        # Retry transient errors
        if category == ErrorCategory.TRANSIENT:
            return True

        # For unknown, retry conservatively
        if category == ErrorCategory.UNKNOWN:
            return attempt < min(2, self.config.max_retries)

        return False

    def extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract Retry-After value from error if available.

        Args:
            error: The exception to check

        Returns:
            Retry delay in seconds, or None
        """
        if isinstance(error, RateLimitError) and error.retry_after:
            return error.retry_after

        # Check for retry_after attribute
        if hasattr(error, "retry_after"):
            return getattr(error, "retry_after")

        # Try to parse from error message
        error_str = str(error).lower()
        if "retry after" in error_str or "retry-after" in error_str:
            import re

            match = re.search(r"retry[- ]after[:\s]+(\d+)", error_str)
            if match:
                return float(match.group(1))

        return None

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful function execution

        Raises:
            Last exception if all retries exhausted
        """
        last_error: Optional[Exception] = None
        operation = getattr(func, "__name__", "unknown")

        for attempt in range(self.config.max_retries + 1):
            self._stats["attempts"] += 1

            try:
                result = await func(*args, **kwargs)
                self._stats["successes"] += 1
                return result

            except Exception as e:
                last_error = e
                category = self.classify_error(e)
                retry_after = self.extract_retry_after(e)

                context = ErrorContext(
                    error=e,
                    category=category,
                    severity=self._get_severity(category, attempt),
                    attempt=attempt,
                    operation=operation,
                    retry_after=retry_after,
                )

                if not self.should_retry(e, attempt):
                    self._stats["failures"] += 1
                    logger.warning(
                        f"Permanent failure in {operation}: {e} "
                        f"(category={category.value}, attempt={attempt})"
                    )
                    raise

                self._stats["retries"] += 1
                delay = self.config.calculate_delay(attempt, retry_after)

                logger.info(
                    f"Retrying {operation} after {delay:.2f}s "
                    f"(attempt={attempt + 1}/{self.config.max_retries}, "
                    f"category={category.value})"
                )

                if self.on_retry:
                    await self.on_retry(context)

                await asyncio.sleep(delay)

        self._stats["failures"] += 1
        raise last_error or RuntimeError("Retry exhausted with no error")

    def retry(
        self,
        func: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> Callable[..., Awaitable[T]]:
        """Decorator for retry logic.

        Example:
            @retry_handler.retry
            async def call_api():
                return await api.request()
        """

        def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                return await self.execute(fn, *args, **kwargs)

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def _get_severity(self, category: ErrorCategory, attempt: int) -> ErrorSeverity:
        """Determine error severity based on category and attempts.

        Args:
            category: Error classification
            attempt: Current attempt number

        Returns:
            Appropriate severity level
        """
        if category == ErrorCategory.PERMANENT:
            return ErrorSeverity.HIGH

        if category == ErrorCategory.RATE_LIMIT:
            return ErrorSeverity.MEDIUM if attempt < 2 else ErrorSeverity.HIGH

        if attempt >= self.config.max_retries - 1:
            return ErrorSeverity.HIGH

        return ErrorSeverity.LOW

    def get_stats(self) -> dict:
        """Get retry statistics.

        Returns:
            Dictionary with attempt counts
        """
        total = self._stats["attempts"]
        return {
            **self._stats,
            "success_rate": self._stats["successes"] / total if total > 0 else 0.0,
            "retry_rate": self._stats["retries"] / total if total > 0 else 0.0,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {"attempts": 0, "successes": 0, "failures": 0, "retries": 0}
