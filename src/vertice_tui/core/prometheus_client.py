"""
PROMETHEUS Client for TUI - Streaming integration.

Provides the same interface as GeminiClient but routes through
PROMETHEUS for enhanced capabilities.
"""

import logging
from typing import AsyncIterator, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from vertice_cli.core.providers.prometheus_provider import PrometheusProvider, PrometheusConfig

    PROMETHEUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Prometheus provider not available: {e}")
    PROMETHEUS_AVAILABLE = False
    PrometheusProvider = None  # type: ignore
    PrometheusConfig = None  # type: ignore


@dataclass
class PrometheusStreamConfig:
    """Streaming configuration."""

    temperature: float = 1.0
    max_output_tokens: int = 8192
    enable_world_model: bool = True
    enable_memory: bool = True
    enable_reflection: bool = True
    init_timeout: float = 15.0
    stream_timeout: float = 120.0
    chunk_timeout: float = 45.0


class PrometheusClient:
    """
    PROMETHEUS Client with streaming support.

    Drop-in replacement for GeminiClient that adds:
    - World model simulation (preview actions)
    - Persistent memory (learn from interactions)
    - Self-reflection (improve over time)
    - Automatic tool creation
    """

    def __init__(
        self,
        config: Optional[PrometheusStreamConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        self.config = config or PrometheusStreamConfig()
        self._tools = tools or []
        self._provider: Optional[PrometheusProvider] = None
        self._initialized = False
        self._init_error: Optional[str] = None

        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._avg_response_time = 0.0

    async def _ensure_provider(self) -> bool:
        """Lazy initialization with error handling.

        Returns:
            True if provider is ready, False otherwise.
        """
        if self._initialized:
            return self._provider is not None

        if not PROMETHEUS_AVAILABLE or PrometheusProvider is None:
            logger.error("Prometheus module not available")
            self._init_error = "Prometheus module not installed"
            self._initialized = True  # Prevent retry loops
            return False

        try:
            logger.info("Initializing Prometheus provider...")
            prometheus_config = PrometheusConfig(
                enable_world_model=self.config.enable_world_model,
                enable_memory=self.config.enable_memory,
                enable_reflection=self.config.enable_reflection,
            )
            self._provider = PrometheusProvider(config=prometheus_config)
            self._initialized = True
            self._init_error = None
            logger.info("Prometheus provider initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus: {e}", exc_info=True)
            self._init_error = str(e)
            self._initialized = True  # Prevent retry loops
            return False

    def set_tools(self, tools: List[Dict[str, Any]]):
        """Set available tools."""
        self._tools = tools

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream response from PROMETHEUS.

        Yields chunks as they arrive, with full PROMETHEUS pipeline:
        1. Memory retrieval (relevant past experiences)
        2. World model simulation (plan before act)
        3. Execution (with tool calling)
        4. Reflection (learn from result)
        """
        start_time = datetime.now()
        self._total_requests += 1

        # Check initialization
        provider_ready = await self._ensure_provider()
        if not provider_ready:
            error_msg = self._init_error or "Unknown initialization error"
            yield f"❌ **Prometheus Error:** {error_msg}\n\n"
            yield "Falling back to standard mode. Please check logs for details.\n"
            return

        try:
            if self._provider:
                async for chunk in self._provider.stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    tools=tools or self._tools,
                ):
                    yield chunk
            else:
                yield "❌ **Prometheus Error:** Provider not available\n"
        except Exception as e:
            logger.error(f"Prometheus stream error: {e}", exc_info=True)
            yield f"\n\n❌ **Prometheus Error:** {str(e)}\n"
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            if self._total_requests > 0:
                self._avg_response_time = (
                    self._avg_response_time * (self._total_requests - 1) + elapsed
                ) / self._total_requests

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        base_status = {
            "provider": "prometheus",
            "available": PROMETHEUS_AVAILABLE,
            "initialized": self._initialized,
            "provider_ready": self._provider is not None,
            "total_requests": self._total_requests,
            "avg_response_time": round(self._avg_response_time, 3),
        }

        if self._init_error:
            base_status["init_error"] = self._init_error

        if self._initialized and self._provider:
            try:
                base_status["prometheus_status"] = self._provider.get_status()
            except Exception as e:
                base_status["status_error"] = str(e)

        return base_status

    async def evolve(self, iterations: int = 5) -> Dict[str, Any]:
        """Run evolution cycle."""
        provider_ready = await self._ensure_provider()
        if not provider_ready:
            return {"error": self._init_error or "Provider not initialized"}
        if self._provider:
            try:
                return await self._provider.evolve(iterations)
            except Exception as e:
                logger.error(f"Evolution cycle failed: {e}", exc_info=True)
                return {"error": str(e)}
        return {"error": "Provider not available"}
