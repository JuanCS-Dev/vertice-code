"""
VerticeClient - Unified LLM Client with FREE FIRST priority.

Provides a single facade for all LLM providers with automatic
fallback and circuit breaking. Inspired by OpenRouter :floor pattern.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, zero TODOs.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)

# Priority order: Vertex AI FIRST (Gemini 2.5 Pro - user's available model)
DEFAULT_PRIORITY: List[str] = [
    "vertex-ai",  # PRIMARY - Gemini 2.5 Pro (user's only available model)
    "groq",  # Fast free tier fallback
    "cerebras",
    "mistral",
    "azure",
]
DEFAULT_MAX_TOKENS: int = 8192
DEFAULT_TEMPERATURE: float = 1.0
CIRCUIT_BREAKER_THRESHOLD: int = 5

# Environment variable mapping
ENV_MAP: Dict[str, str] = {
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "vertex-ai": "GOOGLE_CLOUD_PROJECT",  # Gemini via Vertex AI
    "anthropic-vertex": "GOOGLE_CLOUD_PROJECT",  # Claude via Vertex AI
    "azure": "AZURE_OPENAI_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


class VerticeClientError(Exception):
    """Base exception for VerticeClient errors."""


class AllProvidersExhaustedError(VerticeClientError):
    """All providers failed or exhausted their quotas."""

    def __init__(
        self,
        message: str,
        tried: Optional[List[str]] = None,
        errors: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.tried_providers = tried or []
        self.errors = errors or {}


class RateLimitError(VerticeClientError):
    """Provider rate limit exceeded (HTTP 429)."""

    def __init__(self, provider: str, retry_after: Optional[int] = None) -> None:
        msg = f"Rate limit on {provider}" + (f", retry {retry_after}s" if retry_after else "")
        super().__init__(msg)
        self.provider = provider
        self.retry_after = retry_after


class ProviderProtocol(Protocol):
    """Protocol for LLM providers."""

    def is_available(self) -> bool:
        ...

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        **kwargs: Any,
    ) -> str:
        ...


@dataclass
class VerticeClientConfig:
    """Configuration for VerticeClient."""

    priority: List[str] = field(default_factory=lambda: DEFAULT_PRIORITY.copy())
    max_retries: int = 2
    circuit_breaker_threshold: int = CIRCUIT_BREAKER_THRESHOLD
    default_max_tokens: int = DEFAULT_MAX_TOKENS
    default_temperature: float = DEFAULT_TEMPERATURE


class VerticeClient:
    """
    Unified LLM client with FREE FIRST priority.

    Provides automatic provider selection and failover based on
    availability and rate limits.

    Example:
        >>> client = VerticeClient()
        >>> async for chunk in client.stream_chat(messages):
        ...     print(chunk, end="")
    """

    def __init__(
        self,
        config: Optional[VerticeClientConfig] = None,
        providers: Optional[Dict[str, ProviderProtocol]] = None,
    ) -> None:
        """Initialize with optional config and pre-built providers."""
        self.config = config or VerticeClientConfig()
        self._providers: Dict[str, Optional[ProviderProtocol]] = providers or {}
        self._failures: Dict[str, int] = {}
        self._errors: Dict[str, str] = {}
        self._current_provider: Optional[str] = None

    @property
    def current_provider(self) -> Optional[str]:
        """Currently active provider name."""
        return self._current_provider

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat with automatic fallback through providers."""
        max_tokens = max_tokens or self.config.default_max_tokens
        temperature = temperature or self.config.default_temperature
        full_messages = self._build_messages(messages, system_prompt)
        tried: List[str] = []

        for name in self.config.priority:
            if not self._can_use(name):
                continue
            provider = await self._get_provider(name)
            if not provider:
                continue

            tried.append(name)
            try:
                self._current_provider = name

                # Validate tools support
                tools = kwargs.get("tools")
                if tools and hasattr(provider, "stream_chat"):
                    # Check if provider signature accepts tools
                    import inspect

                    sig = inspect.signature(provider.stream_chat)
                    if "tools" not in sig.parameters:
                        logger.warning(
                            f"Provider {name} ignoring {len(tools)} tools (not supported)"
                        )

                async for chunk in provider.stream_chat(
                    full_messages, max_tokens=max_tokens, temperature=temperature, **kwargs
                ):
                    yield chunk
                self._record_success(name)
                return
            except Exception as e:
                self._record_failure(name, e)
                if self._is_rate_limit(e):
                    logger.info(f"Rate limit on {name}, trying next")
                else:
                    logger.warning(f"Provider {name} failed: {e}")

        raise AllProvidersExhaustedError(
            f"All providers exhausted: {tried}", tried=tried, errors=self._errors.copy()
        )

    async def stream_open_responses(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream using Open Responses SSE protocol.

        Wraps stream_chat() output with semantic SSE events that can be
        parsed by OpenResponsesParser in the TUI.

        Args:
            messages: Chat messages
            system_prompt: Optional system prompt
            **kwargs: Additional kwargs passed to stream_chat

        Yields:
            SSE formatted events following Open Responses spec
        """
        from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

        # Get current model name
        model_name = "gemini-3-pro-preview"
        if self._current_provider:
            model_name = f"{self._current_provider}-model"

        builder = OpenResponsesStreamBuilder(model=model_name)

        # Emit start events
        builder.start()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Add message item
        msg_item = builder.add_message()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Stream content and emit text deltas
        # CRITICAL FIX: Extract tools from kwargs and pass explicitly
        tools = kwargs.pop("tools", None)
        try:
            async for chunk in self.stream_chat(
                messages, system_prompt=system_prompt, tools=tools, **kwargs
            ):
                builder.text_delta(msg_item, chunk)
                yield builder.get_last_event_sse()
                builder.clear_events()

            # Complete successfully
            builder.complete()
            for event in builder.get_events():
                yield event.to_sse()
            yield builder.done()

        except Exception as e:
            # Emit error event
            from vertice_core.openresponses_types import OpenResponsesError

            error = OpenResponsesError(
                code="provider_error",
                message=str(e)[:200],
            )
            builder.fail(error)
            for event in builder.get_events():
                yield event.to_sse()
            yield builder.done()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate non-streaming completion with fallback."""
        max_tokens = max_tokens or self.config.default_max_tokens
        temperature = temperature or self.config.default_temperature
        full_messages = self._build_messages(messages, system_prompt)
        tried: List[str] = []

        for name in self.config.priority:
            if not self._can_use(name):
                continue
            provider = await self._get_provider(name)
            if not provider:
                continue

            tried.append(name)
            try:
                self._current_provider = name
                result = await provider.generate(
                    full_messages, max_tokens=max_tokens, temperature=temperature, **kwargs
                )
                self._record_success(name)
                return result
            except Exception as e:
                self._record_failure(name, e)

        raise AllProvidersExhaustedError(
            f"All providers exhausted: {tried}", tried=tried, errors=self._errors.copy()
        )

    def get_available_providers(self) -> List[str]:
        """Get available and healthy providers."""
        return [n for n in self.config.priority if self._can_use(n) and self._has_api_key(n)]

    def get_provider_status(self) -> Dict[str, Any]:
        """Get detailed status of all providers."""
        return {
            "current_provider": self._current_provider,
            "priority": self.config.priority,
            "providers": {
                n: {
                    "available": self._has_api_key(n),
                    "healthy": self._can_use(n),
                    "failures": self._failures.get(n, 0),
                    "last_error": self._errors.get(n),
                }
                for n in self.config.priority
            },
        }

    def reset_circuit_breaker(self, name: Optional[str] = None) -> None:
        """Reset circuit breaker for provider(s)."""
        if name:
            self._failures.pop(name, None)
            self._errors.pop(name, None)
        else:
            self._failures.clear()
            self._errors.clear()

    def set_preferred_provider(self, name: str) -> bool:
        """Set a provider as preferred (moves to top of priority).

        Args:
            name: Provider name to prioritize

        Returns:
            True if provider was found and moved, False otherwise
        """
        if name not in self.config.priority:
            return False
        self.config.priority.remove(name)
        self.config.priority.insert(0, name)
        self._current_provider = name
        return True

    def get_priority_order(self) -> List[str]:
        """Get current priority order."""
        return self.config.priority.copy()

    def _build_messages(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str]
    ) -> List[Dict[str, str]]:
        if not system_prompt:
            return messages
        return [{"role": "system", "content": system_prompt}, *messages]

    def _can_use(self, name: str) -> bool:
        # Check circuit breaker
        if self._failures.get(name, 0) >= self.config.circuit_breaker_threshold:
            return False
        # Check API key availability
        return self._has_api_key(name)

    def _has_api_key(self, name: str) -> bool:
        env_var = ENV_MAP.get(name)
        return bool(env_var and os.getenv(env_var))

    async def _get_provider(self, name: str) -> Optional[ProviderProtocol]:
        if name in self._providers:
            return self._providers[name]
        provider = self._init_provider(name)
        self._providers[name] = provider
        return provider

    def _init_provider(self, name: str) -> Optional[ProviderProtocol]:
        """
        Initialize provider by name using the registry.

        Uses Dependency Injection pattern to avoid circular imports.
        Providers are registered by vertice_cli at startup.
        """
        from vertice_core.providers import registry

        provider = registry.get(name)
        if provider is None:
            logger.warning(f"Provider not available: {name}")
        return provider

    def _record_success(self, name: str) -> None:
        self._failures[name] = 0
        self._errors.pop(name, None)

    def _record_failure(self, name: str, error: Exception) -> None:
        self._failures[name] = self._failures.get(name, 0) + 1
        self._errors[name] = str(error)

    def _is_rate_limit(self, error: Exception) -> bool:
        s = str(error).lower()
        return "429" in s or "rate limit" in s


# Singleton factory
_default_client: Optional[VerticeClient] = None


def get_client(
    config: Optional[VerticeClientConfig] = None, force_new: bool = False
) -> VerticeClient:
    """Get or create the default VerticeClient instance."""
    global _default_client
    if force_new or config is not None:
        return VerticeClient(config=config)
    if _default_client is None:
        _default_client = VerticeClient()
    return _default_client
