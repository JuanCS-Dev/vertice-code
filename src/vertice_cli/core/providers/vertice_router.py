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
from typing import Dict, List, Optional, AsyncGenerator, Protocol, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

from vertice_cli.core.types import ModelInfo

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
    def get_model_info(self) -> ModelInfo: ...


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
    # Mode: "enterprise" prioritizes Vertex AI, "free" prioritizes free tiers
    PROVIDER_PRIORITY_ENTERPRISE = {
        "vertex-ai": 1,  # Vertex AI Gemini 2.5 Pro - PRIMARY (Best for code, 2026 standard)
        "anthropic-vertex": 2,  # Claude 4.5 - Secondary
        "azure-openai": 3,  # Enterprise GPT-4 via Azure
        "groq": 4,  # 14,400 req/day, ultra-fast fallback
        "cerebras": 5,  # 1M tokens/day, fastest fallback
        "mistral": 6,  # 1B tokens/month
        "openrouter": 7,  # 200 req/day on free models
        "gemini": 8,  # Legacy API
    }

    PROVIDER_PRIORITY_FREE = {
        "groq": 1,  # 14,400 req/day, ultra-fast
        "cerebras": 2,  # 1M tokens/day, fastest
        "mistral": 3,  # 1B tokens/month
        "openrouter": 4,  # 200 req/day on free models
        "gemini": 5,  # Your existing quota (legacy API)
        "anthropic-vertex": 6,  # Enterprise Claude
        "vertex-ai": 7,  # Enterprise Gemini via Vertex AI
        "azure-openai": 8,  # Enterprise GPT-4 via Azure
    }

    # Default to enterprise mode (user has GCloud credits)
    PROVIDER_PRIORITY = PROVIDER_PRIORITY_ENTERPRISE

    # Task complexity to provider mapping (Enterprise mode - Vertex AI first)
    COMPLEXITY_ROUTING = {
        TaskComplexity.SIMPLE: ["vertex-ai", "groq", "cerebras"],
        TaskComplexity.MODERATE: ["vertex-ai", "groq", "mistral"],
        TaskComplexity.COMPLEX: ["vertex-ai", "azure-openai"],
        TaskComplexity.CRITICAL: ["vertex-ai", "azure-openai"],  # Enterprise only
    }

    # Speed requirement to provider mapping (Vertex AI is fast!)
    SPEED_ROUTING = {
        SpeedRequirement.INSTANT: ["vertex-ai", "groq", "cerebras"],
        SpeedRequirement.FAST: ["vertex-ai", "groq", "cerebras"],
        SpeedRequirement.NORMAL: ["vertex-ai", "groq", "mistral", "openrouter"],
        SpeedRequirement.RELAXED: ["vertex-ai", "mistral", "openrouter", "azure-openai"],
    }

    def __init__(self, enterprise_mode: bool = True):
        """Initialize the router.

        Args:
            enterprise_mode: If True, prioritize Vertex AI (for users with GCloud credits).
                           If False, prioritize free tier providers.
        """
        self._providers: Dict[str, LLMProvider] = {}
        self._status: Dict[str, ProviderStatus] = {}
        self._initialized = False
        self._enterprise_mode = enterprise_mode

        # Set priority based on mode
        if enterprise_mode:
            self.PROVIDER_PRIORITY = self.PROVIDER_PRIORITY_ENTERPRISE
        else:
            self.PROVIDER_PRIORITY = self.PROVIDER_PRIORITY_FREE

    def _lazy_init(self):
        """Lazy initialize providers."""
        if self._initialized:
            return

        # Import providers - Free Tier
        from .groq import GroqProvider
        from .cerebras import CerebrasProvider
        from .openrouter import OpenRouterProvider
        from .mistral import MistralProvider
        from .gemini import GeminiProvider

        # Import providers - Enterprise (Your Infrastructure)
        from .vertex_ai import VertexAIProvider
        from .anthropic_vertex import AnthropicVertexProvider
        from .azure_openai import AzureOpenAIProvider

        # Initialize all providers
        provider_classes = {
            # Free Tier Providers
            "groq": (GroqProvider, {"model_name": "llama-70b"}),
            "cerebras": (CerebrasProvider, {"model_name": "llama-70b"}),
            "openrouter": (OpenRouterProvider, {"model_name": "llama-70b"}),
            "mistral": (MistralProvider, {"model_name": "large"}),
            "gemini": (GeminiProvider, {}),  # Legacy - prefer vertex-ai
            # Enterprise Providers (Your Infrastructure)
            "anthropic-vertex": (AnthropicVertexProvider, {"model_name": "sonnet-4.5"}),
            "vertex-ai": (VertexAIProvider, {"model_name": "pro"}),  # Gemini 2.5 Pro
            "azure-openai": (AzureOpenAIProvider, {"deployment": "gpt4o-mini"}),
        }

        for name, (cls, kwargs) in provider_classes.items():
            try:
                provider = cls(**kwargs)
                # Only initialize providers that are actually available
                if provider.is_available():
                    self._providers[name] = provider
                    info = provider.get_model_info()
                    daily_limit = info.get("requests_per_day", 10000)
                    self._status[name] = ProviderStatus(
                        name=name,
                        available=True,
                        daily_limit=daily_limit,
                    )
                    logger.debug("Provider '%s' initialized successfully.", name)
                else:
                    logger.warning("Provider '%s' not available (missing API key or config).", name)
            except (
                ImportError,
                AttributeError,
                RuntimeError,
                ValueError,
                ConnectionError,
                asyncio.TimeoutError,
            ) as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")
                continue
        self._initialized = True
        logger.info(f"Vertice Router initialized with {len(self._providers)} providers")

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        self._lazy_init()
        return [name for name, status in self._status.items() if status.can_use()]

    async def route_with_claude_analysis(
        self,
        task_description: str = "",
        complexity: Optional[TaskComplexity] = None,
        speed: Optional[SpeedRequirement] = None,
        prefer_free: bool = True,
    ) -> RoutingDecision:
        """Route using Claude analysis for intelligent decision making."""
        # First analyze the task with Claude
        if not complexity or not speed:
            analysis = await self._analyze_task_with_claude(task_description)
            complexity = complexity or TaskComplexity(analysis.get("complexity", "moderate"))
            speed = speed or SpeedRequirement(analysis.get("speed", "normal"))

        return self.route(task_description, complexity, speed, prefer_free)

    async def _analyze_task_with_claude(self, task_description: str) -> Dict[str, Any]:
        """Use LLM to analyze task complexity and requirements."""
        # Get the best available LLM (prefer Vertex AI)
        llm_client = None
        for provider_name in ["vertex-ai", "groq", "cerebras"]:
            if provider_name in self._providers:
                llm_client = self._providers[provider_name]
                break

        if not llm_client:
            # Fallback to defaults
            return {
                "complexity": TaskComplexity.MODERATE,
                "speed": SpeedRequirement.NORMAL,
                "skills_needed": ["general"],
                "estimated_time": "medium",
            }

        analysis_prompt = f"""Analyze this software development task and classify its requirements:

TASK: {task_description}

Provide analysis in JSON format:
{{
    "complexity": "simple|moderate|complex|critical",
    "speed": "instant|fast|normal|relaxed",
    "skills_needed": ["skill1", "skill2"],
    "estimated_time": "short|medium|long",
    "recommended_provider": "vertex-ai|groq|etc",
    "reasoning": "brief explanation"
}}

Focus on:
- TECHNICAL COMPLEXITY: algorithm design, architecture decisions, multiple technologies
- TIME SENSITIVITY: user waiting, background processing, iterative development
- EXPERTISE REQUIRED: specialized knowledge, debugging, optimization

Respond with ONLY the JSON object."""

        try:
            response = await llm_client.generate(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=300,
                temperature=0.0,
            )

            # Simple JSON extraction
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                print(f"Failed to parse Claude analysis: {response}")

        except Exception as e:
            print(f"Claude analysis failed: {e}")

        # Fallback
        return {
            "complexity": TaskComplexity.MODERATE,
            "speed": SpeedRequirement.NORMAL,
            "skills_needed": ["general"],
            "estimated_time": "medium",
            "reasoning": "fallback due to analysis failure",
        }

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

        # If specific provider requested, use it
        if required_provider:
            if required_provider in self._providers:
                status = self._status.get(required_provider)
                if status and status.can_use():
                    model_info = self._providers[required_provider].get_model_info()
                    try:
                        model_name = model_info["model"]
                    except KeyError:
                        raise ValueError(
                            f"Provider '{required_provider}' returned invalid model info: missing 'model' key."
                        )
                    decision = RoutingDecision(
                        provider_name=required_provider,
                        model_name=model_name,
                        reasoning=f"Explicitly requested provider: {required_provider}",
                    )
                    logger.info(
                        "Routing decision: %s (Reason: %s)",
                        decision.provider_name,
                        decision.reasoning,
                    )
                    return decision

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

        model_info = self._providers[selected].get_model_info()
        try:
            model_name = model_info["model"]
        except KeyError:
            raise ValueError(
                f"Provider '{selected}' returned invalid model info: missing 'model' key."
            )

        decision = RoutingDecision(
            provider_name=selected,
            model_name=model_name,
            reasoning=f"Selected '{selected}' for {complexity.value} task with {speed.value} speed requirement",
            fallback_providers=fallbacks,
            estimated_cost=0.0 if selected in ["groq", "cerebras", "mistral"] else 0.01,
            estimated_speed="ultra_fast" if selected in ["groq", "cerebras"] else "fast",
        )
        logger.info(
            "Routing decision: %s (Reason: %s, Fallbacks: %s)",
            decision.provider_name,
            decision.reasoning,
            decision.fallback_providers,
        )
        return decision

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
            logger.info("Attempting to generate with primary provider: %s", decision.provider_name)
            result = await provider.generate(messages, **kwargs)
            status.record_request()
            return result
        except (RuntimeError, ValueError, ConnectionError, asyncio.TimeoutError) as e:
            status.record_error(str(e))
            logger.warning(
                "Primary provider '%s' failed with error: %s. Attempting fallbacks.",
                decision.provider_name,
                e,
                exc_info=True,
            )

            # Try fallbacks
            for fallback_name in decision.fallback_providers:
                try:
                    logger.info("Attempting fallback generation with: %s", fallback_name)
                    fallback = self._providers[fallback_name]
                    result = await fallback.generate(messages, **kwargs)
                    self._status[fallback_name].record_request()
                    return result
                except (RuntimeError, ValueError, ConnectionError, asyncio.TimeoutError) as fe:
                    self._status[fallback_name].record_error(str(fe))
                    logger.warning(
                        "Fallback provider '%s' also failed.", fallback_name, exc_info=True
                    )
                    continue

            logger.error("All available providers failed for the generation task.")
            raise RuntimeError(f"All providers failed. Last error: {e}")

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        speed: SpeedRequirement = SpeedRequirement.NORMAL,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        print(f"[DEBUG ROUTER] stream_chat called with complexity={complexity}, speed={speed}")
        """
        Stream chat with automatic routing and fallback.

        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            complexity: Task complexity
            speed: Speed requirement
            **kwargs: Additional arguments

        Yields:
            Text chunks
        """
        decision = self.route(complexity=complexity, speed=speed)

        provider = self._providers[decision.provider_name]
        status = self._status[decision.provider_name]

        print(
            f"[DEBUG ROUTER] Routing decision: provider={decision.provider_name}, fallbacks={decision.fallback_providers}"
        )

        try:
            print(
                f"[DEBUG ROUTER] Attempting to stream with primary provider: {decision.provider_name}"
            )
            async for chunk in provider.stream_chat(
                messages, system_prompt=system_prompt, **kwargs
            ):
                yield chunk
            status.record_request()
        except Exception as e:
            status.record_error(str(e))
            logger.warning(
                "Primary streaming provider '%s' failed: %s. Attempting fallbacks.",
                decision.provider_name,
                e,
                exc_info=True,
            )

            # Try fallbacks
            for fallback_name in decision.fallback_providers:
                try:
                    logger.info("Attempting fallback streaming with: %s", fallback_name)
                    fallback = self._providers[fallback_name]
                    async for chunk in fallback.stream_chat(
                        messages, system_prompt=system_prompt, **kwargs
                    ):
                        yield chunk
                    self._status[fallback_name].record_request()
                    return
                except Exception:
                    logger.warning(
                        "Fallback streaming provider '%s' also failed.",
                        fallback_name,
                        exc_info=True,
                    )
                    continue
            logger.error("All available providers failed for the streaming task.")
            raise RuntimeError(f"All streaming providers failed: {e}")

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
