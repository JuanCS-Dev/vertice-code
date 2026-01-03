"""Dependency Injection Container following Big 3 patterns (2025-2026).

This module provides a production-grade DI system based on best practices from:
- OpenAI Agents SDK: Context object pattern, registry pattern
- Anthropic Claude SDK: Configuration object pattern
- Google/Python: dependency-injector declarative container

Key Features:
    - Declarative container with typed providers
    - Singleton, Factory, and Transient scopes
    - Async lifecycle management
    - Configuration from environment
    - Override support for testing
    - Thread-safe lazy initialization

References:
    - https://openai.github.io/openai-agents-python/config/
    - https://github.com/anthropics/claude-agent-sdk-python
    - https://python-dependency-injector.ets-labs.org/

Design Principles:
    - Explicit is better than implicit (PEP 20)
    - Composition root pattern
    - Constructor injection preferred
    - No service locator anti-pattern

Example:
    >>> from vertice_cli.core.di import Container, inject
    >>>
    >>> # Configure container at app startup
    >>> Container.configure(
    ...     llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
    ...     enable_tracing=True,
    ... )
    >>>
    >>> # Get dependencies
    >>> client = Container.llm_client()
    >>> router = Container.router()
    >>>
    >>> # Or use injection decorator
    >>> @inject
    >>> async def process(client: LLMClient = Provide[Container.llm_client]):
    ...     return await client.complete(prompt)
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
import threading
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


class Scope(Enum):
    """Dependency lifecycle scopes."""

    SINGLETON = "singleton"  # One instance per container
    FACTORY = "factory"  # New instance each time
    TRANSIENT = "transient"  # New instance, no caching
    SCOPED = "scoped"  # One instance per scope (request, session)


class ProviderState(Enum):
    """Provider initialization state."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    DISPOSED = "disposed"


@dataclass
class ProviderConfig:
    """Configuration for a provider.

    Attributes:
        scope: Lifecycle scope.
        lazy: Initialize on first access (default True).
        dispose: Optional cleanup function.
    """

    scope: Scope = Scope.SINGLETON
    lazy: bool = True
    dispose: Optional[Callable[[Any], None]] = None


class Provider(Generic[T], ABC):
    """Base class for dependency providers.

    Providers are factories that create and manage dependency instances.
    """

    def __init__(
        self,
        factory: Callable[..., T],
        config: Optional[ProviderConfig] = None,
    ):
        self._factory = factory
        self._config = config or ProviderConfig()
        self._instance: Optional[T] = None
        self._state = ProviderState.UNINITIALIZED
        self._lock = threading.RLock()
        self._overridden: Optional[Callable[..., T]] = None

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> T:
        """Get or create instance."""
        ...

    def override(self, factory: Callable[..., T]) -> None:
        """Override the factory for testing."""
        self._overridden = factory
        self._instance = None
        self._state = ProviderState.UNINITIALIZED

    def reset(self) -> None:
        """Reset to original factory."""
        self._overridden = None
        self._instance = None
        self._state = ProviderState.UNINITIALIZED

    def dispose(self) -> None:
        """Dispose of the instance."""
        with self._lock:
            if self._instance is not None and self._config.dispose:
                try:
                    self._config.dispose(self._instance)
                except Exception as e:
                    logger.warning(f"Error disposing provider: {e}")
            self._instance = None
            self._state = ProviderState.DISPOSED

    @property
    def is_initialized(self) -> bool:
        """Check if the provider has been initialized."""
        return self._state == ProviderState.INITIALIZED


class Singleton(Provider[T]):
    """Singleton provider - one instance per container."""

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        if self._instance is not None:
            return self._instance

        with self._lock:
            if self._instance is None:
                self._state = ProviderState.INITIALIZING
                factory = self._overridden or self._factory
                self._instance = factory(*args, **kwargs)
                self._state = ProviderState.INITIALIZED
            return self._instance


class Factory(Provider[T]):
    """Factory provider - new instance each call."""

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        factory = self._overridden or self._factory
        return factory(*args, **kwargs)


class Transient(Provider[T]):
    """Transient provider - new instance, no tracking."""

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        factory = self._overridden or self._factory
        return factory(*args, **kwargs)


