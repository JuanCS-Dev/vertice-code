"""
Circuit Breaker - Failure isolation pattern for resilient systems.

Implements Microsoft's circuit breaker pattern:
- CLOSED: Normal operation, requests flow through
- OPEN: Failures exceeded threshold, requests blocked
- HALF_OPEN: Testing recovery with probe requests

References:
- Microsoft Circuit Breaker Pattern
- https://github.com/gitcommitshow/resilient-llm
- resilient-llm library
"""

from __future__ import annotations

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable, Optional, Any, Dict
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field

from .types import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitOpenError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CircuitStats:
    """Statistics for circuit breaker state."""

    failures: int = 0
    successes: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changed_at: datetime = field(default_factory=datetime.utcnow)
    total_requests: int = 0
    requests_blocked: int = 0


class CircuitBreaker:
    """Circuit breaker for isolating failing dependencies.

    States:
    - CLOSED: All requests pass through. Failures counted.
    - OPEN: All requests blocked. Returns cached/fallback or raises.
    - HALF_OPEN: Limited requests allowed to test recovery.

    Example:
        circuit = CircuitBreaker(name="openai")

        @circuit.protect
        async def call_openai(prompt: str) -> str:
            return await openai.chat(prompt)

        # Or use directly:
        result = await circuit.execute(call_openai, "Hello")
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit (e.g., provider name)
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._failure_times: deque = deque(maxlen=100)
        self._lock = asyncio.Lock()
        self._half_open_pending = False

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def _count_recent_failures(self) -> int:
        """Count failures within the time window.

        Returns:
            Number of failures in window
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.config.window_size)

        recent = sum(1 for t in self._failure_times if t > window_start)
        return recent

    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state.

        Args:
            new_state: Target state
        """
        if new_state == self._state:
            return

        old_state = self._state
        self._state = new_state
        self._stats.state_changed_at = datetime.utcnow()

        if new_state == CircuitState.CLOSED:
            self._stats.consecutive_failures = 0
            self._failure_times.clear()
        elif new_state == CircuitState.OPEN:
            self._stats.consecutive_successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_pending = False

        logger.info(
            f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
        )

    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset.

        Returns:
            True if should try half-open
        """
        if self._state != CircuitState.OPEN:
            return False

        time_since_open = (
            datetime.utcnow() - self._stats.state_changed_at
        ).total_seconds()

        return time_since_open >= self.config.timeout

    async def _record_success(self) -> None:
        """Record successful request."""
        async with self._lock:
            self._stats.successes += 1
            self._stats.consecutive_successes += 1
            self._stats.consecutive_failures = 0
            self._stats.last_success_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)

    async def _record_failure(self, error: Exception) -> None:
        """Record failed request.

        Args:
            error: The exception that occurred
        """
        async with self._lock:
            now = datetime.utcnow()
            self._stats.failures += 1
            self._stats.consecutive_failures += 1
            self._stats.consecutive_successes = 0
            self._stats.last_failure_time = now
            self._failure_times.append(now)

            if self._state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)

            elif self._state == CircuitState.CLOSED:
                recent_failures = self._count_recent_failures()
                if recent_failures >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def _check_state(self) -> None:
        """Check and update state before request."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if await self._should_attempt_reset():
                    await self._transition_to(CircuitState.HALF_OPEN)

    def get_reset_time(self) -> Optional[datetime]:
        """Get estimated time when circuit will attempt reset.

        Returns:
            Datetime when half-open will be attempted, or None
        """
        if self._state != CircuitState.OPEN:
            return None

        return self._stats.state_changed_at + timedelta(seconds=self.config.timeout)

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from function

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        self._stats.total_requests += 1
        await self._check_state()

        if self._state == CircuitState.OPEN:
            self._stats.requests_blocked += 1
            reset_time = self.get_reset_time()
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN. Reset at {reset_time}",
                reset_time=reset_time,
            )

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_pending:
                self._stats.requests_blocked += 1
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is HALF_OPEN with pending probe",
                    reset_time=self.get_reset_time(),
                )
            self._half_open_pending = True

        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result

        except Exception as e:
            await self._record_failure(e)
            raise

    def protect(
        self,
        func: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> Callable[..., Awaitable[T]]:
        """Decorator to protect function with circuit breaker.

        Example:
            @circuit.protect
            async def risky_operation():
                return await external_api.call()
        """
        from functools import wraps

        def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                return await self.execute(fn, *args, **kwargs)

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failures": self._stats.failures,
            "successes": self._stats.successes,
            "consecutive_failures": self._stats.consecutive_failures,
            "consecutive_successes": self._stats.consecutive_successes,
            "total_requests": self._stats.total_requests,
            "requests_blocked": self._stats.requests_blocked,
            "last_failure": self._stats.last_failure_time,
            "last_success": self._stats.last_success_time,
            "state_changed_at": self._stats.state_changed_at,
            "recent_failures": self._count_recent_failures(),
        }

    async def reset(self) -> None:
        """Manually reset circuit to closed state."""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
            self._stats = CircuitStats()
            self._failure_times.clear()
            logger.info(f"Circuit '{self.name}' manually reset")

    async def force_open(self) -> None:
        """Manually open circuit (for maintenance/testing)."""
        async with self._lock:
            await self._transition_to(CircuitState.OPEN)
            logger.warning(f"Circuit '{self.name}' manually opened")
