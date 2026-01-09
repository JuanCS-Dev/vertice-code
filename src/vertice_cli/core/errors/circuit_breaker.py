"""
Enhanced Circuit Breaker - Gradual recovery pattern with registry.

Provides EnhancedCircuitBreaker with:
- Named circuit breaker registry
- `call()` method API (vs context manager)
- Gradual recovery with success threshold

For base CircuitBreaker class, use core.resilience:
    from core.resilience import CircuitBreaker

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failing, requests are blocked
- HALF_OPEN: Testing recovery, limited requests allowed

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 3.2
Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional

# Import base types
from vertice_cli.core.errors.types import CircuitState, CircuitOpenError

logger = logging.getLogger(__name__)


class EnhancedCircuitBreaker:
    """
    Circuit breaker with gradual recovery.

    Usage:
        breaker = EnhancedCircuitBreaker(failure_threshold=5)

        async def risky_call():
            return await api.call()

        result = await breaker.call(risky_call)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
        name: str = "default",
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Successes in half-open to close circuit
            name: Identifier for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._success_count_in_half_open = 0
        self._total_calls = 0
        self._total_failures = 0

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    async def call(
        self,
        func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call (sync or async)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
        """
        self._total_calls += 1

        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                logger.info(f"[CircuitBreaker:{self.name}] Entering HALF_OPEN state")
                self._state = CircuitState.HALF_OPEN
                self._success_count_in_half_open = 0
            else:
                raise CircuitOpenError(
                    f"Circuit {self.name} is open. Wait {self._time_until_recovery():.0f}s"
                )

        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed for recovery attempt."""
        if self._last_failure_time is None:
            return True

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    def _time_until_recovery(self) -> float:
        """Get time remaining until recovery attempt."""
        if self._last_failure_time is None:
            return 0

        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count_in_half_open += 1
            logger.debug(
                f"[CircuitBreaker:{self.name}] Success in HALF_OPEN "
                f"({self._success_count_in_half_open}/{self.success_threshold})"
            )

            if self._success_count_in_half_open >= self.success_threshold:
                logger.info(f"[CircuitBreaker:{self.name}] Closing circuit (recovered)")
                self._state = CircuitState.CLOSED
                self._failures = 0
        else:
            self._failures = max(0, self._failures - 1)

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self._failures += 1
        self._total_failures += 1
        self._last_failure_time = time.time()

        logger.warning(
            f"[CircuitBreaker:{self.name}] Failure #{self._failures}: {type(error).__name__}"
        )

        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"[CircuitBreaker:{self.name}] Reopening circuit (failure in HALF_OPEN)")
            self._state = CircuitState.OPEN
            self._success_count_in_half_open = 0

        elif self._failures >= self.failure_threshold:
            logger.warning(f"[CircuitBreaker:{self.name}] Opening circuit (threshold reached)")
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._success_count_in_half_open = 0
        logger.info(f"[CircuitBreaker:{self.name}] Reset to CLOSED")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failures": self._failures,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "failure_rate": (
                self._total_failures / self._total_calls if self._total_calls > 0 else 0
            ),
            "time_until_recovery": (
                self._time_until_recovery() if self._state == CircuitState.OPEN else 0
            ),
        }


# Registry of circuit breakers
_circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}


def get_circuit_breaker(name: str = "default") -> EnhancedCircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = EnhancedCircuitBreaker(name=name)
    return _circuit_breakers[name]


def reset_all_circuits() -> None:
    """Reset all circuit breakers."""
    for breaker in _circuit_breakers.values():
        breaker.reset()
