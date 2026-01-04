"""
Protocol Bridge - MCP and A2A delegation methods for Bridge.

Extracted from Bridge class to comply with CODE_CONSTITUTION <500 lines.
Provides mixin for MCP and A2A protocol integration.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .managers import MCPManager, A2AManager


class ProtocolBridgeMixin:
    """Mixin providing MCP and A2A delegation methods for Bridge."""

    _mcp_manager: "MCPManager"
    _a2a_manager: "A2AManager"

    # =========================================================================
    # MCP MANAGEMENT (Phase 6.2)
    # =========================================================================

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP server and connection status."""
        return self._mcp_manager.get_status()

    async def start_mcp_server(self, port: int = 3000) -> Dict[str, Any]:
        """Start the local MCP server."""
        tools = getattr(self, "tools", None)
        registry = getattr(tools, "registry", None) if tools else None
        return await self._mcp_manager.start_server(
            tool_registry=registry,
            port=port,
        )

    async def stop_mcp_server(self) -> Dict[str, Any]:
        """Stop the local MCP server."""
        return await self._mcp_manager.stop_server()

    async def connect_mcp(self, url: str) -> Dict[str, Any]:
        """Connect to an external MCP server."""
        return await self._mcp_manager.connect_external(url)

    async def disconnect_mcp(self, name: str) -> Dict[str, Any]:
        """Disconnect from an external MCP server."""
        return await self._mcp_manager.disconnect(name)

    def list_mcp_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        return self._mcp_manager.list_tools()

    # =========================================================================
    # A2A MANAGEMENT (Phase 6.3)
    # =========================================================================

    def get_a2a_status(self) -> Dict[str, Any]:
        """Get A2A server and discovery status."""
        return self._a2a_manager.get_status()

    async def start_a2a_server(self, port: int = 50051) -> Dict[str, Any]:
        """Start the A2A gRPC server."""
        return await self._a2a_manager.start_server(port=port)

    async def stop_a2a_server(self) -> Dict[str, Any]:
        """Stop the A2A gRPC server."""
        return await self._a2a_manager.stop_server()

    async def discover_a2a_agents(self) -> List[Dict[str, Any]]:
        """Discover agents on network."""
        await self._a2a_manager.discover_agents()
        return self._a2a_manager.get_discovered_agents()

    async def call_a2a_agent(self, agent_id: str, task: str) -> AsyncIterator[str]:
        """Send task to remote agent."""
        async for chunk in self._a2a_manager.call_agent(agent_id, task):
            yield chunk

    def get_a2a_card(self) -> Optional[Dict[str, Any]]:
        """Get local agent card."""
        return self._a2a_manager.get_local_card()

    async def sign_a2a_card(self, key_path: str) -> Dict[str, Any]:
        """Sign agent card with JWS."""
        return await self._a2a_manager.sign_card(key_path)

    def get_discovered_agents(self) -> List[Dict[str, Any]]:
        """Get list of discovered agents."""
        return self._a2a_manager.get_discovered_agents()
