"""
LLM provider integrations - Vertice Multi-Provider Architecture.

PERFORMANCE OPTIMIZATION (Jan 2026):
- Lazy loading of heavy providers (VertexAI, Gemini, etc.)
- Reduces import time from ~2s to ~10ms
- Providers are loaded on first access

Use:
    from vertice_cli.core.providers import VertexAIProvider
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


# Mapping for lazy loading
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Legacy providers
    "NebiusProvider": (".nebius", "NebiusProvider"),
    "PrometheusProvider": (".prometheus_provider", "PrometheusProvider"),
    "PrometheusConfig": (".prometheus_provider", "PrometheusConfig"),
    "MaximusProvider": (".maximus_provider", "MaximusProvider"),
    "MaximusConfig": (".maximus_config", "MaximusConfig"),
    "TransportMode": (".maximus_config", "TransportMode"),
    "MCPConfig": (".maximus_config", "MCPConfig"),
    # Resilience
    "CircuitBreaker": (".resilience", "CircuitBreaker"),
    "CircuitBreakerConfig": (".resilience", "CircuitBreakerConfig"),
    "RetryConfig": (".resilience", "RetryConfig"),
    "ConnectionPoolConfig": (".resilience", "ConnectionPoolConfig"),
    # Free Tier Providers (relatively lightweight)
    "GeminiProvider": (".gemini", "GeminiProvider"),
    "GroqProvider": (".groq", "GroqProvider"),
    "CerebrasProvider": (".cerebras", "CerebrasProvider"),
    "OpenRouterProvider": (".openrouter", "OpenRouterProvider"),
    "MistralProvider": (".mistral", "MistralProvider"),
    # Enterprise Providers (HEAVY - google.cloud.aiplatform)
    "VertexAIProvider": (".vertex_ai", "VertexAIProvider"),
    "AzureOpenAIProvider": (".azure_openai", "AzureOpenAIProvider"),
    # Unified Router
    "VerticeRouter": (".vertice_router", "VerticeRouter"),
    "TaskComplexity": (".vertice_router", "TaskComplexity"),
    "SpeedRequirement": (".vertice_router", "SpeedRequirement"),
    "RoutingDecision": (".vertice_router", "RoutingDecision"),
    "get_router": (".vertice_router", "get_router"),
}

_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import providers on first access."""
    if name in _cache:
        return _cache[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        try:
            module = importlib.import_module(module_path, __name__)
            value = getattr(module, attr_name)
            _cache[name] = value
            return value
        except ImportError:
            # Some providers may not be installed
            if name in (
                "VerticeRouter",
                "TaskComplexity",
                "SpeedRequirement",
                "RoutingDecision",
                "get_router",
            ):
                return None
            raise

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return available names."""
    return list(_LAZY_IMPORTS.keys())


__all__ = list(_LAZY_IMPORTS.keys())
