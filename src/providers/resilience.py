"""
MAXIMUS Resilience Patterns - Re-export Module.

This module re-exports from core.resilience for backward
compatibility. All implementations are in the canonical location.

Usage:
    from providers.resilience import CircuitBreaker, RetryConfig
    from core.resilience import CircuitBreaker, RetryConfig
"""

from __future__ import annotations

# Re-export everything from the canonical location
from core.resilience import (
    # Base types
    CircuitState,
    CircuitBreakerConfig,
    CircuitOpenError as CircuitBreakerOpen,  # Alias for backward compat
    RetryConfig,
    # Handlers
    CircuitBreaker,
)

# Additional helpers from vertice_cli if available - but don't break if not found
try:
    from vertice_cli.core.providers.resilience import (
        ConnectionPoolConfig,
        call_with_resilience,
        create_http_client,
        with_retry,
    )
except ImportError:
    # Provide minimal stubs if not available
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class ConnectionPoolConfig:
        """HTTPX connection pool configuration."""
        max_connections: int = 100
        max_keepalive: int = 20
        keepalive_expiry: float = 5.0
    
    # Create minimal stubs for required functions
    def with_retry(config=None):
        """Stub retry decorator."""
        def decorator(func):
            return func
        return decorator
    
    def create_http_client(base_url, timeout=30.0, pool_config=None):
        """Stub client creator."""
        raise NotImplementedError("HTTPX client not available")
    
    async def call_with_resilience(func, breaker, retry_config=None):
        """Stub resilience caller."""
        return await func()

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
