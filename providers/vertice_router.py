"""
Vertice Unified Router - Intelligent Multi-Provider Orchestration

Routes requests to the optimal LLM provider based on:
- Task complexity
- Cost (prefer free tiers)
- Speed requirements
- Provider availability
- Rate limit status
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Protocol, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels for routing decisions."""
    SIMPLE = "simple"          # Formatting, simple chat
    MODERATE = "moderate"      # Code generation, analysis
    COMPLEX = "complex"        # Architecture, deep reasoning
    CRITICAL = "critical"      # Security audit, production code


class SpeedRequirement(str, Enum):
    """Speed requirements for routing."""
    INSTANT = "instant"        # < 1s first token
    FAST = "fast"             # < 3s first token
    NORMAL = "normal"         # < 10s first token
    RELAXED = "relaxed"       # Any speed acceptable


@dataclass
class ProviderStatus:
    """Track provider availability and rate limits."""
    name: str
    available: bool = True
    requests_today: int = 0
    tokens_today: int = 0
    last_request: Optional[datetime] = None
    last_error: Optional[str] = None
    daily_limit: int = 10000
    is_rate_limited: bool = False
    rate_limit_until: Optional[datetime] = None

    def can_use(self) -> bool:
        """Check if provider can be used."""
        if not self.available:
            return False
        if self.is_rate_limited:
            if self.rate_limit_until and datetime.now() > self.rate_limit_until:
                self.is_rate_limited = False
                return True
            return False
        if self.requests_today >= self.daily_limit:
            return False
        return True

    def record_request(self, tokens: int = 0):
        """Record a request."""
        self.requests_today += 1
        self.tokens_today += tokens
        self.last_request = datetime.now()

    def record_error(self, error: str):
        """Record an error."""
        self.last_error = error
        if "429" in error or "rate limit" in error.lower():
            self.is_rate_limited = True
            self.rate_limit_until = datetime.now() + timedelta(minutes=5)


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    provider_name: str
    model_name: str
    reasoning: str
    fallback_providers: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_speed: str = "fast"


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def is_available(self) -> bool: ...
    async def generate(self, messages: List[Dict], **kwargs) -> str: ...
    async def stream_generate(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]: ...
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]: ...
    def get_model_info(self) -> Dict: ...


