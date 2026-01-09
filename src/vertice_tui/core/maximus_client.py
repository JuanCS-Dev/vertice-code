"""
MAXIMUS Client for TUI - Streaming integration with MAXIMUS 2.0 Backend.

Provides the same interface as GeminiClient/PrometheusClient but routes
through MAXIMUS for governance, memory, and tool factory capabilities.
"""

from __future__ import annotations

from typing import AsyncIterator, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from vertice_cli.core.providers.maximus_provider import MaximusProvider, MaximusConfig


@dataclass
class MaximusStreamConfig:
    """Streaming configuration for MAXIMUS client."""

    temperature: float = 1.0
    max_output_tokens: int = 8192
    enable_tribunal: bool = True
    enable_memory: bool = True
    enable_factory: bool = True
    init_timeout: float = 15.0
    stream_timeout: float = 120.0
    chunk_timeout: float = 45.0


class MaximusClient:
    """
    MAXIMUS Client with streaming support.

    Drop-in replacement for GeminiClient/PrometheusClient that adds:
    - Tribunal governance (three-judge evaluation)
    - 6-type MIRIX episodic memory
    - Dynamic tool factory with sandbox
    - Constitutional compliance checking
    """

    def __init__(
        self,
        config: Optional[MaximusStreamConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize MAXIMUS client.

        Args:
            config: Optional streaming configuration.
            tools: Optional list of available tools.
        """
        self.config = config or MaximusStreamConfig()
        self._tools = tools or []
        self._provider: Optional[MaximusProvider] = None
        self._initialized = False

        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._avg_response_time = 0.0
        self._tribunal_verdicts: List[Dict[str, Any]] = []

    async def _ensure_provider(self) -> None:
        """Lazy initialization of MAXIMUS provider."""
        if not self._initialized:
            maximus_config = MaximusConfig(
                enable_tribunal=self.config.enable_tribunal,
                enable_memory=self.config.enable_memory,
                enable_factory=self.config.enable_factory,
            )
            self._provider = MaximusProvider(config=maximus_config)
            await self._provider._ensure_initialized()
            self._initialized = True

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Set available tools.

        Args:
            tools: List of tool definitions.
        """
        self._tools = tools

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Stream response from MAXIMUS.

        Yields chunks as they arrive, with full MAXIMUS pipeline:
        1. Memory retrieval (relevant past experiences)
        2. Tribunal pre-check (risk assessment)
        3. Execution (with tool calling)
        4. Tribunal post-check (governance evaluation)
        5. Memory storage (learn from interaction)

        Args:
            prompt: User prompt.
            system_prompt: Optional system instructions.
            context: Conversation history.
            tools: Available tools (uses default if not provided).

        Yields:
            Response text chunks.
        """
        await self._ensure_provider()

        start_time = datetime.now()
        self._total_requests += 1

        try:
            if self._provider:
                async for chunk in self._provider.stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    tools=tools or self._tools,
                    use_tribunal=self.config.enable_tribunal,
                    use_memory=self.config.enable_memory,
                ):
                    yield chunk
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            if self._total_requests > 0:
                self._avg_response_time = (
                    self._avg_response_time * (self._total_requests - 1) + elapsed
                ) / self._total_requests

    # =========================================================================
    # TRIBUNAL OPERATIONS
    # =========================================================================

    async def evaluate_in_tribunal(
        self,
        execution_log: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate execution in Tribunal.

        Args:
            execution_log: Log to evaluate.
            context: Optional context.

        Returns:
            Tribunal verdict with decision and scores.
        """
        await self._ensure_provider()
        if self._provider:
            verdict = await self._provider.tribunal_evaluate(execution_log, context)
            self._tribunal_verdicts.append(verdict)
            return verdict
        return {"error": "Provider not initialized"}

    async def get_tribunal_health(self) -> Dict[str, Any]:
        """Get Tribunal health status.

        Returns:
            Health status dict.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.tribunal_health()
        return {"status": "not_initialized"}

    async def get_tribunal_stats(self) -> Dict[str, Any]:
        """Get Tribunal statistics.

        Returns:
            Statistics about evaluations.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.tribunal_stats()
        return {}

    # =========================================================================
    # MEMORY OPERATIONS
    # =========================================================================

    async def store_memory(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Store memory.

        Args:
            content: Memory content.
            memory_type: Type (core, episodic, semantic, procedural, resource, vault).
            importance: Importance score (0.0-1.0).
            tags: Optional tags.

        Returns:
            Stored memory with ID.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.memory_store(
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags,
            )
        return {"error": "Provider not initialized"}

    async def search_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories.

        Args:
            query: Search query.
            memory_type: Optional type filter.
            limit: Max results.

        Returns:
            List of matching memories.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.memory_search(
                query=query,
                memory_type=memory_type,
                limit=limit,
            )
        return []

    async def get_memory_context(self, task: str) -> Dict[str, Any]:
        """Get memory context for a task.

        Args:
            task: Task description.

        Returns:
            Context with memories from all 6 types.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.memory_context(task)
        return {}

    async def consolidate_memories(
        self,
        threshold: float = 0.8,
    ) -> Dict[str, int]:
        """Consolidate high-importance memories to vault.

        Args:
            threshold: Minimum importance.

        Returns:
            Count by original type.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.memory_consolidate(threshold)
        return {}

    # =========================================================================
    # FACTORY OPERATIONS
    # =========================================================================

    async def generate_tool(
        self,
        name: str,
        description: str,
        examples: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a new tool dynamically.

        Args:
            name: Tool name.
            description: Tool description.
            examples: Input/output examples.

        Returns:
            Generated tool spec.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.factory_generate(
                name=name,
                description=description,
                examples=examples,
            )
        return {"error": "Provider not initialized"}

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a generated tool.

        Args:
            tool_name: Tool to execute.
            params: Tool parameters.

        Returns:
            Execution result.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.factory_execute(tool_name, params)
        return {"error": "Provider not initialized"}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available generated tools.

        Returns:
            List of tool specs.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.factory_list()
        return []

    async def delete_tool(self, tool_name: str) -> bool:
        """Delete a generated tool.

        Args:
            tool_name: Tool to delete.

        Returns:
            True if deleted.
        """
        await self._ensure_provider()
        if self._provider:
            return await self._provider.factory_delete(tool_name)
        return False

    # =========================================================================
    # STATUS AND HEALTH
    # =========================================================================

    def get_health_status(self) -> Dict[str, Any]:
        """Get client health status.

        Returns:
            Health status with metrics.
        """
        base_status = {
            "provider": "maximus",
            "initialized": self._initialized,
            "total_requests": self._total_requests,
            "avg_response_time": self._avg_response_time,
            "tribunal_verdicts": len(self._tribunal_verdicts),
        }

        if self._initialized and self._provider:
            base_status["maximus_status"] = self._provider.get_status()

        return base_status

    async def close(self) -> None:
        """Close client and release resources."""
        if self._provider:
            await self._provider.close()
            self._provider = None
            self._initialized = False
