"""Production-grade multi-backend LLM client.

This is a thin wrapper around VerticeClient for CLI-specific features.
All provider routing and resilience is delegated to VerticeClient.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, zero TODOs.
"""

from __future__ import annotations

import logging
import os
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, TypedDict, Union

try:
    from vertice_core.core.types import (
        JSONDict,
        TokenCallback,
        ToolCall,
        ToolDefinition,
    )
except ImportError:
    # Define fallbacks for environments where types are not available
    TokenCallback = Any
    ToolDefinition = Dict[str, Any]
    ToolCall = Dict[str, Any]
    JSONDict = Dict[str, Any]


# Silence gRPC/glog warnings
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "3")
from .config import config
from vertice_core.utils.error_handler import CircuitBreaker
from vertice_core.core.errors.types import CircuitState
from vertice_core.core.resilience import RateLimiter

warnings.filterwarnings("ignore", message=".*ALTS.*")

logger = logging.getLogger(__name__)


class MetricsSummary(TypedDict):
    """Summary of LLM request metrics."""

    total_requests: int
    success_rate: str
    avg_latency_ms: str
    total_tokens: int
    providers: Dict[str, Dict[str, int]]
    vertice_status: Optional[JSONDict]


class GenerationResult(TypedDict, total=False):
    """Result of a generation call."""

    content: str
    tokens_used: int
    tool_calls: List[ToolCall]


