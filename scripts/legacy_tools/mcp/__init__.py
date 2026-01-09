"""
Vertice MCP Server

Model Context Protocol server for agent coordination.
Exposes tools for:
- Agent delegation (delegate_to_ai)
- Memory operations
- Tool execution
"""

from .server import VerticeMCPServer, get_server

__all__ = ["VerticeMCPServer", "get_server"]
