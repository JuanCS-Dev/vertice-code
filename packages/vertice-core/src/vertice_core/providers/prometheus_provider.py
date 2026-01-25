"""
PROMETHEUS Provider - LLM Provider wrapping PrometheusOrchestrator.

Integra o PROMETHEUS como provider de LLM no ecossistema vertice_core,
permitindo uso transparente em Shell CLI, MCP e Gradio UI.
"""

import os
import sys
import logging
from typing import AsyncIterator, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Ensure the project root is in sys.path to import prometheus
# This avoids circular imports by ensuring we can find 'prometheus' even if the package is partially loaded
root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


@dataclass
class PrometheusConfig:
    """Configuration for PROMETHEUS provider."""

    enable_world_model: bool = True
    enable_memory: bool = True
    enable_reflection: bool = True
    enable_evolution: bool = False  # Expensive, enable manually
    evolution_iterations: int = 5
    memory_consolidation_interval: int = 10


class PrometheusProvider:
    """
    PROMETHEUS as LLM Provider.

    Implements the same interface as GeminiProvider/OllamaProvider
    but routes through PrometheusOrchestrator for enhanced capabilities.
    """

    def __init__(self, config: Optional[PrometheusConfig] = None, api_key: Optional[str] = None):
        self.config = config or PrometheusConfig()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._agent: Optional[Any] = None
        self._orchestrator: Optional[Any] = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazy initialization of PROMETHEUS."""
        if not self._initialized:
            try:
                # Local import to avoid circular dependencies during module loading
                from prometheus.main import PrometheusAgent

                self._agent = PrometheusAgent(api_key=self.api_key)
                # Initialize the agent (creates orchestrator internally)
                await self._agent._ensure_initialized()

                # Get orchestrator reference
                self._orchestrator = self._agent._orchestrator
                self._initialized = True
                logger.info("PROMETHEUS provider initialized successfully.")
            except ImportError as e:
                logger.error(f"Failed to import PROMETHEUS: {e}")
                # We don't print a warning anymore to avoid cluttering, but log the error
                raise RuntimeError(f"PROMETHEUS module not found or circular import: {e}")

    def is_available(self) -> bool:
        """Check if PROMETHEUS is available."""
        return bool(self.api_key)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream response from PROMETHEUS."""
        await self._ensure_initialized()

        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, system_prompt, context)

        # Stream through PROMETHEUS orchestrator
        if self._orchestrator and hasattr(self._orchestrator, "execute"):
            async for chunk in self._orchestrator.execute(full_prompt, stream=True):
                yield chunk
        else:
            yield "Error: Prometheus Orchestrator not initialized or missing execute method."

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        """Non-streaming generation."""
        chunks = []
        async for chunk in self.stream(prompt, system_prompt, context, **kwargs):
            chunks.append(chunk)
        return "".join(chunks)

    def _build_prompt(
        self, prompt: str, system_prompt: Optional[str], context: Optional[List[Dict[str, str]]]
    ) -> str:
        """Build full prompt with context."""
        parts = []

        if system_prompt:
            parts.append(f"[SYSTEM]\n{system_prompt}\n")

        if context:
            parts.append("[CONVERSATION HISTORY]")
            for msg in context[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"{role.upper()}: {content}")
            parts.append("")

        # Inject local file content if referenced
        prompt = self._inject_local_files(prompt)

        parts.append(f"[CURRENT REQUEST]\n{prompt}")

        return "\n".join(parts)

    def _inject_local_files(self, prompt: str) -> str:
        """Detect file paths in prompt and inject content."""
        import re

        # Regex for common file paths
        path_pattern = r"(?<!\w)(?:\./|/|\w+/)[a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+"

        matches = re.finditer(path_pattern, prompt)
        injections = []

        for match in matches:
            path_str = match.group(0)
            try:
                # Validate path
                path = os.path.abspath(os.path.expanduser(path_str))
                if os.path.exists(path) and os.path.isfile(path):
                    # Size check (max 50KB)
                    if os.path.getsize(path) < 50 * 1024:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            injections.append(
                                f"\n[FILE_CONTENT: {path_str}]\n```\n{content}\n```\n"
                            )
            except (FileNotFoundError, PermissionError, IOError, OSError):
                pass

        if injections:
            return prompt + "\n" + "".join(injections)

        return prompt

    async def evolve(self, iterations: int = 5) -> Dict[str, Any]:
        """Run evolution cycle to improve capabilities."""
        await self._ensure_initialized()
        if self._orchestrator and hasattr(self._orchestrator, "evolve_capabilities"):
            return await self._orchestrator.evolve_capabilities(iterations)
        return {"error": "Evolution capability not available"}

    def get_status(self) -> Dict[str, Any]:
        """Get PROMETHEUS system status."""
        if not self._initialized:
            return {"status": "not_initialized"}
        if self._orchestrator and hasattr(self._orchestrator, "get_status"):
            return self._orchestrator.get_status()
        return {"status": "initialized", "details": "Orchestrator status unavailable"}

    def get_memory_context(self, task: str) -> Dict[str, Any]:
        """Get memory context for a task."""
        if not self._initialized:
            return {}
        if (
            self._orchestrator
            and hasattr(self._orchestrator, "memory")
            and hasattr(self._orchestrator.memory, "get_context_for_task")
        ):
            return self._orchestrator.memory.get_context_for_task(task)
        return {}
