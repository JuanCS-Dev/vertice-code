"""
Vertice MCP Client - Python SDK

Generated with ❤️ by Vertex AI Codey
For the evolution of collective AI.

This SDK provides a complete Python interface to the Vertice MCP (Model Context Protocol)
server, enabling seamless integration with the collective AI ecosystem.
"""

from vertice_mcp.client import MCPClient, AsyncMCPClient
from vertice_mcp.types import (
    AgentTask,
    AgentResponse,
    TaskResult,
    MCPError,
    Skill,
    ConsensusResult,
    MCPClientConfig,
)

__version__ = "1.0.0"
__author__ = "Vertice AI Collective"

__all__ = [
    "MCPClient",
    "AsyncMCPClient",
    "AgentTask",
    "AgentResponse",
    "TaskResult",
    "MCPError",
    "Skill",
    "ConsensusResult",
    "MCPClientConfig",
]
