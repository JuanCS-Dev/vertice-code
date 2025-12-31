"""
MCP Manager - Model Context Protocol integration for TUI.

Commands:
- /mcp status: Current state
- /mcp serve [port]: Start server
- /mcp stop: Stop server
- /mcp connect <url>: Connect to external MCP
- /mcp disconnect <name>: Disconnect
- /mcp tools: List tools

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_cli.tools.base import ToolRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# STATE DATACLASSES
# =============================================================================


@dataclass
class MCPServerState:
    """State of the local MCP server."""

    running: bool = False
    port: int = 3000
    transport: str = "stdio"
    exposed_tools: int = 0
    host: str = "127.0.0.1"
    error: Optional[str] = None


@dataclass
class MCPClientConnection:
    """State of an external MCP connection."""

    url: str
    name: str
    connected: bool = False
    tools: List[str] = field(default_factory=list)
    error: Optional[str] = None


# =============================================================================
# MCP MANAGER
# =============================================================================


class MCPManager:
    """
    Manages MCP server lifecycle and external connections.

    Provides:
    - Start/stop local MCP server (via QwenMCPServer)
    - Connect to external MCP servers
    - List available/imported tools
    - Status reporting

    Example:
        manager = MCPManager()
        await manager.start_server(tool_registry, port=3000)
        status = manager.get_status()
    """

    def __init__(self) -> None:
        """Initialize MCP manager."""
        self._server: Optional[Any] = None
        self._server_state = MCPServerState()
        self._connections: Dict[str, MCPClientConnection] = {}
        self._exposed_tools: List[str] = []
        self._imported_tools: Dict[str, List[str]] = {}

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Get complete MCP status.

        Returns:
            Status dict with server and connection info
        """
        return {
            "server": asdict(self._server_state),
            "connections": [asdict(c) for c in self._connections.values()],
            "total_exposed_tools": len(self._exposed_tools),
            "total_imported_tools": sum(
                len(tools) for tools in self._imported_tools.values()
            ),
        }

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._server_state.running

    # =========================================================================
    # SERVER MANAGEMENT
    # =========================================================================

    async def start_server(
        self,
        tool_registry: Optional["ToolRegistry"] = None,
        port: int = 3000,
        host: str = "127.0.0.1",
        transport: str = "stdio",
    ) -> Dict[str, Any]:
        """
        Start the local MCP server.

        Args:
            tool_registry: Registry of tools to expose
            port: Port to listen on (for SSE transport)
            host: Host to bind to
            transport: Transport type (stdio, sse)

        Returns:
            Result dict with success status
        """
        if self._server_state.running:
            return {"success": False, "error": "Server already running"}

        try:
            # Lazy import to avoid dependency issues
            from vertice_cli.integrations.mcp.server import QwenMCPServer
            from vertice_cli.integrations.mcp.config import MCPConfig

            # Get default registry if not provided
            if tool_registry is None:
                from vertice_cli.tools.registry_helper import get_default_registry
                tool_registry = get_default_registry()

            # Configure and initialize
            config = MCPConfig.from_env()
            config.enabled = True
            config.port = port
            config.host = host

            self._server = QwenMCPServer(config)
            self._server.initialize(tool_registry)

            # Update state
            self._server_state.running = True
            self._server_state.port = port
            self._server_state.host = host
            self._server_state.transport = transport
            self._server_state.error = None

            # Track exposed tools
            all_tools = tool_registry.get_all()
            self._exposed_tools = list(all_tools.keys())
            self._server_state.exposed_tools = len(self._exposed_tools)

            logger.info(f"MCP server started on {host}:{port} with {len(self._exposed_tools)} tools")

            return {
                "success": True,
                "port": port,
                "host": host,
                "tools_exposed": len(self._exposed_tools),
            }

        except ImportError as e:
            error_msg = f"MCP dependencies not installed: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to start MCP server: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def stop_server(self) -> Dict[str, Any]:
        """
        Stop the local MCP server.

        Returns:
            Result dict with success status
        """
        if not self._server_state.running:
            return {"success": False, "error": "Server not running"}

        try:
            if self._server is not None:
                await self._server.stop()

            self._server = None
            self._server_state.running = False
            self._server_state.error = None
            self._exposed_tools.clear()
            self._server_state.exposed_tools = 0

            logger.info("MCP server stopped")
            return {"success": True}

        except Exception as e:
            error_msg = f"Error stopping server: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    # =========================================================================
    # EXTERNAL CONNECTIONS
    # =========================================================================

    async def connect_external(
        self,
        url: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Connect to an external MCP server.

        Args:
            url: MCP server URL
            name: Optional connection name

        Returns:
            Result dict with success status
        """
        conn_name = name or url

        if conn_name in self._connections:
            existing = self._connections[conn_name]
            if existing.connected:
                return {"success": False, "error": f"Already connected to {conn_name}"}

        try:
            # Create connection record
            conn = MCPClientConnection(url=url, name=conn_name)

            # Placeholder: actual MCP client connection logic
            # In production, this would use mcp.client to connect
            conn.connected = True
            conn.tools = []  # Would be populated from server

            self._connections[conn_name] = conn
            self._imported_tools[conn_name] = conn.tools

            logger.info(f"Connected to external MCP: {conn_name}")
            return {
                "success": True,
                "name": conn_name,
                "url": url,
                "tools": len(conn.tools),
            }

        except Exception as e:
            error_msg = f"Failed to connect to {url}: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def disconnect(self, name: str) -> Dict[str, Any]:
        """
        Disconnect from an external MCP server.

        Args:
            name: Connection name to disconnect

        Returns:
            Result dict with success status
        """
        if name not in self._connections:
            return {"success": False, "error": f"No connection named {name}"}

        try:
            conn = self._connections[name]
            conn.connected = False

            del self._connections[name]
            if name in self._imported_tools:
                del self._imported_tools[name]

            logger.info(f"Disconnected from MCP: {name}")
            return {"success": True, "name": name}

        except Exception as e:
            error_msg = f"Error disconnecting: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    # =========================================================================
    # TOOL LISTING
    # =========================================================================

    def list_tools(self) -> Dict[str, Any]:
        """
        List all available MCP tools.

        Returns:
            Dict with exposed and imported tools
        """
        return {
            "exposed": self._exposed_tools.copy(),
            "imported": {
                name: tools.copy()
                for name, tools in self._imported_tools.items()
            },
        }

    def get_exposed_tools(self) -> List[str]:
        """Get list of tools exposed by local server."""
        return self._exposed_tools.copy()

    def get_imported_tools(self) -> Dict[str, List[str]]:
        """Get tools imported from external servers."""
        return {
            name: tools.copy()
            for name, tools in self._imported_tools.items()
        }

    # =========================================================================
    # CONNECTION INFO
    # =========================================================================

    def get_connections(self) -> List[Dict[str, Any]]:
        """Get list of active connections."""
        return [
            asdict(conn)
            for conn in self._connections.values()
            if conn.connected
        ]

    def get_connection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get info for a specific connection."""
        if name in self._connections:
            return asdict(self._connections[name])
        return None
