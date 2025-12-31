"""LLM provider integrations - Vertice Multi-Provider Architecture."""

from .nebius import NebiusProvider
from .prometheus_provider import PrometheusProvider, PrometheusConfig
from .maximus_provider import MaximusProvider
from .maximus_config import MaximusConfig, TransportMode, MCPConfig
from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    RetryConfig,
    ConnectionPoolConfig,
)

# Vertice Free Tier Providers
from .gemini import GeminiProvider
from .groq import GroqProvider
from .cerebras import CerebrasProvider
from .openrouter import OpenRouterProvider
from .mistral import MistralProvider

# Enterprise Providers (Your Infrastructure)
from .vertex_ai import VertexAIProvider
from .azure_openai import AzureOpenAIProvider

# Unified Client (NEW - Dec 2025)
# Use vertice_core.clients.VerticeClient instead of vertice_router
# vertice_router is deprecated, kept for backward compatibility

# Legacy router (DEPRECATED - use VerticeClient)
try:
    from .vertice_router import (
        VerticeRouter,
        TaskComplexity,
        SpeedRequirement,
        RoutingDecision,
        get_router,
    )
except ImportError:
    # vertice_router may be removed in future
    VerticeRouter = None
    TaskComplexity = None
    SpeedRequirement = None
    RoutingDecision = None
    get_router = None

__all__ = [
    # Legacy providers
    "NebiusProvider",
    "PrometheusProvider",
    "PrometheusConfig",
    "MaximusProvider",
    "MaximusConfig",
    "TransportMode",
    "MCPConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "RetryConfig",
    "ConnectionPoolConfig",
    # Vertice Providers (Free Tier)
    "GeminiProvider",
    "GroqProvider",
    "CerebrasProvider",
    "OpenRouterProvider",
    "MistralProvider",
    # Enterprise Providers (Your Infrastructure)
    "VertexAIProvider",
    "AzureOpenAIProvider",
    # Unified Router
    "VerticeRouter",
    "TaskComplexity",
    "SpeedRequirement",
    "RoutingDecision",
    "get_router",
]
