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

import asyncio
import os
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

    SIMPLE = "simple"  # Formatting, simple chat
    MODERATE = "moderate"  # Code generation, analysis
    COMPLEX = "complex"  # Architecture, deep reasoning
    CRITICAL = "critical"  # Security audit, production code


class SpeedRequirement(str, Enum):
    """Speed requirements for routing."""

    INSTANT = "instant"  # < 1s first token
    FAST = "fast"  # < 3s first token
    NORMAL = "normal"  # < 10s first token
    RELAXED = "relaxed"  # Any speed acceptable


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
    async def stream_generate(
        self, messages: List[Dict], **kwargs
    ) -> AsyncGenerator[str, None]: ...
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

    # PROVIDER PRIORITIES (Lower = Higher Priority)
    # Claude 4.5 is the supreme primary powerhouse for 2026.
    PROVIDER_PRIORITY = {
        "anthropic-vertex": 1,  # PRIMARY - Claude 4.5 (Optimized & Powerful)
        "vertex-ai": 2,  # SECONDARY - Gemini (Stable Tooling)
        "groq": 10,
        "cerebras": 11,
        "mistral": 12,
    }

    # COMPLEXITY ROUTING (2026 Standards)
    # All levels now prefer Anthropic Vertex as the first option.
    COMPLEXITY_ROUTING = {
        TaskComplexity.SIMPLE: ["anthropic-vertex", "vertex-ai", "groq"],
        TaskComplexity.MODERATE: ["anthropic-vertex", "vertex-ai", "groq"],
        TaskComplexity.COMPLEX: ["anthropic-vertex", "vertex-ai"],
        TaskComplexity.CRITICAL: ["anthropic-vertex", "vertex-ai"],
    }

    # SPEED ROUTING
    SPEED_ROUTING = {
        SpeedRequirement.INSTANT: ["groq", "cerebras", "anthropic-vertex"],
        SpeedRequirement.FAST: ["anthropic-vertex", "vertex-ai", "groq"],
        SpeedRequirement.NORMAL: ["anthropic-vertex", "vertex-ai"],
        SpeedRequirement.RELAXED: ["anthropic-vertex", "vertex-ai"],
    }

    def __init__(self):
        """Initialize the router."""
        self._providers: Dict[str, LLMProvider] = {}
        self._status: Dict[str, ProviderStatus] = {}
        self._initialized = False

    def _lazy_init(self):
        """Initialize providers on first use."""
        if self._initialized:
            return

        # Initialize providers
        self._init_providers()
        self._initialized = True

    def _init_providers(self):
        """Initialize all configured providers."""
        # Import here to avoid circular imports
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider

        # Anthropic Vertex (Claude 4.5)
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

                self._providers["anthropic-vertex"] = AnthropicVertexProvider()
                self._status["anthropic-vertex"] = ProviderStatus(name="anthropic-vertex")
            except Exception as e:
                logger.warning(f"Failed to initialize anthropic-vertex: {e}")

        # Vertex AI (Gemini)
        try:
            self._providers["vertex-ai"] = VertexAIProvider()
            self._status["vertex-ai"] = ProviderStatus(name="vertex-ai")
        except Exception as e:
            logger.warning(f"Failed to initialize vertex-ai: {e}")

    def _init_provider_on_demand(self, provider_name: str):
        """Initialize a provider on demand."""
        # For now, just call _init_providers (they're all initialized at once)
        self._init_providers()

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        self._lazy_init()
        return [
            name
            for name, status in self._status.items()
            if status.can_use() and name in self._providers
        ]

    def route(
        self,
        task_description: str = "",
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        speed: SpeedRequirement = SpeedRequirement.NORMAL,
        prefer_free: bool = True,
        required_provider: Optional[str] = None,
    ) -> RoutingDecision:
        """Route a request to the optimal provider."""
        self._lazy_init()

        # Analyze task description for RAG or Tooling keywords
        is_rag = any(
            kw in task_description.lower()
            for kw in ["rag", "context", "search", "document", "knowledge"]
        )
        is_tooling = any(
            kw in task_description.lower() for kw in ["tool", "function", "api", "execute", "run"]
        )

        # Force Anthropic for RAG in 2026 due to Prompt Caching efficiency
        if is_rag and not required_provider:
            required_provider = "anthropic-vertex"

        # Force Gemini for Tooling (if user preferred and Gemini 3 works)
        # Note: Gemini 3 is often preferred for latency in tools, but user reported issues.
        # We stick to stable vertex-ai (Gemini 2.5) for now.
        if is_tooling and not required_provider:
            required_provider = "vertex-ai"

            # If specific provider requested, use it
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
            p
            for p in candidates
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

        # Model Selection Strategy (2026 Optimized)
        model_name = self._providers[selected].get_model_info()["model"]

        if selected == "anthropic-vertex":
            # Sonnet 4.5 for Light tasks, Opus 4.5 for Heavy tasks
            if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
                model_name = "claude-sonnet-4-5@20250929"  # Sonnet
            else:
                model_name = "claude-opus-4-5@20251101"  # Opus

        return RoutingDecision(
            provider_name=selected,
            model_name=model_name,
            reasoning=f"Selected {selected} ({model_name}) for {complexity.value} task with {speed.value} speed requirement",
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
        **kwargs,
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
            # Pass the specifically selected model
            result = await provider.generate(messages, model=decision.model_name, **kwargs)
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
        **kwargs,
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
                model=decision.model_name,
                **kwargs,
            ):
                yield chunk
            status.record_request()

        except Exception as e:
            status.record_error(str(e))
            logger.warning(f"Provider {decision.provider_name} failed: {e}")

            # Try fallbacks
            for fallback_name in decision.fallback_providers:
                try:
                    logger.info(f"Trying fallback provider: {fallback_name}")
                    fallback = self._providers[fallback_name]
                    async for chunk in fallback.stream_chat(
                        messages, system_prompt=system_prompt, tools=tools, **kwargs
                    ):
                        yield chunk
                    self._status[fallback_name].record_request()
                    return
                except Exception as fallback_error:
                    logger.warning(
                        f"Fallback provider {fallback_name} also failed: {fallback_error}"
                    )
                    self._status[fallback_name].record_error(str(fallback_error))
                    continue

            logger.error("All streaming providers failed")
            raise RuntimeError(f"All providers failed: {e}")

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