class AsyncSingleton(Provider[T]):
    """Async singleton provider for async factories."""

    def __init__(
        self,
        factory: Callable[..., T],
        config: Optional[ProviderConfig] = None,
    ):
        super().__init__(factory, config)
        self._async_lock = asyncio.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        # Sync fallback - just return cached or create sync
        if self._instance is not None:
            return self._instance
        raise RuntimeError("Use async_get() for async singletons")

    async def async_get(self, *args: Any, **kwargs: Any) -> T:
        """Get instance asynchronously."""
        if self._instance is not None:
            return self._instance

        async with self._async_lock:
            if self._instance is None:
                self._state = ProviderState.INITIALIZING
                factory = self._overridden or self._factory
                result = factory(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    self._instance = await result
                else:
                    self._instance = result
                self._state = ProviderState.INITIALIZED
            return self._instance


class Configuration:
    """Configuration provider for environment and settings.

    Following OpenAI's pattern of environment-based configuration
    with programmatic overrides.
    """

    def __init__(self, prefix: str = "VERTICE_"):
        self._prefix = prefix
        self._values: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def __getattr__(self, name: str) -> Any:
        # Check programmatic override first
        if name in self._values:
            return self._values[name]

        # Then check environment
        env_key = f"{self._prefix}{name.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        raise AttributeError(f"Configuration '{name}' not found")

    def get(self, name: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        try:
            return getattr(self, name)
        except AttributeError:
            return default

    def set(self, name: str, value: Any) -> None:
        """Set configuration value programmatically."""
        with self._lock:
            self._values[name] = value

    def from_env(self, mapping: Dict[str, str]) -> None:
        """Load multiple values from environment."""
        for key, env_var in mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._values[key] = self._parse_env_value(value)

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable to appropriate type."""
        # Boolean
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        # String
        return value


# Sentinel for Provide pattern
class _ProvideMarker:
    """Marker for dependency injection."""

    def __init__(self, provider: Provider):
        self.provider = provider

    def __class_getitem__(cls, provider: Provider) -> _ProvideMarker:
        return cls(provider)


Provide = _ProvideMarker


def inject(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for automatic dependency injection.

    Example:
        >>> @inject
        ... def process(
        ...     data: str,
        ...     client: LLMClient = Provide[Container.llm_client]
        ... ):
        ...     return client.complete(data)
    """
    hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get defaults from function
        defaults = func.__defaults__ or ()
        kwdefaults = func.__kwdefaults__ or {}

        # Inject dependencies
        injected = {}
        for name, hint in hints.items():
            if name in kwargs:
                continue
            # Check kwdefaults for Provide markers
            if name in kwdefaults and isinstance(kwdefaults[name], _ProvideMarker):
                injected[name] = kwdefaults[name].provider()

        return func(*args, **{**injected, **kwargs})

    return wrapper


class ContainerMeta(type):
    """Metaclass for declarative container definition."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        providers = {}
        for key, value in namespace.items():
            if isinstance(value, Provider):
                providers[key] = value

        namespace["_providers"] = providers
        return super().__new__(mcs, name, bases, namespace)


class BaseContainer(metaclass=ContainerMeta):
    """Base class for dependency containers.

    Subclass to define your application's dependencies.

    Example:
        >>> class AppContainer(BaseContainer):
        ...     config = Configuration()
        ...     llm_client = Singleton(lambda: LLMClient(api_key=config.api_key))
        ...     router = Singleton(lambda: Router(client=llm_client()))
    """

    _providers: Dict[str, Provider] = {}
    _config: Optional[Configuration] = None

    @classmethod
    def configure(cls, **kwargs: Any) -> None:
        """Configure container with settings."""
        if cls._config is None:
            cls._config = Configuration()
        for key, value in kwargs.items():
            cls._config.set(key, value)

    @classmethod
    def override(cls, provider_name: str, factory: Callable) -> None:
        """Override a provider for testing."""
        if provider_name in cls._providers:
            cls._providers[provider_name].override(factory)
        else:
            raise KeyError(f"Provider '{provider_name}' not found")

    @classmethod
    def reset(cls, provider_name: Optional[str] = None) -> None:
        """Reset provider(s) to original factory."""
        if provider_name:
            if provider_name in cls._providers:
                cls._providers[provider_name].reset()
        else:
            for provider in cls._providers.values():
                provider.reset()

    @classmethod
    def dispose(cls, provider_name: Optional[str] = None) -> None:
        """Dispose of provider(s)."""
        if provider_name:
            if provider_name in cls._providers:
                cls._providers[provider_name].dispose()
        else:
            for provider in cls._providers.values():
                provider.dispose()

    @classmethod
    @contextmanager
    def override_context(cls, **overrides: Callable):
        """Context manager for temporary overrides (testing).

        Example:
            >>> with Container.override_context(llm_client=lambda: MockClient()):
            ...     result = my_function()  # Uses MockClient
        """
        for name, factory in overrides.items():
            cls.override(name, factory)
        try:
            yield
        finally:
            for name in overrides:
                cls.reset(name)


# =============================================================================
# VERTICE CONTAINER - Application-specific container
# =============================================================================


class VerticeContainer(BaseContainer):
    """Main dependency container for Vertice application.

    This container centralizes all dependency configuration following
    the Composition Root pattern.

    Usage:
        >>> # At application startup
        >>> VerticeContainer.configure(
        ...     api_key=os.getenv("ANTHROPIC_API_KEY"),
        ...     model="claude-sonnet-4-5-20250929",
        ... )
        >>>
        >>> # Get dependencies
        >>> client = VerticeContainer.llm_client()
        >>> router = VerticeContainer.router()
    """

    # Configuration
    config = Configuration(prefix="VERTICE_")

    # ==========================================================================
    # Core Infrastructure
    # ==========================================================================

    @classmethod
    def llm_client(cls):
        """Get LLM client singleton."""
        # Lazy import to avoid circular dependencies
        from vertice_cli.core.llm import get_default_client
        return get_default_client()

    @classmethod
    def vertice_client(cls):
        """Get Vertice client singleton."""
        from vertice_core.clients.vertice_client import get_client
        return get_client()

    @classmethod
    def router(cls):
        """Get router singleton."""
        from vertice_cli.core.providers.vertice_router import get_router
        return get_router()

    @classmethod
    def semantic_router(cls):
        """Get semantic router singleton."""
        from vertice_core.agents.router import get_router
        return get_router()

    # ==========================================================================
    # Memory & Context
    # ==========================================================================

    @classmethod
    def memory_manager(cls):
        """Get memory manager singleton."""
        from vertice_cli.core.memory import get_memory_manager
        return get_memory_manager()

    @classmethod
    def context_compactor(cls):
        """Get context compactor singleton."""
        from vertice_cli.core.context_compact import get_context_compactor
        return get_context_compactor()

    @classmethod
    def context_tracker(cls):
        """Get context tracker singleton."""
        from vertice_cli.core.context_tracker import get_default_tracker
        return get_default_tracker()

    # ==========================================================================
    # Managers
    # ==========================================================================

    @classmethod
    def session_manager(cls):
        """Get session manager singleton."""
        from vertice_cli.core.session_manager import get_default_manager
        return get_default_manager()

    @classmethod
    def undo_manager(cls):
        """Get undo manager singleton."""
        from vertice_cli.core.undo_manager import get_default_manager
        return get_default_manager()

    # ==========================================================================
    # Intelligence
    # ==========================================================================

    @classmethod
    def intent_classifier(cls):
        """Get intent classifier singleton."""
        from vertice_cli.core.intent_classifier import get_classifier
        return get_classifier()

    @classmethod
    def suggestion_engine(cls):
        """Get suggestion engine singleton."""
        from vertice_cli.intelligence.engine import get_engine
        return get_engine()

    # ==========================================================================
    # Resilience
    # ==========================================================================

    @classmethod
    def rate_limiter(cls):
        """Get rate limiter singleton."""
        from vertice_cli.core.resilience import get_rate_limiter
        return get_rate_limiter()

    @classmethod
    def error_handler(cls):
        """Get error escalation handler singleton."""
        from vertice_cli.core.errors.escalation import get_default_handler
        return get_default_handler()

    # ==========================================================================
    # Observability
    # ==========================================================================

    @classmethod
    def audit_logger(cls):
        """Get audit logger singleton."""
        from vertice_cli.core.audit_logger import get_default_logger
        return get_default_logger()

    # ==========================================================================
    # Messaging
    # ==========================================================================

    @classmethod
    def event_bus(cls):
        """Get event bus singleton."""
        from vertice_core.messaging.events import get_global_bus
        return get_global_bus()

    @classmethod
    def message_broker(cls):
        """Get message broker singleton."""
        from vertice_core.messaging.memory import get_global_broker
        return get_global_broker()

    # ==========================================================================
    # Agents
    # ==========================================================================

    @classmethod
    def agent_registry(cls):
        """Get agent registry singleton."""
        from vertice_agents.registry import AgentRegistry
        return AgentRegistry.instance()

    @classmethod
    def agency(cls):
        """Get agency singleton."""
        from core.agency import get_agency
        return get_agency()


# Convenience alias
Container = VerticeContainer


# =============================================================================
# TESTING UTILITIES
# =============================================================================


class TestContainer(BaseContainer):
    """Test container with mock defaults.

    Use this for unit tests to avoid hitting real services.

    Example:
        >>> from vertice_cli.core.di import TestContainer
        >>>
        >>> def test_something():
        ...     client = TestContainer.llm_client()  # Returns mock
        ...     assert client.complete("test") == "mock response"
    """

    @classmethod
    def llm_client(cls):
        """Get mock LLM client."""
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.complete.return_value = "mock response"
        return mock

    @classmethod
    def router(cls):
        """Get mock router."""
        from unittest.mock import MagicMock
        return MagicMock()


def with_container(container_class: Type[BaseContainer]):
    """Decorator to run function with specific container.

    Example:
        >>> @with_container(TestContainer)
        ... def test_feature():
        ...     client = Container.llm_client()  # Uses TestContainer
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Temporarily swap Container reference
            original = globals().get("Container")
            globals()["Container"] = container_class
            try:
                return func(*args, **kwargs)
            finally:
                if original:
                    globals()["Container"] = original
        return wrapper
    return decorator


__all__ = [
    # Core types
    "Scope",
    "Provider",
    "ProviderConfig",
    # Providers
    "Singleton",
    "Factory",
    "Transient",
    "AsyncSingleton",
    "Configuration",
    # Container
    "BaseContainer",
    "VerticeContainer",
    "Container",
    "TestContainer",
    # Injection
    "Provide",
    "inject",
    # Testing
    "with_container",
]