class VerticeRouter:
    """
    Intelligent LLM Router for Vertice Agency.

    Routing Strategy:
    1. FREE FIRST: Always prefer free tier providers
    2. SPEED AWARE: Route to fastest available for urgent tasks
    3. COMPLEXITY AWARE: Use premium providers for complex tasks
    4. FALLBACK CHAIN: Automatic failover on errors
    """

    # Provider priorities (lower = higher priority)
    # STABILITY MODE: vertex-ai only. Multi-provider routing planned for later.
    PROVIDER_PRIORITY = {
        "vertex-ai": 1,    # PRIMARY - Gemini via Vertex AI (stable)
        # Future: enable after system stabilization
        "groq": 10,
        "cerebras": 11,
        "mistral": 12,
        "openrouter": 13,
        "gemini": 14,
        "azure-openai": 15,
    }

    # STABILITY MODE: All complexity levels route to vertex-ai
    COMPLEXITY_ROUTING = {
        TaskComplexity.SIMPLE: ["vertex-ai"],
        TaskComplexity.MODERATE: ["vertex-ai"],
        TaskComplexity.COMPLEX: ["vertex-ai"],
        TaskComplexity.CRITICAL: ["vertex-ai"],
    }

    # STABILITY MODE: All speed requirements route to vertex-ai
    SPEED_ROUTING = {
        SpeedRequirement.INSTANT: ["vertex-ai"],
        SpeedRequirement.FAST: ["vertex-ai"],
        SpeedRequirement.NORMAL: ["vertex-ai"],
        SpeedRequirement.RELAXED: ["vertex-ai"],
    }

    def __init__(self):
        """Initialize the router."""
        self._providers: Dict[str, LLMProvider] = {}
        self._status: Dict[str, ProviderStatus] = {}
        self._initialized = False

    def _lazy_init(self):
        """Lazy initialize providers.

        TEMPORARY FIX: Only initializes vertex-ai by default.
        Other providers are initialized on-demand via /model command.
        """
        if self._initialized:
            return

        # TEMPORARY FIX: Only import and initialize vertex-ai
        from .vertex_ai import VertexAIProvider

        try:
            provider = VertexAIProvider(model_name="flash")
            if provider.is_available():
                self._providers["vertex-ai"] = provider
                info = provider.get_model_info()
                self._status["vertex-ai"] = ProviderStatus(
                    name="vertex-ai",
                    available=True,
                    daily_limit=info.get("requests_per_day", 10000),
                )
                logger.info(f"✅ Vertex AI initialized: {info.get('model')}")
            else:
                logger.error("❌ Vertex AI not available - check GOOGLE_CLOUD_PROJECT")
        except (RuntimeError, ValueError, ImportError, AttributeError) as e:
            logger.error(f"❌ Failed to initialize Vertex AI: {e}")

        self._initialized = True
        logger.info(f"Vertice Router initialized (vertex-ai only mode)")

    def _init_provider_on_demand(self, name: str) -> bool:
        """Initialize a specific provider on demand (for /model command).

        Args:
            name: Provider name to initialize

        Returns:
            True if provider was initialized successfully
        """
        if name in self._providers:
            return True  # Already initialized

        provider_classes = {
            "groq": (".groq", "GroqProvider", {"model_name": "llama-70b"}),
            "cerebras": (".cerebras", "CerebrasProvider", {"model_name": "llama-70b"}),
            "openrouter": (".openrouter", "OpenRouterProvider", {"model_name": "llama-70b"}),
            "mistral": (".mistral", "MistralProvider", {"model_name": "large"}),
            "gemini": (".gemini", "GeminiProvider", {}),
            "azure-openai": (".azure_openai", "AzureOpenAIProvider", {"deployment": "gpt4o-mini"}),
        }

        if name not in provider_classes:
            logger.warning(f"Unknown provider: {name}")
            return False

        module_name, class_name, kwargs = provider_classes[name]

        try:
            import importlib
            module = importlib.import_module(module_name, package="providers")
            cls = getattr(module, class_name)
            provider = cls(**kwargs)

            if provider.is_available():
                self._providers[name] = provider
                info = provider.get_model_info()
                self._status[name] = ProviderStatus(
                    name=name,
                    available=True,
                    daily_limit=info.get("requests_per_day", 10000),
                )
                logger.info(f"✅ Provider {name} initialized on-demand")
                return True
            else:
                logger.warning(f"⚠️ Provider {name} not available (missing API key)")
                return False
        except (ImportError, AttributeError, RuntimeError, ValueError) as e:
            logger.error(f"❌ Failed to initialize {name}: {e}")
            return False

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        self._lazy_init()
        return [
            name for name, status in self._status.items()
            if status.can_use()
        ]

    def route(
        self,
        task_description: str = "",
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        speed: SpeedRequirement = SpeedRequirement.NORMAL,
        prefer_free: bool = True,
        required_provider: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Route a request to the optimal provider.

        Args:
            task_description: Description of the task (for keyword analysis)
            complexity: Task complexity level
            speed: Speed requirement
            prefer_free: Whether to prefer free tier providers
            required_provider: Force a specific provider

        Returns:
            RoutingDecision with provider selection
        """
        self._lazy_init()

        # If specific provider requested, use it (init on-demand if needed)
        if required_provider:
            # Try to initialize on-demand if not already available
            if required_provider not in self._providers:
                self._init_provider_on_demand(required_provider)

            if required_provider in self._providers:
                status = self._status.get(required_provider)
                if status and status.can_use():
                    return RoutingDecision(
                        provider_name=required_provider,
                        model_name=self._providers[required_provider].get_model_info()["model"],
                        reasoning=f"Explicitly requested provider: {required_provider}",
                    )

        # Get candidate providers based on complexity and speed
        complexity_providers = set(self.COMPLEXITY_ROUTING.get(complexity, []))
        speed_providers = set(self.SPEED_ROUTING.get(speed, []))

        # Intersection of complexity and speed requirements
        candidates = complexity_providers & speed_providers

        # Filter by availability
        available_candidates = [
            p for p in candidates
            if p in self._providers and self._status.get(p, ProviderStatus(name=p)).can_use()
        ]

        if not available_candidates:
            # Fallback to any available provider
            available_candidates = self.get_available_providers()

        if not available_candidates:
            raise RuntimeError("No LLM providers available")

        # Sort by priority (prefer free, then fast)
        if prefer_free:
            available_candidates.sort(key=lambda p: self.PROVIDER_PRIORITY.get(p, 99))

        # Select best provider
        selected = available_candidates[0]
        fallbacks = available_candidates[1:3] if len(available_candidates) > 1 else []

        return RoutingDecision(
            provider_name=selected,
            model_name=self._providers[selected].get_model_info()["model"],
            reasoning=f"Selected {selected} for {complexity.value} task with {speed.value} speed requirement",
            fallback_providers=fallbacks,
            estimated_cost=0.0 if selected in ["groq", "cerebras", "mistral"] else 0.01,
            estimated_speed="ultra_fast" if selected in ["groq", "cerebras"] else "fast",
        )

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a specific provider instance."""
        self._lazy_init()
        return self._providers.get(name)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        speed: SpeedRequirement = SpeedRequirement.NORMAL,
        **kwargs
    ) -> str:
        """
        Generate completion with automatic routing and fallback.

        Args:
            messages: Conversation messages
            complexity: Task complexity
            speed: Speed requirement
            **kwargs: Additional arguments for the provider

        Returns:
            Generated text
        """
        decision = self.route(complexity=complexity, speed=speed)

        # Try primary provider
        provider = self._providers[decision.provider_name]
        status = self._status[decision.provider_name]

        try:
            result = await provider.generate(messages, **kwargs)
            status.record_request()
            return result
        except (RuntimeError, ValueError, ConnectionError, asyncio.TimeoutError) as e:
            status.record_error(str(e))
            logger.warning(f"Provider {decision.provider_name} failed: {e}")

            # Try fallbacks
            for fallback_name in decision.fallback_providers:
                try:
                    fallback = self._providers[fallback_name]
                    result = await fallback.generate(messages, **kwargs)
                    self._status[fallback_name].record_request()
                    return result
                except (RuntimeError, ValueError, ConnectionError, asyncio.TimeoutError) as fe:
                    self._status[fallback_name].record_error(str(fe))
                    continue

            raise RuntimeError(f"All providers failed. Last error: {e}")

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        speed: SpeedRequirement = SpeedRequirement.NORMAL,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat with automatic routing and fallback.

        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            complexity: Task complexity
            speed: Speed requirement
            tools: Optional list of tools for function calling
            **kwargs: Additional arguments

        Yields:
            Text chunks
        """
        decision = self.route(complexity=complexity, speed=speed)

        provider = self._providers[decision.provider_name]
        status = self._status[decision.provider_name]

        try:
            async for chunk in provider.stream_chat(
                messages,
                system_prompt=system_prompt,
                tools=tools,
                **kwargs
            ):
                yield chunk
            status.record_request()
        except (RuntimeError, ValueError, ConnectionError, asyncio.TimeoutError) as e:
            status.record_error(str(e))
            logger.warning(f"Provider {decision.provider_name} failed: {e}")

            # Try fallbacks
            for fallback_name in decision.fallback_providers:
                try:
                    fallback = self._providers[fallback_name]
                    async for chunk in fallback.stream_chat(
                        messages,
                        system_prompt=system_prompt,
                        tools=tools,
                        **kwargs
                    ):
                        yield chunk
                    self._status[fallback_name].record_request()
                    return
                except (ConnectionError, asyncio.TimeoutError, RuntimeError, ValueError) as fallback_error:
                    self._status[fallback_name].record_error(str(fallback_error))
                    continue

            yield f"\n[Error: All providers failed - {e}]"

    def get_status_report(self) -> str:
        """Get a status report of all providers."""
        self._lazy_init()

        lines = ["Vertice Router Status", "=" * 40]

        for name, status in self._status.items():
            provider = self._providers.get(name)
            if provider:
                info = provider.get_model_info()
                available = "✅" if status.can_use() else "❌"
                lines.append(
                    f"{available} {name}: {info['model']} "
                    f"({status.requests_today}/{status.daily_limit} requests)"
                )
            else:
                lines.append(f"❌ {name}: Not configured")

        return "\n".join(lines)


# Global router instance
_router: Optional[VerticeRouter] = None


def get_router() -> VerticeRouter:
    """Get the global router instance."""
    global _router
    if _router is None:
        _router = VerticeRouter()
    return _router
