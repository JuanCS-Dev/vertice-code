"""
ProviderManager - LLM provider selection and management.

Extracted from Bridge as part of Phase 5.1 TUI Lightweight refactoring.

Implements intelligent provider routing:
- Auto-detection of task complexity
- Provider initialization with lazy loading
- Fallback chain support

References:
- OpenAI Multi-Agent: https://cookbook.openai.com/examples/agents_sdk
- LiteLLM Routing: https://docs.litellm.ai/docs/routing

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Protocol

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for provider selection."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    GOVERNANCE = "governance"


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients."""

    @property
    def is_available(self) -> bool:
        """Check if client is available."""
        ...


@dataclass
class ProviderConfig:
    """Configuration for provider selection."""

    default_provider: str = "auto"
    enable_complexity_detection: bool = True
    complexity_threshold: int = 2
    long_message_threshold: int = 500
    very_long_message_threshold: int = 1000

    # Pattern sets for complexity detection
    simple_patterns: List[str] = field(
        default_factory=lambda: [
            r"^(what|who|when|where|how|why)\s+\w+\??$",
            r"^\w+\s*\?$",
            r"^(hi|hello|hey|thanks|ok|yes|no)\b",
        ]
    )

    complex_patterns: List[str] = field(
        default_factory=lambda: [
            r"\b(create|build|implement|design|architect)\b.*\b(system|pipeline|framework|application)\b",
            r"\b(analyze|debug|investigate|troubleshoot)\b.*\b(complex|multiple|entire)\b",
            r"\b(refactor|optimize|improve)\b.*\b(codebase|architecture|performance)\b",
            r"\b(multi.?step|step.?by.?step|sequentially|iteratively)\b",
            r"\b(remember|recall|previous|earlier|context)\b",
            r"\b(simulate|predict|plan|strategy)\b",
            r"\b(evolve|learn|adapt|improve over time)\b",
        ]
    )

    governance_patterns: List[str] = field(
        default_factory=lambda: [
            r"\b(tribunal|governance|evaluate|judge)\b",
            r"\b(constitution|compliance|policy)\b",
            r"\b(remember long.?term|consolidate|vault)\b",
            r"\b(generate tool|create tool|dynamic tool)\b",
            r"\b(VERITAS|SOPHIA|DIKE)\b",
        ]
    )


