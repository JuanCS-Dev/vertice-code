"""
Resilience Patterns Module - Fault Tolerance
============================================

Re-exports from core.resilience with TUI-specific additions.

Usage:
    # Preferred: direct from core
    from core.resilience import CircuitBreaker, CircuitState

    # This module (re-exports + TUI additions)
    from vertice_tui.core.resilience_patterns import CircuitBreaker, CircuitBreakerStats

Contains:
- CircuitBreaker: Prevents cascading failures (from core.resilience)
- CircuitBreakerStats: Extended stats for TUI observability
"""

from __future__ import annotations

# Re-export from canonical location
from core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError as CircuitBreakerOpen,  # Alias for backward compat
    CircuitState,
)

# TUI-specific addition
from vertice_tui.core.resilience_patterns.circuit_breaker import (
    CircuitBreakerStats,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitBreakerStats",
    "CircuitState",
]
