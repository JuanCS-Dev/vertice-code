"""
Vertice Core Resilience Module - Unified resilience patterns.

SCALE & SUSTAIN Phase 2.1 - CircuitBreaker Consolidation.

This module re-exports the canonical resilience implementation from
core/resilience/ to provide a consistent import path within vertice_core.

Canonical implementation: core/resilience/
- CircuitBreaker: Failure isolation pattern
- RetryHandler: Exponential backoff with jitter
- RateLimiter: Token bucket rate limiting
- FallbackHandler: Multi-provider fallback orchestration

Usage:
    from vertice_core.resilience import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitOpenError,
        CircuitState,
        RetryConfig,
        RetryHandler,
    )

Author: Vertice Team
Date: 2026-01-02
"""

# Re-export everything from canonical implementation
from core.resilience import (
    # Types and Enums
    ErrorCategory,
    ErrorSeverity,
    CircuitState,
    # Configs
    RetryConfig,
    RateLimitConfig,
    FallbackConfig,
    # Exceptions
    ResilienceError,
    TransientError,
    PermanentError,
    RateLimitError,
    CircuitOpenError,
    # Handlers
    RetryHandler,
    CircuitBreaker,
    RateLimiter,
    TokenBucket,
    FallbackHandler,
    # Mixin
    ResilienceMixin,
    # Web Rate Limiting
    WebRateLimitConfig,
    WebRateLimiter,
    WebRateLimiterRegistry,
    get_fetch_limiter,
    get_search_limiter,
)

# Import CircuitBreakerConfig from types
from core.resilience.types import CircuitBreakerConfig

__all__ = [
    # Types and Enums
    "ErrorCategory",
    "ErrorSeverity",
    "CircuitState",
    # Configs
    "RetryConfig",
    "CircuitBreakerConfig",
    "RateLimitConfig",
    "FallbackConfig",
    # Exceptions
    "ResilienceError",
    "TransientError",
    "PermanentError",
    "RateLimitError",
    "CircuitOpenError",
    # Handlers
    "RetryHandler",
    "CircuitBreaker",
    "RateLimiter",
    "TokenBucket",
    "FallbackHandler",
    # Mixin
    "ResilienceMixin",
    # Web Rate Limiting
    "WebRateLimitConfig",
    "WebRateLimiter",
    "WebRateLimiterRegistry",
    "get_fetch_limiter",
    "get_search_limiter",
]
