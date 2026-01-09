"""
MAXIMUS Resilience Patterns - Re-export Module.

This module re-exports from vertice_cli.core.providers.resilience for backward
compatibility. All implementations are in the canonical location.

Usage:
    # Preferred
    from vertice_cli.core.providers.resilience import CircuitBreaker, RetryConfig

    # Also works (this module)
    from providers.resilience import CircuitBreaker, RetryConfig

    # Base classes only
    from core.resilience import CircuitBreaker, RetryConfig
"""

from __future__ import annotations

# Re-export everything from the canonical location
from vertice_cli.core.providers.resilience import (
    # Base classes (from core.resilience)
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
    RetryConfig,
    # Maximus-specific
    ConnectionPoolConfig,
    call_with_resilience,
    create_http_client,
    with_retry,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitState",
    "RetryConfig",
    "ConnectionPoolConfig",
    "call_with_resilience",
    "create_http_client",
    "with_retry",
]
