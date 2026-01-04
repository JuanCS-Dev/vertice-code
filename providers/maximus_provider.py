"""
MAXIMUS Provider - Integration with MAXIMUS 2.0 Backend.

Connects Prometheus CLI to MAXIMUS backend services via MCP/HTTP:
- Tribunal: Governance evaluation
- Memory: Episodic memory with MIRIX 6-types
- Factory: Dynamic tool generation

Based on 2025 best practices:
- MCP (Model Context Protocol) as primary transport
- HTTP fallback for compatibility
- Tenacity retry with exponential backoff
- Circuit breaker for fail-fast resilience

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, cast

import httpx

from .maximus_config import MaximusConfig
from .maximus_helpers import (
    build_enhanced_prompt,
    format_execution_log,
    format_interaction_for_memory,
)
from .resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    call_with_resilience,
    create_http_client,
)


class MaximusProvider:
    """MAXIMUS 2.0 Backend Provider with resilience.

    Implements the same interface as PrometheusProvider but routes
    to MAXIMUS backend services with:

    - Tribunal: Three-judge governance (VERITAS, SOPHIA, DIKE)
    - Memory: 6-type MIRIX episodic memory
    - Factory: Dynamic tool generation with sandbox
    - Resilience: Retry + Circuit breaker for production reliability
    """

    def __init__(self, config: Optional[MaximusConfig] = None) -> None:
        """Initialize MAXIMUS provider.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or MaximusConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._health_status: Dict[str, Any] = {}

        # Resilience components
        self._breaker = CircuitBreaker(self.config.circuit_breaker)
        self._mcp_available = False

    async def _ensure_initialized(self) -> None:
        """Lazy initialization of HTTP client with connection pooling."""
        if not self._initialized:
            self._client = create_http_client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                pool_config=self.config.pool,
            )
            self._initialized = True
            await self._check_health()

    async def _check_health(self) -> Dict[str, Any]:
        """Check MAXIMUS health status."""
        if not self._client:
            return {"status": "not_initialized"}

        try:
            response = await self._client.get("/health")
            self._health_status = response.json()
            self._mcp_available = self._health_status.get("mcp_enabled", False)
            return self._health_status
        except httpx.HTTPError as e:
            self._health_status = {"status": "error", "error": str(e)}
            return self._health_status

    def is_available(self) -> bool:
        """Check if MAXIMUS is available."""
        return (
            self._initialized
            and self._health_status.get("status") in ("ok", "healthy")
            and not self._breaker.is_open()
        )

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with resilience.

        Uses circuit breaker and retry logic for reliability.

        Args:
            method: HTTP method.
            path: Request path.
            json: JSON body.
            params: Query parameters.

        Returns:
            Response JSON.

        Raises:
            CircuitBreakerOpen: If circuit is open.
        """
        await self._ensure_initialized()
        if not self._client:
            return {"error": "Client not initialized"}

        async def _do_request() -> Dict[str, Any]:
            """Execute HTTP request and return JSON response."""
            if self._client is None:
                return {"error": "Client not initialized"}
            response = await self._client.request(
                method, path, json=json, params=params
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

        try:
            return await call_with_resilience(
                _do_request,
                self._breaker,
                self.config.retry,
            )
        except CircuitBreakerOpen:
            return {"error": "Service unavailable (circuit open)"}
        except httpx.HTTPError as e:
            return {"error": str(e)}

    # =========================================================================
    # TRIBUNAL INTEGRATION
    # =========================================================================

    async def tribunal_evaluate(
        self,
        execution_log: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate execution in Tribunal with resilience."""
        payload: Dict[str, Any] = {"execution_log": execution_log}
        if context:
            payload["context"] = context

        result = await self._request("POST", "/v1/tribunal/evaluate", json=payload)
        if "error" in result:
            result["decision"] = "ERROR"
        return result

    async def tribunal_health(self) -> Dict[str, Any]:
        """Check Tribunal health with resilience."""
        return await self._request("GET", "/v1/tribunal/health")

    async def tribunal_stats(self) -> Dict[str, Any]:
        """Get Tribunal statistics with resilience."""
        return await self._request("GET", "/v1/tribunal/stats")

    # =========================================================================
    # MEMORY INTEGRATION
    # =========================================================================

    async def memory_store(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Store memory in episodic system with resilience."""
        payload = {
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags or [],
        }
        return await self._request("POST", "/v1/memories", json=payload)

    async def memory_search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories with resilience."""
        params: Dict[str, Any] = {"query": query, "limit": limit}
        if memory_type:
            params["memory_type"] = memory_type

        result = await self._request("GET", "/v1/memories/search", params=params)
        return cast(List[Dict[str, Any]], result.get("memories", []))

    async def memory_context(self, task: str) -> Dict[str, Any]:
        """Get memory context for a task with resilience."""
        return await self._request("POST", "/v1/memories/context", json={"task": task})

    async def memory_consolidate(self, threshold: float = 0.8) -> Dict[str, int]:
        """Consolidate high-importance memories to vault with resilience."""
        result = await self._request(
            "POST", "/v1/memories/consolidate", json={"threshold": threshold}
        )
        if isinstance(result, dict) and "error" not in result:
            return result
        return {}

    # =========================================================================
    # FACTORY INTEGRATION
    # =========================================================================

    async def factory_generate(
        self,
        name: str,
        description: str,
        examples: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a new tool dynamically with resilience."""
        payload = {"name": name, "description": description, "examples": examples}
        return await self._request("POST", "/v1/tools/generate", json=payload)

    async def factory_execute(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a generated tool with resilience."""
        return await self._request(
            "POST", f"/v1/tools/{tool_name}/execute", json=params
        )

    async def factory_list(self) -> List[Dict[str, Any]]:
        """List available generated tools with resilience."""
        result = await self._request("GET", "/v1/tools")
        return cast(List[Dict[str, Any]], result.get("tools", []))

    async def factory_delete(self, tool_name: str) -> bool:
        """Delete a generated tool with resilience."""
        result = await self._request("DELETE", f"/v1/tools/{tool_name}")
        return bool(result.get("success", False))

    # =========================================================================
    # STREAMING INTEGRATION
    # =========================================================================

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        use_tribunal: bool = True,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """Stream response with MAXIMUS pipeline.

        Pipeline:
        1. Memory context retrieval
        2. LLM generation (Gemini via MAXIMUS)
        3. Tribunal evaluation (background)
        4. Memory storage (background)
        """
        await self._ensure_initialized()
        if not self._client:
            yield "Error: MAXIMUS not initialized"
            return

        if self._breaker.is_open():
            yield "Error: MAXIMUS service unavailable (circuit open)"
            return

        # 1. Get memory context
        memory_ctx: Dict[str, Any] = {}
        if use_memory and self.config.enable_memory:
            memory_ctx = await self.memory_context(prompt)

        # 2. Build enhanced prompt
        enhanced_prompt = build_enhanced_prompt(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            memory_context=memory_ctx,
        )

        # 3. Stream via MAXIMUS
        full_response = ""
        try:
            async with self._client.stream(
                "POST",
                "/v1/chat/stream",
                json={"prompt": enhanced_prompt, "tools": tools or []},
                timeout=httpx.Timeout(120.0, connect=10.0),
            ) as response:
                async for chunk in response.aiter_text():
                    full_response += chunk
                    yield chunk
            self._breaker.record_success()
        except httpx.HTTPError as e:
            self._breaker.record_failure()
            yield f"\n[MAXIMUS Error: {e}]"
            return

        # 4. Background tasks (tribunal + memory)
        if use_tribunal and self.config.enable_tribunal:
            asyncio.create_task(self._evaluate_in_tribunal(prompt, full_response))
        if use_memory and self.config.enable_memory:
            asyncio.create_task(self._store_interaction(prompt, full_response))

    async def _evaluate_in_tribunal(self, prompt: str, response: str) -> None:
        """Evaluate interaction in Tribunal (background)."""
        try:
            execution_log = format_execution_log(prompt, response)
            await self.tribunal_evaluate(execution_log)
        except (httpx.HTTPError, asyncio.CancelledError, asyncio.TimeoutError):
            pass

    async def _store_interaction(self, prompt: str, response: str) -> None:
        """Store interaction in memory (background)."""
        try:
            content = format_interaction_for_memory(prompt, response)
            await self.memory_store(content=content, memory_type="episodic")
        except (httpx.HTTPError, asyncio.CancelledError, asyncio.TimeoutError):
            pass

    # =========================================================================
    # STATUS AND HEALTH
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get MAXIMUS status with resilience info."""
        return {
            "initialized": self._initialized,
            "health": self._health_status,
            "mcp_available": self._mcp_available,
            "circuit_breaker": self._breaker.get_stats(),
            "config": {
                "base_url": self.config.base_url,
                "transport_mode": self.config.transport_mode.value,
                "tribunal_enabled": self.config.enable_tribunal,
                "memory_enabled": self.config.enable_memory,
                "factory_enabled": self.config.enable_factory,
            },
        }
