"""MCP Client - Backward compatibility re-export.

All MCP functionality is now in vertice_core.core.mcp
This file exists for backward compatibility.
"""

from vertice_core.core.mcp import MCPClient, create_mcp_client, MCPManager, mcp_manager

__all__ = ["MCPClient", "create_mcp_client", "MCPManager", "mcp_manager"]