@dataclass
class RequestMetrics:
    """Telemetry for LLM requests."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_latency: float = 0.0
    provider_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def record_request(
        self,
        provider: str,
        success: bool,
        latency: float,
        tokens: int = 0,
    ) -> None:
        """Record request metrics."""
        self.total_requests += 1
        self.total_latency += latency
        self.total_tokens += tokens

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if provider not in self.provider_stats:
            self.provider_stats[provider] = {"success": 0, "fail": 0, "tokens": 0}

        if success:
            self.provider_stats[provider]["success"] += 1
        else:
            self.provider_stats[provider]["fail"] += 1
        self.provider_stats[provider]["tokens"] += tokens

    def get_summary(self) -> MetricsSummary:
        """Get metrics summary."""
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = self.successful_requests / self.total_requests * 100

        avg_latency = 0.0
        if self.successful_requests > 0:
            avg_latency = self.total_latency / self.successful_requests

        return {
            "total_requests": self.total_requests,
            "success_rate": f"{success_rate:.1f}%",
            "avg_latency_ms": f"{avg_latency * 1000:.0f}",
            "total_tokens": self.total_tokens,
            "providers": self.provider_stats,
        }


class LLMClient:
    """Production-grade LLM client using VerticeClient for routing."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout: float = 30.0,
        enable_telemetry: bool = True,
        token_callback: Optional[TokenCallback] = None,
    ) -> None:
        """Initialize LLM client.

        Args:
            max_retries: Max retries per request
            timeout: Request timeout in seconds
            enable_telemetry: Enable request metrics
            token_callback: Optional callback(input_tokens, output_tokens)
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.token_callback = token_callback
        self.metrics = RequestMetrics() if enable_telemetry else None

        # Use VerticeClient for all provider routing
        self._vertice_coreent: Optional[Any] = None
        self._init_vertice_coreent()

        # Legacy fallback providers
        self._hf_client: Optional[Any] = None
        self._nebius_client: Optional[Any] = None
        self._gemini_client: Optional[Any] = None
        self._ollama_client: Optional[Any] = None

    def _init_vertice_coreent(self) -> None:
        """Initialize VerticeClient for unified routing."""
        try:
            from vertice_core.clients import get_client

            self._vertice_coreent = get_client()
            available = self._vertice_coreent.get_available_providers()
            if available:
                logger.info(
                    f"VerticeClient: {len(available)} providers ({', '.join(available[:3])}...)"
                )
            else:
                logger.debug("No providers configured in VerticeClient")
        except ImportError:
            logger.debug("VerticeClient not available, using legacy providers")
        except Exception as e:
            logger.debug(f"VerticeClient init failed: {e}")

    def get_available_providers(self) -> List[str]:
        """Get list of available providers.

        Delegates to VerticeClient if available, otherwise returns
        legacy priority list.
        """
        if self._vertice_coreent:
            try:
                return self._vertice_coreent.get_available_providers()
            except Exception as e:
                logger.debug(f"Failed to check providers: {e}")
        return self.provider_priority

    @property
    def default_provider(self) -> str:
        """Get current default provider."""
        if self._vertice_coreent:
            return self._vertice_coreent.current_provider or "vertex-ai"
        return "vertex-ai"

    @property
    def provider_priority(self) -> List[str]:
        """Get provider priority list."""
        if self._vertice_coreent:
            return self._vertice_coreent.get_available_providers()
        return ["gemini", "nebius", "hf", "ollama"]

    async def stream_chat(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
        enable_failover: bool = True,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion with automatic failover.

        Args:
            prompt: User prompt
            context: Optional system context
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            provider: Preferred provider (auto = use priority)
            enable_failover: Enable automatic failover

        Yields:
            Response text chunks

        Raises:
            ValueError: If prompt is empty
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        max_tokens = max_tokens or config.max_tokens
        temperature = temperature or config.temperature
        start_time = time.time()

        # Build messages
        messages: List[Dict[str, str]] = []
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"You are a helpful coding assistant. Context:\n\n{context}",
                }
            )
        messages.append({"role": "user", "content": prompt})

        # Use VerticeClient if available
        if self._vertice_coreent:
            try:
                async for chunk in self._vertice_coreent.stream_chat(
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=tools,
                ):
                    yield chunk

                # Record success
                if self.metrics:
                    provider_name = self._vertice_coreent.current_provider or "unknown"
                    latency = time.time() - start_time
                    self.metrics.record_request(provider_name, True, latency)
                return

            except Exception as e:
                logger.warning(f"VerticeClient failed: {e}")
                if self.metrics:
                    latency = time.time() - start_time
                    self.metrics.record_request("vertice", False, latency)

        # Legacy fallback
        async for chunk in self._stream_legacy(messages, max_tokens, temperature):
            yield chunk

    async def _stream_legacy(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream via legacy providers (Gemini, Nebius, etc.)."""
        # Try Gemini first
        gemini = self._get_gemini()
        if gemini:
            try:
                async for chunk in gemini.stream_chat(
                    messages, max_tokens=max_tokens, temperature=temperature
                ):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")

        # Try Nebius
        nebius = self._get_nebius()
        if nebius:
            try:
                async for chunk in nebius.stream_chat(
                    messages, max_tokens=max_tokens, temperature=temperature
                ):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Nebius failed: {e}")

        # Fallback message
        yield "All providers failed. Please check your API keys."

    def _get_gemini(self) -> Optional[Any]:
        """Lazy load Gemini provider."""
        if self._gemini_client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    from .providers.gemini import GeminiProvider

                    self._gemini_client = GeminiProvider(api_key=api_key)
                except Exception as e:
                    logger.warning(f"Gemini init failed: {e}")
        return self._gemini_client

    def _get_nebius(self) -> Optional[Any]:
        """Lazy load Nebius provider."""
        if self._nebius_client is None:
            api_key = os.getenv("NEBIUS_API_KEY")
            if api_key:
                try:
                    from .providers.nebius import NebiusProvider

                    self._nebius_client = NebiusProvider(api_key=api_key)
                except Exception as e:
                    logger.warning(f"Nebius init failed: {e}")
        return self._nebius_client

    def validate(self) -> Dict[str, bool]:
        """Validate available providers.

        Returns:
            Dict mapping provider names to availability status
        """
        status: Dict[str, bool] = {}

        # Check VerticeClient providers
        if self._vertice_coreent:
            provider_status = self._vertice_coreent.get_provider_status()
            for name, info in provider_status.get("providers", {}).items():
                status[name] = info.get("available", False)

        # Check legacy providers
        status["gemini"] = status.get("gemini", bool(os.getenv("GEMINI_API_KEY")))
        status["nebius"] = bool(os.getenv("NEBIUS_API_KEY"))
        status["hf"] = bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN"))
        status["ollama"] = bool(os.getenv("OLLAMA_BASE_URL"))

        return status

    def get_metrics(self) -> Union[MetricsSummary, Dict[str, bool]]:
        """Get request metrics summary.

        Returns:
            Dict with metrics summary
        """
        if not self.metrics:
            return {"enabled": False}

        summary = self.metrics.get_summary()

        # Add VerticeClient status if available
        if self._vertice_coreent:
            summary["vertice_status"] = self._vertice_coreent.get_provider_status()

        return summary

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        if self.metrics:
            self.metrics = RequestMetrics()

    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate complete response (non-streaming).

        Args:
            prompt: User prompt
            context: Optional system context
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        chunks = []
        async for chunk in self.stream_chat(prompt, context, max_tokens, temperature):
            chunks.append(chunk)
        return "".join(chunks)

    async def generate_async(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_config: Optional[str] = "AUTO",
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate response with native function calling support.

        Args:
            messages: Conversation messages [{role, content}, ...]
            temperature: Sampling temperature
            max_tokens: Max output tokens
            tools: Tool schemas for native function calling
            tool_config: Function calling mode (AUTO, ANY, NONE)
            **kwargs: Additional provider-specific args

        Returns:
            Dict with 'content', 'tokens_used', and optionally 'tool_calls'
        """
        max_tokens = max_tokens or config.max_tokens
        temperature = temperature or config.temperature
        start_time = time.time()

        chunks: List[str] = []
        tool_calls: List[Dict[str, Any]] = []

        # Use VerticeClient if available
        if self._vertice_coreent:
            try:
                async for chunk in self._vertice_coreent.stream_chat(
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=tools,
                    tool_config=tool_config,
                    **kwargs,
                ):
                    # Check if chunk is a tool call JSON
                    if chunk.startswith('{"tool_call"'):
                        try:
                            import json

                            call_data = json.loads(chunk)
                            if "tool_call" in call_data:
                                tool_calls.append(call_data["tool_call"])
                        except json.JSONDecodeError:
                            chunks.append(chunk)
                    else:
                        chunks.append(chunk)

                content = "".join(chunks)
                tokens_used = len(content) // 4

                # Record success
                if self.metrics:
                    provider_name = self._vertice_coreent.current_provider or "unknown"
                    latency = time.time() - start_time
                    self.metrics.record_request(provider_name, True, latency, tokens_used)

                result: Dict[str, Any] = {
                    "content": content,
                    "tokens_used": tokens_used,
                }
                if tool_calls:
                    result["tool_calls"] = tool_calls

                return result

            except Exception as e:
                logger.warning(f"VerticeClient failed: {e}")
                if self.metrics:
                    latency = time.time() - start_time
                    self.metrics.record_request("vertice", False, latency)

        # Legacy fallback (no native function calling)
        async for chunk in self._stream_legacy(messages, max_tokens, temperature):
            chunks.append(chunk)

        content = "".join(chunks)
        return {
            "content": content,
            "tokens_used": len(content) // 4,
        }


# Singleton instance
_default_client: Optional[LLMClient] = None


def get_llm_client(
    max_retries: int = 3,
    timeout: float = 30.0,
    enable_telemetry: bool = True,
    force_new: bool = False,
) -> LLMClient:
    """Get or create default LLM client.

    Args:
        max_retries: Max retries per request
        timeout: Request timeout in seconds
        enable_telemetry: Enable request metrics
        force_new: Create new instance instead of reusing

    Returns:
        LLMClient instance
    """
    global _default_client

    if force_new:
        return LLMClient(
            max_retries=max_retries,
            timeout=timeout,
            enable_telemetry=enable_telemetry,
        )

    if _default_client is None:
        _default_client = LLMClient(
            max_retries=max_retries,
            timeout=timeout,
            enable_telemetry=enable_telemetry,
        )

    return _default_client


# Create default singleton instance for convenient import
llm_client: LLMClient = get_llm_client()

__all__ = [
    "LLMClient",
    "RequestMetrics",
    "get_llm_client",
    "llm_client",
    "CircuitBreaker",
    "CircuitState",
    "RateLimiter",
]
