"""
Vertice Protocols - Communication Standards
===========================================

A2A v0.3 Protocol implementation with:
- Protocol Buffers (canonical binary encoding)
- gRPC service (HTTP/2 + TLS)
- JSON-RPC 2.0 (HTTP)
- Agent Cards with JWS signatures

Phase 4 Integration:
- A2A Protocol (Agent-to-Agent) v0.3
- MCP Integration (Model Context Protocol) 2025-11-25

Reference:
- A2A Protocol: https://a2a-protocol.org/latest/specification/
- Linux Foundation A2A Project: https://github.com/a2aproject/A2A
- gRPC: https://grpc.io/docs/languages/python/

Author: JuanCS Dev
Date: 2025-12-30
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
from .grpc_server import (
    TaskStore,
    A2AServiceImpl,
    create_grpc_server,
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
    # gRPC (Phase 4)
    "TaskStore",
    "A2AServiceImpl",
    "create_grpc_server",
]
