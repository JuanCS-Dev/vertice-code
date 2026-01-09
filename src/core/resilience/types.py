"""
Resilience Types - Error categories, configurations, and exceptions.

Based on 2025 best practices:
- Explicit failure classification (transient vs permanent)
- Configurable retry strategies
- Circuit breaker states
- Token bucket rate limiting configs

References:
- https://sparkco.ai/blog/mastering-retry-logic-agents
- https://github.com/gitcommitshow/resilient-llm
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime


class ErrorCategory(Enum):
    """Classification of errors for retry decisions."""

    TRANSIENT = "transient"  # Network timeout, rate limit, 5xx - retry
    PERMANENT = "permanent"  # Auth error, invalid request - don't retry
    RATE_LIMIT = "rate_limit"  # Specific rate limit - backoff required
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker open - use fallback
    UNKNOWN = "unknown"  # Unclassified - conservative retry


class ErrorSeverity(Enum):
    """Severity level for monitoring and alerting."""

    LOW = "low"  # Informational, expected failures
    MEDIUM = "medium"  # Degraded service, needs attention
    HIGH = "high"  # Service impacted, investigate soon
    CRITICAL = "critical"  # Service down, immediate action


class CircuitState(Enum):
    """Circuit breaker states following Microsoft pattern."""

    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Failures exceeded threshold, block requests
    HALF_OPEN = "half_open"  # Testing recovery with probe requests


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Multiplier for exponential backoff (default 2)
        jitter: Random jitter factor (0.0-1.0) to prevent thundering herd
        retry_on: List of exception types to retry on
        respect_retry_after: Honor Retry-After headers from APIs
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    retry_on: List[type] = field(default_factory=lambda: [Exception])
    respect_retry_after: bool = True

    def calculate_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculate delay for given attempt with jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Optional Retry-After header value in seconds

        Returns:
            Delay in seconds with jitter applied
        """
        import random

        if retry_after is not None and self.respect_retry_after:
            return min(retry_after, self.max_delay)

        delay = self.base_delay * (self.exponential_base**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.1, delay)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern.

    Attributes:
        failure_threshold: Failures before opening circuit
        success_threshold: Successes in half-open before closing
        timeout: Seconds before attempting recovery (half-open)
        window_size: Time window for counting failures (seconds)
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0
    window_size: float = 60.0


@dataclass
class RateLimitConfig:
    """Configuration for token bucket rate limiting.

    Attributes:
        requests_per_minute: Max requests per minute
        tokens_per_minute: Max tokens per minute (for LLM APIs)
        burst_size: Max burst of requests allowed
        refill_rate: Tokens added per second
    """

    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    burst_size: int = 10
    refill_rate: Optional[float] = None

    def __post_init__(self) -> None:
        """Calculate refill rate if not provided."""
        if self.refill_rate is None:
            self.refill_rate = self.requests_per_minute / 60.0


@dataclass
class FallbackConfig:
    """Configuration for fallback provider chain.

    Attributes:
        providers: Ordered list of provider names to try
        timeout_per_provider: Max time per provider attempt
        parallel_fallback: Try providers in parallel (first success wins)
    """

    providers: List[str] = field(default_factory=list)
    timeout_per_provider: float = 30.0
    parallel_fallback: bool = False


@dataclass
class ErrorContext:
    """Context for error handling decisions.

    Attributes:
        error: The exception that occurred
        category: Classified error category
        severity: Error severity level
        attempt: Current retry attempt number
        provider: Provider that raised the error
        operation: Operation being performed
        timestamp: When the error occurred
        retry_after: Suggested retry delay from API
        metadata: Additional context data
    """

    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    attempt: int = 0
    provider: Optional[str] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Custom Exceptions


class ResilienceError(Exception):
    """Base exception for resilience module."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize resilience error.

        Args:
            message: Error description
            category: Error classification
            severity: Error severity
            context: Additional error context
        """
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context


class TransientError(ResilienceError):
    """Transient error that should be retried."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize transient error."""
        super().__init__(
            message, category=ErrorCategory.TRANSIENT, severity=ErrorSeverity.LOW, **kwargs
        )


class PermanentError(ResilienceError):
    """Permanent error that should not be retried."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize permanent error."""
        super().__init__(
            message, category=ErrorCategory.PERMANENT, severity=ErrorSeverity.HIGH, **kwargs
        )


class RateLimitError(ResilienceError):
    """Rate limit exceeded error."""

    def __init__(
        self, message: str, retry_after: Optional[float] = None, **kwargs: Any
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error description
            retry_after: Suggested wait time in seconds
        """
        super().__init__(
            message, category=ErrorCategory.RATE_LIMIT, severity=ErrorSeverity.MEDIUM, **kwargs
        )
        self.retry_after = retry_after


class CircuitOpenError(ResilienceError):
    """Circuit breaker is open, requests blocked."""

    def __init__(self, message: str, reset_time: Optional[datetime] = None, **kwargs: Any) -> None:
        """Initialize circuit open error.

        Args:
            message: Error description
            reset_time: When circuit will attempt half-open
        """
        super().__init__(
            message, category=ErrorCategory.CIRCUIT_OPEN, severity=ErrorSeverity.HIGH, **kwargs
        )
        self.reset_time = reset_time


# Type aliases for callbacks
RetryCallback = Callable[[ErrorContext], Awaitable[None]]
FallbackCallback = Callable[[str, Exception], Awaitable[Any]]
