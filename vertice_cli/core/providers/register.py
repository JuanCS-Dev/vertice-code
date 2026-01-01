"""
Provider Registration - Dependency Injection Setup.

This module registers all providers with the vertice_core registry.
Must be called at CLI startup before using any providers.

Pattern: Dependency Injection (avoids circular imports)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_registered = False


def register_all_providers() -> None:
    """
    Register all providers with the vertice_core registry.

    This function should be called once at CLI startup.
    Safe to call multiple times (idempotent).
    """
    global _registered
    if _registered:
        return

    from vertice_core.providers import registry

    # Register each provider with a factory function
    # Using lambdas for lazy loading - providers are only
    # instantiated when first accessed

    try:
        from .groq import GroqProvider
        registry.register("groq", lambda: GroqProvider())
    except ImportError as e:
        logger.debug(f"Groq provider not available: {e}")

    try:
        from .cerebras import CerebrasProvider
        registry.register("cerebras", lambda: CerebrasProvider())
    except ImportError as e:
        logger.debug(f"Cerebras provider not available: {e}")

    try:
        from .mistral import MistralProvider
        registry.register("mistral", lambda: MistralProvider())
    except ImportError as e:
        logger.debug(f"Mistral provider not available: {e}")

    try:
        from .vertex_ai import VertexAIProvider
        registry.register("vertex-ai", lambda: VertexAIProvider())
    except ImportError as e:
        logger.debug(f"Vertex AI provider not available: {e}")

    try:
        from .azure_openai import AzureOpenAIProvider
        registry.register("azure", lambda: AzureOpenAIProvider())
        registry.register("azure-openai", lambda: AzureOpenAIProvider())
    except ImportError as e:
        logger.debug(f"Azure OpenAI provider not available: {e}")

    try:
        from .openrouter import OpenRouterProvider
        registry.register("openrouter", lambda: OpenRouterProvider())
    except ImportError as e:
        logger.debug(f"OpenRouter provider not available: {e}")

    try:
        from .gemini import GeminiProvider
        registry.register("gemini", lambda: GeminiProvider())
    except ImportError as e:
        logger.debug(f"Gemini provider not available: {e}")

    _registered = True
    logger.debug(f"Registered providers: {registry.get_available()}")


def ensure_providers_registered() -> None:
    """
    Ensure providers are registered (alias for register_all_providers).

    Can be called from anywhere that needs providers.
    """
    register_all_providers()
