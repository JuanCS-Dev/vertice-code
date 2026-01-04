"""
Circuit Breaker Types for vertice_core.

Re-exports from core.resilience with domain-specific additions:
- CircuitBreakerStats: Extended statistics
- SimpleCircuitBreaker: Dataclass-based simple breaker for backward compat

Usage:
    # Preferred: direct from core
    from core.resilience import CircuitBreaker, CircuitState

    # Domain types (this module)
    from vertice_core.types.circuit import CircuitBreakerStats, SimpleCircuitBreaker

Author: JuanCS Dev
Date: 2025-11-26
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Re-export base types from core.resilience
from core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
)


# =============================================================================
# VERTICE_CORE SPECIFIC TYPES
# =============================================================================


@dataclass
class CircuitBreakerStats:
    """Statistics for observability."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: List[Tuple[str, float]] = field(default_factory=list)
    last_failure_time: Optional[float] = None
    last_failure_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "state_changes": self.state_changes,
            "last_failure_time": self.last_failure_time,
            "last_failure_reason": self.last_failure_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerStats":
        """Deserialize from dictionary."""
        return cls(
            total_calls=data.get("total_calls", 0),
            successful_calls=data.get("successful_calls", 0),
            failed_calls=data.get("failed_calls", 0),
            rejected_calls=data.get("rejected_calls", 0),
            state_changes=data.get("state_changes", []),
            last_failure_time=data.get("last_failure_time"),
            last_failure_reason=data.get("last_failure_reason"),
        )

    def __repr__(self) -> str:
        """Concise representation."""
        success_rate = self.successful_calls / self.total_calls * 100 if self.total_calls > 0 else 0
        return f"CircuitBreakerStats(calls={self.total_calls}, success={success_rate:.1f}%)"


@dataclass
class SimpleCircuitBreaker:
    """
    Simple dataclass-based circuit breaker for lightweight use cases.

    For full-featured circuit breaker, use CircuitBreaker from core.resilience.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3

    failures: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0

    def record_success(self) -> None:
        self.failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_attempt(self) -> Tuple[bool, str]:
        if self.state == CircuitState.CLOSED:
            return True, "Circuit closed"

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) >= self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True, "Circuit half-open"
            return False, "Circuit open"

        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            return True, f"Half-open test {self.half_open_calls}"

        return False, "Half-open limit"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "half_open_max_calls": self.half_open_max_calls,
            "failures": self.failures,
            "state": self.state.value,
            "last_failure_time": self.last_failure_time,
            "half_open_calls": self.half_open_calls,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleCircuitBreaker":
        """Deserialize from dictionary."""
        state = data.get("state", "closed")
        return cls(
            failure_threshold=data.get("failure_threshold", 5),
            recovery_timeout=data.get("recovery_timeout", 60.0),
            half_open_max_calls=data.get("half_open_max_calls", 3),
            failures=data.get("failures", 0),
            state=CircuitState(state) if isinstance(state, str) else state,
            last_failure_time=data.get("last_failure_time"),
            half_open_calls=data.get("half_open_calls", 0),
        )

    def __repr__(self) -> str:
        """Concise representation."""
        return f"SimpleCircuitBreaker(state={self.state.value}, failures={self.failures}/{self.failure_threshold})"


__all__ = [
    # Re-exports from core.resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "CircuitState",
    # Domain-specific
    "CircuitBreakerStats",
    "SimpleCircuitBreaker",
]
