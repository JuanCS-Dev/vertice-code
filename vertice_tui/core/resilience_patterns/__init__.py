"""
Resilience Patterns Module - Fault Tolerance
============================================

DEPRECATED: This module is deprecated. Use core.resilience or vertice_core.resilience instead.

Migration:
    # Old (deprecated)
    from vertice_tui.core.resilience_patterns import CircuitBreaker

    # New (canonical)
    from core.resilience import CircuitBreaker
    # or
    from vertice_core.resilience import CircuitBreaker

Contains:
- CircuitBreaker: Prevents cascading failures (re-exported for backward compat)
"""

import warnings

warnings.warn(
    "vertice_tui.core.resilience_patterns is deprecated. "
    "Use 'from core.resilience import CircuitBreaker' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from canonical location for backward compatibility
from core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError as CircuitBreakerOpen,  # Alias for backward compat
    CircuitState,
)

# Stats class from local (canonical doesn't have exact match)
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
