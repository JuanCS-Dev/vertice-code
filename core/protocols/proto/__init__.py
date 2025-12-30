"""
A2A Protocol Buffers Generated Code
===================================

Auto-generated protobuf and gRPC code for A2A v0.3 protocol.

DO NOT EDIT these files manually - regenerate using:
    cd proto && make proto

Reference:
- A2A Spec: https://a2a-protocol.org/latest/specification/
- Protobuf: https://protobuf.dev/

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

# Common types
from .common_pb2 import (
    PartType,
    TextPart,
    FilePart,
    DataPart,
    Part,
    Artifact,
    ErrorSeverity,
    Error,
)

# Message types
from .message_pb2 import (
    MessageRole,
    Message,
    StreamEventType,
    StreamChunk,
    TaskStatusUpdate,
)

# Task types
from .task_pb2 import (
    TaskState,
    Task,
    TaskStateTransition,
    SendMessageRequest,
    SendMessageResponse,
    GetTaskRequest,
    ListTasksRequest,
    ListTasksResponse,
    CancelTaskRequest,
    CancelTaskResponse,
)

# Agent Card types
from .agent_card_pb2 import (
    AgentCapabilities,
    AgentSkill,
    SkillExample,
    SecuritySchemeType,
    SecurityScheme,
    OAuth2Config,
    OpenIDConnectConfig,
    SupportedInterface,
    AgentCardSignature,
    AgentCard,
    GetAgentCardRequest,
    GetAgentCardResponse,
)

# Service types
from .service_pb2 import (
    SubscribeTaskRequest,
    HealthCheckRequest,
    HealthStatus,
    HealthCheckResponse,
)

# gRPC stubs
from .service_pb2_grpc import (
    A2AServiceStub,
    A2AServiceServicer,
    add_A2AServiceServicer_to_server,
)

__all__ = [
    # Common
    "PartType",
    "TextPart",
    "FilePart",
    "DataPart",
    "Part",
    "Artifact",
    "ErrorSeverity",
    "Error",
    # Message
    "MessageRole",
    "Message",
    "StreamEventType",
    "StreamChunk",
    "TaskStatusUpdate",
    # Task
    "TaskState",
    "Task",
    "TaskStateTransition",
    "SendMessageRequest",
    "SendMessageResponse",
    "GetTaskRequest",
    "ListTasksRequest",
    "ListTasksResponse",
    "CancelTaskRequest",
    "CancelTaskResponse",
    # Agent Card
    "AgentCapabilities",
    "AgentSkill",
    "SkillExample",
    "SecuritySchemeType",
    "SecurityScheme",
    "OAuth2Config",
    "OpenIDConnectConfig",
    "SupportedInterface",
    "AgentCardSignature",
    "AgentCard",
    "GetAgentCardRequest",
    "GetAgentCardResponse",
    # Service
    "SubscribeTaskRequest",
    "HealthCheckRequest",
    "HealthStatus",
    "HealthCheckResponse",
    # gRPC
    "A2AServiceStub",
    "A2AServiceServicer",
    "add_A2AServiceServicer_to_server",
]
