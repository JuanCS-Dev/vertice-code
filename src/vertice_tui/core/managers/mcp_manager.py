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
import asyncio
import shlex
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_cli.tools.base import ToolRegistry

# MCP Imports
try:
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    from mcp import ClientSession, StdioServerParameters

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

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
    session: Optional[Any] = None  # ClientSession
    task: Optional[asyncio.Task] = None
    disconnect_event: asyncio.Event = field(default_factory=asyncio.Event)


# =============================================================================
# MCP MANAGER
# =============================================================================


class MCPManager:
    """
    Manages MCP server lifecycle and external connections.
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
        """Get complete MCP status."""
        return {
            "server": asdict(self._server_state),
            "connections": [
                {
                    k: v
                    for k, v in asdict(c).items()
                    if k not in ["session", "task", "disconnect_event"]
                }
                for c in self._connections.values()
            ],
            "total_exposed_tools": len(self._exposed_tools),
            "total_imported_tools": sum(len(tools) for tools in self._imported_tools.values()),
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
        """Start the local MCP server."""
        if self._server_state.running:
            return {"success": False, "error": "Server already running"}

        try:
            from vertice_cli.integrations.mcp.server import QwenMCPServer
            from vertice_cli.integrations.mcp.config import MCPConfig

            if tool_registry is None:
                from vertice_cli.tools.registry_helper import get_default_registry

                tool_registry = get_default_registry()

            config = MCPConfig.from_env()
            config.enabled = True
            config.port = port
            config.host = host
            config.transport = transport

            self._server = QwenMCPServer(config)
            self._server.initialize(tool_registry)

            # In stdio mode, start_server usually blocks or runs in background
            # For TUI, we might need to handle this differently depending on transport
            # But QwenMCPServer.run() is async.
            # If transport is stdio, it awaits stdin/stdout loop.
            # If transport is sse, it starts an aiohttp app.

            # Since we are inside the TUI, we probably want SSE server to be backgrounded.
            # Stdio server inside TUI is tricky (TUI owns stdio).
            if transport == "stdio":
                # We cannot run stdio server inside the TUI process easily as TUI uses stdio
                return {"success": False, "error": "Cannot run stdio server inside TUI"}

            # For SSE, we spawn a task
            asyncio.create_task(self._server.run())

            self._server_state.running = True
            self._server_state.port = port
            self._server_state.host = host
            self._server_state.transport = transport
            self._server_state.error = None

            all_tools = tool_registry.get_all()
            self._exposed_tools = list(all_tools.keys())
            self._server_state.exposed_tools = len(self._exposed_tools)

            logger.info(f"MCP server started on {host}:{port} ({transport})")
            return {
                "success": True,
                "port": port,
                "host": host,
                "tools_exposed": len(self._exposed_tools),
            }

        except ImportError as e:
            return {"success": False, "error": f"Dependencies missing: {e}"}
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return {"success": False, "error": str(e)}

    async def stop_server(self) -> Dict[str, Any]:
        """Stop the local MCP server."""
        if not self._server_state.running:
            return {"success": False, "error": "Server not running"}

        try:
            if self._server:
                await self._server.stop()

            self._server = None
            self._server_state.running = False
            self._exposed_tools.clear()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # EXTERNAL CONNECTIONS
    # =========================================================================

    async def connect_external(
        self,
        url: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Connect to an external MCP server."""
        if not MCP_AVAILABLE:
            return {"success": False, "error": "mcp package not installed"}

        conn_name = name or url
        if conn_name in self._connections:
            return {"success": False, "error": f"Already connected to {conn_name}"}

        conn = MCPClientConnection(url=url, name=conn_name)
        self._connections[conn_name] = conn

        # Spawn background task to manage connection
        conn.task = asyncio.create_task(self._manage_connection(conn))

        # Wait briefly for connection to establish
        for _ in range(20):
            if conn.connected:
                return {"success": True, "name": conn_name, "tools": len(conn.tools)}
            if conn.error:
                del self._connections[conn_name]
                return {"success": False, "error": conn.error}
            await asyncio.sleep(0.1)

        return {"success": True, "name": conn_name, "status": "connecting..."}

    async def _manage_connection(self, conn: MCPClientConnection):
        """Background task to manage MCP connection lifecycle."""
        try:
            if conn.url.startswith("http://") or conn.url.startswith("https://"):
                async with sse_client(conn.url) as (read, write):
                    await self._run_session(conn, read, write)
            else:
                # Assume command
                args = shlex.split(conn.url)
                server_params = StdioServerParameters(command=args[0], args=args[1:], env=None)
                async with stdio_client(server_params) as (read, write):
                    await self._run_session(conn, read, write)
        except Exception as e:
            conn.error = str(e)
            conn.connected = False
            logger.error(f"MCP Connection error {conn.name}: {e}")
        finally:
            if conn.name in self._connections:
                del self._connections[conn.name]

    async def _run_session(self, conn, read, write):
        """Run the MCP session."""
        async with ClientSession(read, write) as session:
            conn.session = session
            await session.initialize()

            # List tools
            result = await session.list_tools()
            conn.tools = [t.name for t in result.tools]
            self._imported_tools[conn.name] = conn.tools

            conn.connected = True
            conn.error = None

            # Wait until disconnect requested
            await conn.disconnect_event.wait()

    async def disconnect(self, name: str) -> Dict[str, Any]:
        """Disconnect from an external MCP server."""
        if name not in self._connections:
            return {"success": False, "error": f"No connection named {name}"}

        try:
            conn = self._connections[name]
            conn.disconnect_event.set()

            if conn.task:
                try:
                    await asyncio.wait_for(conn.task, timeout=2.0)
                except asyncio.TimeoutError:
                    conn.task.cancel()

            return {"success": True, "name": name}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # TOOL LISTING
    # =========================================================================

    def list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools."""
        return {
            "exposed": self._exposed_tools.copy(),
            "imported": {name: tools.copy() for name, tools in self._imported_tools.items()},
        }
