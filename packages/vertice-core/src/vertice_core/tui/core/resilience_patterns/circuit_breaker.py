"""
Circuit Breaker Pattern - Re-exports with TUI-specific additions.

Base classes are from vertice_core.resilience. This module adds:
- CircuitBreakerStats: Extended statistics for TUI observability

Usage:
    # Preferred: direct from core
    from vertice_core.resilience import CircuitBreaker, CircuitState

    # TUI-specific stats
    from vertice_core.tui.core.resilience_patterns.circuit_breaker import CircuitBreakerStats

Author: JuanCS Dev
Date: 2025-11-27
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Re-export base classes from vertice_core.resilience
from vertice_core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError as CircuitBreakerOpen,  # Alias for backward compat
    CircuitState,
)


# =============================================================================
# TUI-SPECIFIC ADDITIONS
# =============================================================================


@dataclass
class CircuitBreakerStats:
    """Extended statistics for TUI observability."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: List[Tuple[str, float]] = field(default_factory=list)
    last_failure_time: Optional[float] = None
    last_failure_reason: Optional[str] = None


__all__ = [
    # Re-exports from vertice_core.resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitState",
    # TUI-specific
    "CircuitBreakerStats",
]
