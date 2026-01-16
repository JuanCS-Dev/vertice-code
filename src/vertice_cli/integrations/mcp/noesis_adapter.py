"""
Noesis MCP Adapter - Wrapper for existing Noesis ValidatedTools.

Consolidates existing tools from noesis_mcp.py and distributed_noesis_mcp.py
into a consistent adapter pattern for MCPGateway integration.

Does NOT duplicate or reimplement - WRAPS existing tools.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class NoesissMCPAdapter:
    """Adapter to expose Noesis tools via MCP.

    WRAPS existing ValidatedTool classes from:
    - noesis_mcp.py (5 tools)
    - distributed_noesis_mcp.py (6+ tools)

    Does NOT recreate any functionality.
    """

    def __init__(self):
        self._mcp_tools: Dict[str, Any] = {}
        self._noesis_tools: List[Any] = []
        self._distributed_tools: List[Any] = []

    def _get_noesis_tools(self) -> List[Any]:
        """Lazy import to avoid circular dependencies."""
        if not self._noesis_tools:
            from vertice_cli.tools.noesis_mcp import (
                GetNoesisConsciousnessTool,
                ActivateNoesisConsciousnessTool,
                DeactivateNoesisConsciousnessTool,
                QueryNoesisTribunalTool,
                ShareNoesisInsightTool,
            )

            self._noesis_tools = [
                GetNoesisConsciousnessTool(),
                ActivateNoesisConsciousnessTool(),
                DeactivateNoesisConsciousnessTool(),
                QueryNoesisTribunalTool(),
                ShareNoesisInsightTool(),
            ]
        return self._noesis_tools

    def _get_distributed_tools(self) -> List[Any]:
        """Lazy import distributed consciousness tools."""
        if not self._distributed_tools:
            from vertice_cli.tools.distributed_noesis_mcp import (
                ActivateDistributedConsciousnessTool,
                DeactivateDistributedConsciousnessTool,
                GetDistributedConsciousnessStatusTool,
                ProposeDistributedCaseTool,
                GetDistributedCaseStatusTool,
                ShareDistributedInsightTool,
                GetCollectiveInsightsTool,
            )

            self._distributed_tools = [
                ActivateDistributedConsciousnessTool(),
                DeactivateDistributedConsciousnessTool(),
                GetDistributedConsciousnessStatusTool(),
                ProposeDistributedCaseTool(),
                GetDistributedCaseStatusTool(),
                ShareDistributedInsightTool(),
                GetCollectiveInsightsTool(),
            ]
        return self._distributed_tools

    def register_all(self, mcp_server) -> None:
        """Register all Noesis tools as MCP tools."""

        # Register core Noesis tools
        noesis_tools = self._get_noesis_tools()
        for tool in noesis_tools:
            # Wrap ValidatedTool._execute_validated as MCP tool
            async def create_handler(t):
                async def handler(**kwargs):
                    result = await t._execute_validated(**kwargs)
                    if hasattr(result, "to_dict"):
                        return result.to_dict()
                    return {
                        "success": result.success,
                        "message": result.message,
                        "data": result.data,
                        "error": result.error,
                    }

                return handler

            # Register with MCP
            import asyncio

            handler = asyncio.get_event_loop().run_until_complete(create_handler(tool))
            mcp_server.tool(name=tool.name)(handler)
            self._mcp_tools[tool.name] = handler

        # Register distributed consciousness tools
        distributed_tools = self._get_distributed_tools()
        for tool in distributed_tools:

            async def create_dist_handler(t):
                async def handler(**kwargs):
                    result = await t._execute_validated(**kwargs)
                    if hasattr(result, "to_dict"):
                        return result.to_dict()
                    return {
                        "success": result.success,
                        "message": result.message,
                        "data": result.data,
                        "error": result.error,
                    }

                return handler

            import asyncio

            handler = asyncio.get_event_loop().run_until_complete(create_dist_handler(tool))
            mcp_server.tool(name=tool.name)(handler)
            self._mcp_tools[tool.name] = handler

        logger.info(f"Registered {len(self._mcp_tools)} Noesis MCP tools")

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())


__all__ = ["NoesissMCPAdapter"]
