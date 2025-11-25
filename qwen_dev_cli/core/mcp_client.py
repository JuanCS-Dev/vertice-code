"""MCP Client - Backward compatibility re-export.

All MCP functionality is now in qwen_dev_cli.core.mcp
This file exists for backward compatibility.
"""
from qwen_dev_cli.core.mcp import MCPClient, create_mcp_client, MCPManager, mcp_manager

__all__ = ['MCPClient', 'create_mcp_client', 'MCPManager', 'mcp_manager']
