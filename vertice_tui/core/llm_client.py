"""
LLM Client Module - Gemini API Integration
==========================================

Simplified facade after SCALE & SUSTAIN refactoring (Nov 2025).

Components extracted to dedicated modules:
- CircuitBreaker: vertice_tui/core/resilience/circuit_breaker.py
- ToolCallParser: vertice_tui/core/parsing/tool_call_parser.py
- Streaming: vertice_tui/core/streaming/gemini_stream.py

This module provides:
- GeminiClient: Main client with function calling support
- Re-exports for backward compatibility

VERTEX AI INTEGRATION (Dec 2025):
- When GOOGLE_CLOUD_PROJECT is set, uses Vertex AI (enterprise quota)
- Falls back to direct Gemini API only when Vertex AI unavailable
- Like GPT via Azure, Gemini via Vertex AI avoids consumer API limits
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future type hints if needed

# Import from canonical resilience module
from core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitBreakerStats,
    CircuitState,
)
from vertice_tui.core.parsing.tool_call_parser import (
    ToolCallParser,
    KNOWN_TOOLS,
)
from vertice_tui.core.schema_adapter import SchemaAdapter
from vertice_tui.core.streaming.gemini import (
    GeminiStreamConfig,
    GeminiStreamer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# GEMINI CLIENT
# =============================================================================


class GeminiClient:
    """
    Optimized Gemini API client with streaming support.

    Best Practices (Nov 2025):
    - Temperature 1.0 for Gemini 3.x (optimized setting)
    - Streaming for UI responsiveness
    - System instructions for consistent behavior
    - Exponential backoff with jitter for rate limits
    - Circuit Breaker for fault tolerance

    Attributes:
        api_key: Gemini API key
        model_name: Model identifier
        temperature: Generation temperature
        max_output_tokens: Maximum response length

    Example:
        client = GeminiClient(api_key="...", model="gemini-2.0-flash")
        async for chunk in client.stream("Hello!"):
            print(chunk, end="")
    """

    # Timeout configuration
    INIT_TIMEOUT: float = 10.0
    STREAM_TIMEOUT: float = 60.0
    CHUNK_TIMEOUT: float = 30.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_output_tokens: int = 8192,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: API key (defaults to GEMINI_API_KEY or GOOGLE_API_KEY env var)
            model: Model name (defaults to GEMINI_MODEL env var or gemini-2.0-flash)
            temperature: Generation temperature (0-2, default 1.0)
            max_output_tokens: Maximum response tokens (default 8192)
            circuit_breaker_config: Optional circuit breaker configuration

        Note:
            When GOOGLE_CLOUD_PROJECT is set, uses Vertex AI (enterprise quota).
            Falls back to direct Gemini API only when Vertex AI unavailable.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-pro"
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        # Multi-provider integration (Dec 2025)
        # VerticeClient handles all providers with FREE FIRST priority
        self._vertice_client: Optional[Any] = None
        self._use_multi_provider = False
        self._init_multi_provider()

        # Streaming configuration (fallback to direct API)
        self._stream_config = GeminiStreamConfig(
            model_name=self.model_name,
            api_key=self.api_key or "",
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            init_timeout=self.INIT_TIMEOUT,
            stream_timeout=self.STREAM_TIMEOUT,
            chunk_timeout=self.CHUNK_TIMEOUT,
        )
        self._streamer: Optional[GeminiStreamer] = None
        self._initialized = False

        # Function calling support
        self._tool_schemas: List[Dict[str, Any]] = []
        self._gemini_tools = None

        # Circuit Breaker for resilience
        self._circuit_breaker = CircuitBreaker(
            name="gemini_api",
            config=circuit_breaker_config
            or CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=30.0,
            ),
        )

    def _init_multi_provider(self) -> None:
        """Initialize VerticeClient for unified multi-provider routing.

        Priority order (handled by VerticeClient):
        1. Groq, Cerebras, Mistral (FREE FIRST)
        2. Gemini, Vertex AI, Azure (Enterprise)
        3. Direct Gemini API (Fallback)
        """
        # Try VerticeClient (unified router)
        try:
            from vertice_core.clients import get_client

            self._vertice_client = get_client()
            available = self._vertice_client.get_available_providers()

            if available:
                self._use_multi_provider = True
                logger.info(
                    f"✅ VerticeClient enabled: {len(available)} providers "
                    f"({', '.join(available[:3])}{'...' if len(available) > 3 else ''})"
                )
                return

        except ImportError:
            logger.debug("VerticeClient not available")
        except Exception as e:
            logger.debug(f"VerticeClient init failed: {e}")

        self._vertice_client = None
        logger.debug("Using direct Gemini API (VerticeClient unavailable)")

    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers.

        Returns:
            List of provider names (groq, cerebras, vertex-ai, etc.)
        """
        if self._vertice_client:
            return self._vertice_client.get_available_providers()
        elif self.api_key:
            return ["gemini"]
        return []

    def get_provider_status(self) -> str:
        """Get status report of all providers.

        Returns:
            Human-readable status report
        """
        if self._vertice_client:
            status = self._vertice_client.get_provider_status()
            current = status.get("current_provider", "none")
            providers = status.get("providers", {})
            available = [k for k, v in providers.items() if v.get("available")]
            return f"VerticeClient: {current} ({len(available)} available)"
        elif self.api_key:
            return "Gemini Direct API: ✅ Active"
        return "No providers available"

    def get_current_provider_name(self) -> str:
        """Get the name of the current/primary provider.

        Returns:
            Provider name (e.g., 'groq', 'cerebras', 'vertex-ai', 'gemini')
        """
        if self._vertice_client:
            available = self._vertice_client.get_available_providers()
            current = self._vertice_client.current_provider
            if current:
                return current
            if available:
                return available[0]
            return "vertice"
        elif self.api_key:
            return "gemini"
        return "none"

    def set_provider(self, name: str) -> bool:
        """Set the preferred provider.

        Args:
            name: Provider name to prioritize

        Returns:
            True if provider was set, False otherwise
        """
        if self._vertice_client:
            success = self._vertice_client.set_preferred_provider(name)
            if success:
                logger.info(f"Switched provider to: {name}")
            return success
        return False

    def set_tools(self, schemas: List[Dict[str, Any]]) -> None:
        """
        Configure tools for function calling.

        Args:
            schemas: List of tool schemas with name, description, parameters
        """
        self._tool_schemas = schemas
        self._gemini_tools = None  # Reset to force rebuild

    def _build_gemini_tools(self) -> Optional[List[Any]]:
        """Convert tool schemas to Gemini Tool objects."""
        if not self._tool_schemas:
            return None

        try:
            from google.generativeai.types import (
                FunctionDeclaration,
                Tool as GeminiTool,
            )

            declarations = []
            for schema in self._tool_schemas:
                try:
                    # Use SchemaAdapter to transform and validate
                    gemini_schema = SchemaAdapter.to_gemini_schema(schema)

                    declarations.append(
                        FunctionDeclaration(
                            name=gemini_schema["name"],
                            description=gemini_schema["description"],
                            parameters=gemini_schema["parameters"],
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to adapt schema for {schema.get('name')}: {e}")
                    # Continue to try other tools, or raise if strict
                    continue

            if not declarations:
                logger.warning("No valid tool declarations built")
                return None

            self._gemini_tools = [GeminiTool(function_declarations=declarations)]
            return self._gemini_tools

        except ImportError:
            logger.warning("google-generativeai not available for function calling")
            return None
        except Exception as e:
            import traceback

            traceback.print_exc()
            logger.error(f"Failed to build Gemini tools: {e}")
            return None

    async def _ensure_initialized(self) -> bool:
        """Lazy initialization of streamer with timeout."""
        if self._initialized and self._streamer:
            return True

        if not self.api_key:
            logger.error("No API key configured")
            return False

        try:
            self._streamer = GeminiStreamer(self._stream_config)
            result = await asyncio.wait_for(self._streamer.initialize(), timeout=self.INIT_TIMEOUT)
            self._initialized = result
            return result

        except asyncio.TimeoutError:
            await self._circuit_breaker.record_failure("Initialization timeout")
            return False
        except Exception as e:
            await self._circuit_breaker.record_failure(f"Init error: {str(e)}")
            return False

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream response using intelligent multi-provider routing.

        Priority:
        1. VerticeRouter (Groq, Cerebras, Mistral, etc.) - FREE FIRST
        2. Vertex AI - Enterprise quota
        3. Direct Gemini API - Fallback

        Args:
            prompt: User's message
            system_prompt: System instructions
            context: Optional conversation history
            tools: Optional tool schemas to use for this request
            **kwargs: Extra arguments (for compatibility)

        Yields:
            Text chunks for UI rendering
        """
        # Check circuit breaker first
        if not await self._circuit_breaker.can_execute():
            retry_after = self._circuit_breaker.retry_after
            yield f"⚡ Service temporarily unavailable. Retry in {retry_after:.0f}s"
            return

        # Route 1: Use VerticeClient if available (unified multi-provider)
        if self._vertice_client:
            async for chunk in self._stream_via_client(prompt, system_prompt, context):
                yield chunk
            return

        # Route 2: Direct Gemini API (fallback when VerticeClient unavailable)
        async for chunk in self._stream_via_gemini(prompt, system_prompt, context, tools):
            yield chunk

    async def _stream_via_client(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[List[Dict[str, str]]],
    ) -> AsyncIterator[str]:
        """Stream via VerticeClient with automatic provider fallback."""
        try:
            # Build messages in OpenAI format
            messages = []
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": prompt})

            # Stream via VerticeClient (handles all fallback logic)
            async for chunk in self._vertice_client.stream_chat(
                messages,
                system_prompt=system_prompt,
            ):
                yield chunk

            await self._circuit_breaker.record_success()

        except Exception as e:
            await self._circuit_breaker.record_failure(str(e))
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                yield "\n⚠️ Rate limit reached on all providers. Please wait."
            elif "AllProvidersExhausted" in error_msg:
                yield "\n⚠️ All providers exhausted. Check API keys."
            else:
                yield f"\n❌ Client error: {error_msg[:200]}"

    async def _stream_via_gemini(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]],
    ) -> AsyncIterator[str]:
        """Stream via direct Gemini API (fallback)."""
        if not await self._ensure_initialized():
            yield "❌ Gemini not configured. Set GEMINI_API_KEY environment variable."
            return

        # Build tools for function calling
        if tools:
            self._tool_schemas = tools
            self._gemini_tools = None
        gemini_tools = self._build_gemini_tools() if self._tool_schemas else None

        if gemini_tools:
            logger.info(f"Function calling enabled with {len(self._tool_schemas)} tools")

        try:
            async for chunk in self._streamer.stream(prompt, system_prompt, context, gemini_tools):
                yield chunk

            await self._circuit_breaker.record_success()

        except asyncio.TimeoutError:
            await self._circuit_breaker.record_failure("Stream timeout")
            yield f"\n⚠️ Request timed out after {self.STREAM_TIMEOUT}s"
        except Exception as e:
            error_str = str(e)
            await self._circuit_breaker.record_failure(error_str)
            # Handle rate limiting gracefully
            if "429" in error_str or "quota" in error_str.lower():
                yield "\n⚠️ Rate limit reached. Please wait a moment and try again."
            elif "RepeatedComposite" in error_str or "serializable" in error_str.lower():
                yield "\n⚠️ Response parsing error. Retrying..."
            else:
                yield f"\n❌ Error: {error_str[:200]}"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """
        Generate complete response (non-streaming).

        Args:
            prompt: User's message
            system_prompt: System instructions
            **kwargs: Additional parameters (temperature, etc) passed to stream()

        Returns:
            Complete response text
        """
        chunks = []
        async for chunk in self.stream(prompt, system_prompt, **kwargs):
            chunks.append(chunk)
        return "".join(chunks)

    @property
    def is_available(self) -> bool:
        """Check if any provider is configured."""
        if self._vertice_client:
            return bool(self._vertice_client.get_available_providers())
        return bool(self.api_key)

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Access circuit breaker for external monitoring."""
        return self._circuit_breaker

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status for observability.

        Returns:
            Dict with health metrics and circuit breaker status
        """
        cb_status = self._circuit_breaker.get_status()
        return {
            "service": "gemini_api",
            "healthy": self._circuit_breaker.is_closed and self.is_available,
            "available": self.is_available,
            "initialized": self._initialized,
            "model": self.model_name,
            "circuit_breaker": cb_status,
            "config": {
                "init_timeout": self.INIT_TIMEOUT,
                "stream_timeout": self.STREAM_TIMEOUT,
                "chunk_timeout": self.CHUNK_TIMEOUT,
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            },
        }

    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker (for recovery)."""
        self._circuit_breaker.reset()


# =============================================================================
# EXPORTS (Backward Compatibility)
# =============================================================================

__all__ = [
    # Main client
    "GeminiClient",
    # Parsing (re-exported from parsing module)
    "ToolCallParser",
    "KNOWN_TOOLS",
    # Circuit Breaker (re-exported from resilience module)
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitBreakerStats",
    "CircuitState",
    # Streaming config (re-exported from streaming module)
    "GeminiStreamConfig",
]
