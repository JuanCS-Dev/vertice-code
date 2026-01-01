"""
Provider Registry - Dependency Injection for LLM Providers.

Solves circular import issue: vertice_core should NOT import from vertice_cli.
Instead, vertice_cli registers providers here, and vertice_core uses them.

Pattern: Dependency Injection (Python Best Practices 2026)
"""

from __future__ import annotations

import logging
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    runtime_checkable,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class ProviderProtocol(Protocol):
    """
    Protocol that all LLM providers must implement.

    Using Protocol for structural subtyping - providers don't need to
    inherit from a base class, just implement these methods.
    """

    def is_available(self) -> bool:
        """Check if provider is available (has API key, etc)."""
        ...

    async def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Generate completion from messages."""
        ...

    async def stream_generate(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream generation from messages."""
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        ...


# Type for provider factory functions
ProviderFactory = Callable[[], ProviderProtocol]


class ProviderRegistry:
    """
    Central registry for LLM providers.

    Usage:
        # In vertice_cli (registers providers):
        from vertice_core.providers import registry
        from vertice_cli.core.providers.groq import GroqProvider

        registry.register("groq", GroqProvider)

        # In vertice_core (uses providers):
        provider = registry.get("groq")
        if provider:
            result = await provider.generate(messages)
    """

    def __init__(self) -> None:
        self._factories: Dict[str, ProviderFactory] = {}
        self._instances: Dict[str, ProviderProtocol] = {}
        self._initialized = False

    def register(
        self,
        name: str,
        factory: ProviderFactory,
        *,
        override: bool = False,
    ) -> None:
        """
        Register a provider factory.

        Args:
            name: Provider name (e.g., "groq", "vertex-ai")
            factory: Callable that creates the provider instance
            override: If True, allow overriding existing registration
        """
        if name in self._factories and not override:
            logger.debug(f"Provider {name} already registered, skipping")
            return

        self._factories[name] = factory
        logger.debug(f"Registered provider: {name}")

    def register_instance(
        self,
        name: str,
        instance: ProviderProtocol,
        *,
        override: bool = False,
    ) -> None:
        """
        Register a pre-created provider instance.

        Useful for testing or when provider needs special initialization.
        """
        if name in self._instances and not override:
            logger.debug(f"Provider instance {name} already exists, skipping")
            return

        self._instances[name] = instance
        logger.debug(f"Registered provider instance: {name}")

    def get(self, name: str) -> Optional[ProviderProtocol]:
        """
        Get a provider by name.

        Creates instance on first access (lazy loading).
        Returns None if provider not registered or unavailable.
        """
        # Check for pre-registered instance
        if name in self._instances:
            return self._instances[name]

        # Check for factory
        if name not in self._factories:
            logger.debug(f"Provider not registered: {name}")
            return None

        # Create instance (lazy loading)
        try:
            instance = self._factories[name]()
            if instance.is_available():
                self._instances[name] = instance
                return instance
            else:
                logger.debug(f"Provider {name} not available")
                return None
        except Exception as e:
            logger.warning(f"Failed to create provider {name}: {e}")
            return None

    def get_available(self) -> List[str]:
        """Get list of available provider names."""
        available = []
        for name in self._factories:
            provider = self.get(name)
            if provider:
                available.append(name)
        return available

    def is_registered(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._factories or name in self._instances

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._factories.clear()
        self._instances.clear()
        self._initialized = False

    def __contains__(self, name: str) -> bool:
        return self.is_registered(name)

    def __repr__(self) -> str:
        registered = list(self._factories.keys())
        instantiated = list(self._instances.keys())
        return (
            f"ProviderRegistry(registered={registered}, "
            f"instantiated={instantiated})"
        )


# Global singleton registry
registry = ProviderRegistry()


def register_provider(
    name: str,
    factory: ProviderFactory,
    *,
    override: bool = False,
) -> None:
    """Convenience function to register a provider."""
    registry.register(name, factory, override=override)


def get_provider(name: str) -> Optional[ProviderProtocol]:
    """Convenience function to get a provider."""
    return registry.get(name)


def get_available_providers() -> List[str]:
    """Convenience function to get available providers."""
    return registry.get_available()
