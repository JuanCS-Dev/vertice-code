"""
Vertice Tools

Tool implementations for the agency:
- MCP Server: Model Context Protocol server
- Filesystem: File operations
- Git: Version control
- Shell: Command execution
- Web: HTTP requests

Usage:
    from tools.mcp import get_server
    server = get_server()
"""

from .mcp import VerticeMCPServer, get_server

__all__ = [
    "VerticeMCPServer",
    "get_server",
]
