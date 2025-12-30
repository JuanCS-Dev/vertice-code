"""
Vertice Protocols - Communication Standards

Phase 3 Integration:
- A2A Protocol (Agent-to-Agent)
- MCP Integration (Model Context Protocol)

Reference:
- A2A Protocol: https://a2a-protocol.org/
- Linux Foundation A2A Project: https://github.com/a2aproject/A2A
"""

from .types import (
    MessageRole,
    TaskStatus,
    A2AMessage,
    TaskArtifact,
    AgentSkill,
    AgentCapabilities,
)
from .task import A2ATask
from .agent_card import AgentCard
from .mixin import A2AProtocolMixin
from .jsonrpc import (
    create_jsonrpc_request,
    create_jsonrpc_response,
    create_jsonrpc_error,
    JSONRPC_PARSE_ERROR,
    JSONRPC_INVALID_REQUEST,
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_INVALID_PARAMS,
    JSONRPC_INTERNAL_ERROR,
)

__all__ = [
    # Types
    "MessageRole",
    "TaskStatus",
    "A2AMessage",
    "TaskArtifact",
    "AgentSkill",
    "AgentCapabilities",
    # Task
    "A2ATask",
    # Agent Card
    "AgentCard",
    # Mixin
    "A2AProtocolMixin",
    # JSON-RPC
    "create_jsonrpc_request",
    "create_jsonrpc_response",
    "create_jsonrpc_error",
    "JSONRPC_PARSE_ERROR",
    "JSONRPC_INVALID_REQUEST",
    "JSONRPC_METHOD_NOT_FOUND",
    "JSONRPC_INVALID_PARAMS",
    "JSONRPC_INTERNAL_ERROR",
]
