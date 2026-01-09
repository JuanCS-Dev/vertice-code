"""
Core Resilience Module - Basic implementations to break circular imports.

This module provides basic implementations of CircuitBreaker and related classes
to resolve circular import issues between vertice_core and vertice_cli.

For full-featured implementations, use vertice_cli.core.providers.resilience.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    name: str = "default"


class CircuitBreaker:
    """Basic circuit breaker implementation."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0

    def record_success(self) -> None:
        """Record a successful call."""
        self.failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if call can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) >= self.config.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        if self.half_open_calls < self.config.half_open_max_calls:
            self.half_open_calls += 1
            return True

        return False

    def __call__(self, func):
        """Decorator to apply circuit breaker to function."""

        def wrapper(*args, **kwargs):
            if not self.can_attempt():
                raise CircuitOpenError("Circuit breaker is open")
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise e

        return wrapper


class RateLimiter:
    """Basic rate limiter implementation."""

    def __init__(
        self, max_requests: int = 100, window_seconds: float = 60.0, name: str = "default"
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self.requests = []
        self._lock = None  # Would need threading.Lock in real implementation

    def can_make_request(self) -> bool:
        """Check if request can be made within rate limits."""
        now = time.time()
        # Remove old requests outside the window
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.window_seconds
        ]

        return len(self.requests) < self.max_requests

    def record_request(self) -> None:
        """Record a request."""
        if self.can_make_request():
            self.requests.append(time.time())

    def get_remaining_requests(self) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(self.requests))

    def get_reset_time(self) -> float:
        """Get time until rate limit resets."""
        if not self.requests:
            return 0.0
        now = time.time()
        oldest_request = min(self.requests)
        return max(0.0, self.window_seconds - (now - oldest_request))
