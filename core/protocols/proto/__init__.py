"""
A2A Protocol Protobuf Definitions
=================================

Generated from .proto files using grpcio-tools.
"""

# Common types
from .common_pb2 import (
    PartType,
    ErrorSeverity,
    TextPart,
    FilePart,
    DataPart,
    Part,
    Artifact,
    Error,
)

# Message types
from .message_pb2 import (
    MessageRole,
    Message,
    StreamChunk,
    StreamEventType,
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
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    GetAgentCardRequest,
    GetAgentCardResponse,
)

# Service types
from .service_pb2 import (
    SubscribeTaskRequest,
    HealthCheckRequest,
    HealthCheckResponse,
    HealthStatus,
)

# gRPC service
from .service_pb2_grpc import (
    A2AServiceServicer,
    A2AServiceStub,
    add_A2AServiceServicer_to_server,
)

__all__ = [
    # Common
    "PartType",
    "ErrorSeverity",
    "TextPart",
    "FilePart",
    "DataPart",
    "Part",
    "Artifact",
    "Error",
    # Message
    "MessageRole",
    "Message",
    "StreamChunk",
    "StreamEventType",
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
    "AgentCard",
    "AgentSkill",
    "AgentCapabilities",
    "GetAgentCardRequest",
    "GetAgentCardResponse",
    # Service
    "SubscribeTaskRequest",
    "HealthCheckRequest",
    "HealthCheckResponse",
    "HealthStatus",
    # gRPC
    "A2AServiceServicer",
    "A2AServiceStub",
    "add_A2AServiceServicer_to_server",
]
