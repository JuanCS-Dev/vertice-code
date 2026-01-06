"""
Prometheus MCP Adapter - Expose Prometheus tools via MCP protocol.

This adapter allows other agents to use Prometheus capabilities through MCP:
- prometheus_execute: Execute task via PROMETHEUS
- prometheus_memory_query: Query PROMETHEUS memory
- prometheus_simulate: Simulate action via world model
- prometheus_evolve: Run evolution cycle
- prometheus_reflect: Trigger reflection
- prometheus_create_tool: Generate new tool dynamically
- prometheus_get_status: Get full system status
- prometheus_benchmark: Run benchmark suite
"""

import logging
from typing import Optional
from vertice_cli.integrations.mcp.shell_handler import ShellManager
from vertice_cli.core.providers import PrometheusProvider

logger = logging.getLogger(__name__)


class PrometheusMCPAdapter:
    """Adapter to expose Prometheus tools as MCP tools."""

    def __init__(
        self,
        prometheus_provider: Optional[PrometheusProvider] = None,
        shell_manager: Optional[ShellManager] = None,
    ):
        self.provider = prometheus_provider
        self.shell_manager = shell_manager or ShellManager()
        self._mcp_tools = {}

    def set_provider(self, provider: PrometheusProvider):
        """Set Prometheus provider (for lazy initialization)."""
        self.provider = provider

    def register_all(self, mcp_server):
        """Register all Prometheus tools as MCP tools."""
        if not self.provider:
            logger.warning("Prometheus provider not set, skipping MCP registration")
            return

        self._register_prometheus_tools(mcp_server)
        logger.info(f"Registered {len(self._mcp_tools)} Prometheus MCP tools")

    def _register_prometheus_tools(self, mcp_server):
        """Register Prometheus-specific tools."""

        @mcp_server.tool(name="prometheus_execute")
        async def prometheus_execute(
            task: str, use_world_model: bool = True, use_memory: bool = True
        ) -> dict:
            """Execute task via PROMETHEUS self-evolving meta-agent."""
            try:
                # Configure provider
                self.provider.config.enable_world_model = use_world_model
                self.provider.config.enable_memory = use_memory

                result = await self.provider.generate(task)
                return {
                    "success": True,
                    "tool": "prometheus_execute",
                    "result": result,
                    "world_model_used": use_world_model,
                    "memory_used": use_memory,
                }
            except Exception as e:
                logger.error(f"Prometheus execute error: {e}")
                return {"success": False, "tool": "prometheus_execute", "error": str(e)}

        @mcp_server.tool(name="prometheus_memory_query")
        async def prometheus_memory_query(query: str, memory_type: str = "all") -> dict:
            """Query PROMETHEUS 6-type persistent memory system (MIRIX)."""
            try:
                # Use get_memory_context for queries
                context = self.provider.get_memory_context(query)
                return {
                    "success": True,
                    "tool": "prometheus_memory_query",
                    "query": query,
                    "memory_type": memory_type,
                    "result": context,
                }
            except Exception as e:
                logger.error(f"Prometheus memory query error: {e}")
                return {"success": False, "tool": "prometheus_memory_query", "error": str(e)}

        @mcp_server.tool(name="prometheus_simulate")
        async def prometheus_simulate(action_plan: str) -> dict:
            """Simulate action via World Model (SimuRA) without executing it."""
            try:
                await self.provider._ensure_initialized()
                if (
                    self.provider._orchestrator
                    and hasattr(self.provider._orchestrator, "world_model")
                    and hasattr(self.provider._orchestrator.world_model, "simulate")
                ):
                    simulation = await self.provider._orchestrator.world_model.simulate(action_plan)
                    return {
                        "success": True,
                        "tool": "prometheus_simulate",
                        "action_plan": action_plan,
                        "simulation": simulation,
                    }
                else:
                    return {
                        "success": False,
                        "tool": "prometheus_simulate",
                        "error": "World Model simulation not available",
                    }
            except Exception as e:
                logger.error(f"Prometheus simulate error: {e}")
                return {"success": False, "tool": "prometheus_simulate", "error": str(e)}

        @mcp_server.tool(name="prometheus_evolve")
        async def prometheus_evolve(iterations: int = 5) -> dict:
            """Run self-evolution cycle (Agent0) to improve capabilities."""
            try:
                result = await self.provider.evolve(iterations)
                return {
                    "success": True,
                    "tool": "prometheus_evolve",
                    "iterations": iterations,
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Prometheus evolve error: {e}")
                return {"success": False, "tool": "prometheus_evolve", "error": str(e)}

        @mcp_server.tool(name="prometheus_reflect")
        async def prometheus_reflect(outcome: str, task_id: Optional[str] = None) -> dict:
            """Trigger self-reflection on a completed task or action."""
            try:
                await self.provider._ensure_initialized()
                if (
                    self.provider._orchestrator
                    and hasattr(self.provider._orchestrator, "reflection")
                    and hasattr(self.provider._orchestrator.reflection, "reflect")
                ):
                    reflection = await self.provider._orchestrator.reflection.reflect(
                        outcome, task_id
                    )
                    return {
                        "success": True,
                        "tool": "prometheus_reflect",
                        "outcome": outcome,
                        "task_id": task_id,
                        "reflection": reflection,
                    }
                else:
                    return {
                        "success": False,
                        "tool": "prometheus_reflect",
                        "error": "Reflection module not available",
                    }
            except Exception as e:
                logger.error(f"Prometheus reflect error: {e}")
                return {"success": False, "tool": "prometheus_reflect", "error": str(e)}

        @mcp_server.tool(name="prometheus_create_tool")
        async def prometheus_create_tool(tool_description: str, language: str = "python") -> dict:
            """Generate a new tool dynamically (AutoTools) based on description."""
            try:
                await self.provider._ensure_initialized()
                if hasattr(self.provider._orchestrator, "tool_factory"):
                    new_tool = await self.provider._orchestrator.tool_factory.create_tool(
                        tool_description, language
                    )
                    return {
                        "success": True,
                        "tool": "prometheus_create_tool",
                        "description": tool_description,
                        "language": language,
                        "new_tool": new_tool,
                    }
                else:
                    return {
                        "success": False,
                        "tool": "prometheus_create_tool",
                        "error": "Tool Factory not available",
                    }
            except Exception as e:
                logger.error(f"Prometheus create tool error: {e}")
                return {"success": False, "tool": "prometheus_create_tool", "error": str(e)}

        @mcp_server.tool(name="prometheus_get_status")
        async def prometheus_get_status() -> dict:
            """Get full PROMETHEUS system status (memory, world model, evolution)."""
            try:
                status = self.provider.get_status()
                return {"success": True, "tool": "prometheus_get_status", "status": status}
            except Exception as e:
                logger.error(f"Prometheus get status error: {e}")
                return {"success": False, "tool": "prometheus_get_status", "error": str(e)}

        @mcp_server.tool(name="prometheus_benchmark")
        async def prometheus_benchmark(suite: str = "all") -> dict:
            """Run PROMETHEUS benchmark suite to measure capabilities."""
            try:
                await self.provider._ensure_initialized()
                if hasattr(self.provider._orchestrator, "run_benchmark"):
                    results = await self.provider._orchestrator.run_benchmark(suite)
                    return {
                        "success": True,
                        "tool": "prometheus_benchmark",
                        "suite": suite,
                        "results": results,
                    }
                else:
                    return {
                        "success": False,
                        "tool": "prometheus_benchmark",
                        "error": "Benchmark capability not available",
                    }
            except Exception as e:
                logger.error(f"Prometheus benchmark error: {e}")
                return {"success": False, "tool": "prometheus_benchmark", "error": str(e)}

        # Register all tools
        self._mcp_tools.update(
            {
                "prometheus_execute": prometheus_execute,
                "prometheus_memory_query": prometheus_memory_query,
                "prometheus_simulate": prometheus_simulate,
                "prometheus_evolve": prometheus_evolve,
                "prometheus_reflect": prometheus_reflect,
                "prometheus_create_tool": prometheus_create_tool,
                "prometheus_get_status": prometheus_get_status,
                "prometheus_benchmark": prometheus_benchmark,
            }
        )

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())