class ProviderManager:
    """
    Manages LLM provider selection and initialization.

    Supports multiple providers with intelligent routing:
    - Gemini: Default for simple tasks
    - Prometheus: Complex multi-step tasks
    - Maximus: Governance and long-term memory

    Usage:
        manager = ProviderManager(gemini_client)
        client, name = manager.get_client("complex task message")
    """

    def __init__(
        self,
        gemini_client: LLMClientProtocol,
        prometheus_factory: Optional[Any] = None,
        maximus_factory: Optional[Any] = None,
        config: Optional[ProviderConfig] = None,
    ):
        """Initialize provider manager.

        Args:
            gemini_client: Default Gemini client
            prometheus_factory: Factory for Prometheus client (lazy init)
            maximus_factory: Factory for Maximus client (lazy init)
            config: Provider configuration
        """
        self.gemini = gemini_client
        self._prometheus_factory = prometheus_factory
        self._maximus_factory = maximus_factory
        self._prometheus: Optional[LLMClientProtocol] = None
        self._maximus: Optional[LLMClientProtocol] = None

        self.config = config or ProviderConfig()
        self._mode = os.getenv("VERTICE_PROVIDER", self.config.default_provider)
        self._complexity_cache: Dict[str, TaskComplexity] = {}

    @property
    def mode(self) -> str:
        """Get current provider mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set provider mode.

        Now supports dynamic providers (groq, cerebras) via GeminiClient/VerticeRouter.
        """
        self._mode = value
        # If mode is a specific provider, tell the GeminiClient to switch
        if value not in {"auto", "prometheus", "maximus"} and hasattr(self.gemini, "set_provider"):
            self.gemini.set_provider(value)

    def detect_complexity(self, message: str) -> TaskComplexity:
        """Detect task complexity from message content.

        Uses pattern matching and heuristics to determine
        the appropriate complexity level.

        Args:
            message: User message to analyze

        Returns:
            Detected complexity level
        """
        # Check cache first
        cache_key = message[:100]  # Use first 100 chars as key
        if cache_key in self._complexity_cache:
            return self._complexity_cache[cache_key]

        message_lower = message.lower()

        # Check governance patterns first (highest priority)
        for pattern in self.config.governance_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                self._complexity_cache[cache_key] = TaskComplexity.GOVERNANCE
                return TaskComplexity.GOVERNANCE

        # Check simple patterns
        for pattern in self.config.simple_patterns:
            if re.search(pattern, message_lower):
                self._complexity_cache[cache_key] = TaskComplexity.SIMPLE
                return TaskComplexity.SIMPLE

        # Score complex patterns
        complexity_score = 0
        for pattern in self.config.complex_patterns:
            if re.search(pattern, message_lower):
                complexity_score += 1

        # Length heuristics
        if len(message) > self.config.long_message_threshold:
            complexity_score += 1
        if len(message) > self.config.very_long_message_threshold:
            complexity_score += 1

        # Code indicators
        if "```" in message or "def " in message or "class " in message:
            complexity_score += 1

        # Determine complexity level
        if complexity_score >= self.config.complexity_threshold:
            result = TaskComplexity.COMPLEX
        elif complexity_score >= 1:
            result = TaskComplexity.MODERATE
        else:
            result = TaskComplexity.SIMPLE

        self._complexity_cache[cache_key] = result
        return result

    def _get_prometheus(self) -> LLMClientProtocol:
        """Get or create Prometheus client (lazy initialization)."""
        if self._prometheus is None:
            if self._prometheus_factory is None:
                raise RuntimeError("Prometheus factory not configured")
            self._prometheus = self._prometheus_factory()
        return self._prometheus

    def _get_maximus(self) -> LLMClientProtocol:
        """Get or create Maximus client (lazy initialization)."""
        if self._maximus is None:
            if self._maximus_factory is None:
                raise RuntimeError("Maximus factory not configured")
            self._maximus = self._maximus_factory()
        return self._maximus

    def get_client(self, message: str = "") -> Tuple[LLMClientProtocol, str]:
        """Get appropriate LLM client based on mode and task complexity.

        Args:
            message: User message (used for auto mode)

        Returns:
            Tuple of (client, provider_name)
        """
        if self._mode == "prometheus":
            return self._get_prometheus(), "prometheus"

        if self._mode == "maximus":
            return self._get_maximus(), "maximus"

        # If mode is not one of the special agents, use GeminiClient (which wraps VerticeClient)
        # We don't check for "gemini" specifically anymore, as any other mode (groq, cerebras)
        # relies on GeminiClient/VerticeClient to handle the routing.
        if self._mode != "auto":
            provider_name = self._get_gemini_provider_name()
            return self.gemini, provider_name

        # Auto mode - detect complexity
        if self.config.enable_complexity_detection and message:
            complexity = self.detect_complexity(message)

            if complexity == TaskComplexity.GOVERNANCE:
                try:
                    return self._get_maximus(), "maximus"
                except RuntimeError:
                    logger.warning("Maximus not available, falling back to Gemini")

            elif complexity == TaskComplexity.COMPLEX:
                try:
                    return self._get_prometheus(), "prometheus"
                except RuntimeError:
                    logger.warning("Prometheus not available, falling back to Gemini")

        # Get actual provider name (may be router, vertex-ai, or gemini)
        provider_name = self._get_gemini_provider_name()
        return self.gemini, provider_name

    def _get_gemini_provider_name(self) -> str:
        """Get the actual provider name from GeminiClient.

        GeminiClient may use VerticeRouter internally which routes to
        Groq, Cerebras, Mistral, etc.
        """
        if hasattr(self.gemini, "get_current_provider_name"):
            return self.gemini.get_current_provider_name()
        return "gemini"

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers.

        Returns:
            Dict with provider availability and current mode
        """
        status = {
            "mode": self._mode,
            "providers": {
                "prometheus": {
                    "available": self._prometheus_factory is not None,
                    "initialized": self._prometheus is not None,
                    "active": self._mode == "prometheus",
                },
                "maximus": {
                    "available": self._maximus_factory is not None,
                    "initialized": self._maximus is not None,
                    "active": self._mode == "maximus",
                },
            },
            "complexity_cache_size": len(self._complexity_cache),
        }

        # Add dynamic providers from GeminiClient/VerticeClient
        if hasattr(self.gemini, "get_available_providers"):
            available = self.gemini.get_available_providers()
            current = getattr(self.gemini, "get_current_provider_name", lambda: "gemini")()

            for p in available:
                status["providers"][p] = {"available": True, "active": current == p}

            # Ensure "gemini" is always listed if available
            if "gemini" not in status["providers"] and getattr(self.gemini, "is_available", True):
                status["providers"]["gemini"] = {"available": True, "active": current == "gemini"}

        return status

    def clear_complexity_cache(self) -> None:
        """Clear the complexity detection cache."""
        self._complexity_cache.clear()
