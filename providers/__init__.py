"""LLM provider integrations - Vertice Multi-Provider Architecture.

Phase 8 Enhanced (2025 Best Practices):
- Rate limit header parsing (Groq, Cerebras, OpenRouter)
- Token usage tracking with cost calculation
- Monthly budget tracking (Mistral 1B free tier)
- OpenRouter :floor suffix for cost optimization
- Prometheus-compatible metrics export
"""

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

# Phase 8: Enhanced Types & Base Class
from .types import (
    CostTier,
    SpeedTier,
    RateLimitInfo,
    UsageInfo,
    CostInfo,
    ProviderPricing,
    ProviderHealth,
    OpenRouterProviderPrefs,
)
from .base import EnhancedProviderBase, ProviderStats

# Vertice Free Tier Providers (Enhanced)
from .gemini import GeminiProvider
from .groq import GroqProvider
from .cerebras import CerebrasProvider
from .openrouter import OpenRouterProvider
from .mistral import MistralProvider

# Enterprise Providers (Your Infrastructure)
from .vertex_ai import VertexAIProvider
from .azure_openai import AzureOpenAIProvider

# Unified Router
from .vertice_router import (
    VerticeRouter,
    TaskComplexity,
    SpeedRequirement,
    RoutingDecision,
    get_router,
)

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
    # Phase 8: Enhanced Types
    "CostTier",
    "SpeedTier",
    "RateLimitInfo",
    "UsageInfo",
    "CostInfo",
    "ProviderPricing",
    "ProviderHealth",
    "OpenRouterProviderPrefs",
    "EnhancedProviderBase",
    "ProviderStats",
    # Vertice Providers (Free Tier - Enhanced)
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
