"""
Resilience Module - Production-grade fault tolerance for AI agents.

Provides:
- RetryHandler: Exponential backoff with jitter
- CircuitBreaker: Failure isolation pattern
- RateLimiter: Token bucket rate limiting
- FallbackHandler: Multi-provider fallback orchestration
- ResilienceMixin: Agent integration mixin

References:
- AWS Architecture: Build Resilient Generative AI Agents
- Microsoft Circuit Breaker Pattern
- resilient-llm library patterns
- Tenacity retry library
"""

from __future__ import annotations

from .types import (
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    CircuitState,
    CircuitBreakerConfig,
    RateLimitConfig,
    FallbackConfig,
    ResilienceError,
    TransientError,
    PermanentError,
    RateLimitError,
    CircuitOpenError,
)

# Backward compatibility aliases
CircuitBreakerOpen = CircuitOpenError  # Alias for backward compat
CircuitBreakerStats = None  # Placeholder - use from vertice_tui.core.resilience_patterns
from .retry import RetryHandler
from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter, TokenBucket
from .fallback import FallbackHandler
from .mixin import ResilienceMixin
from .web_rate_limiter import (
    WebRateLimitConfig,
    WebRateLimiter,
    WebRateLimiterRegistry,
    get_fetch_limiter,
    get_search_limiter,
)

__all__ = [
    # Types
    "ErrorCategory",
    "ErrorSeverity",
    "RetryConfig",
    "CircuitState",
    "CircuitBreakerConfig",
    "RateLimitConfig",
    "FallbackConfig",
    "ResilienceError",
    "TransientError",
    "PermanentError",
    "RateLimitError",
    "CircuitOpenError",
    # Backward compat aliases
    "CircuitBreakerOpen",  # Alias for CircuitOpenError
    "CircuitBreakerStats",  # Placeholder - use from TUI/vertice_core
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
