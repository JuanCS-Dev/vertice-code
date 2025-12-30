"""
A2A Protocol Types

Type definitions for Agent-to-Agent protocol.

Reference:
- A2A Specification: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    """Role of message sender in A2A communication."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class TaskStatus(str, Enum):
    """
    Task lifecycle states per A2A specification.

    Flow: submitted → working → input-required/completed/failed/cancelled
    """
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class A2AMessage:
    """
    A2A protocol message.

    Supports text, files, and structured JSON data.
    """
    role: MessageRole
    content: str
    parts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TaskArtifact:
    """Artifact produced by a task (file, data, etc.)."""
    id: str
    name: str
    mime_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSkill:
    """
    A discrete function the agent can perform.

    Skills are the primary way clients discover what an agent can do.
    """
    id: str
    name: str
    description: str
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentCapabilities:
    """
    Optional features the agent supports.

    Based on A2A v0.3 specification.
    """
    streaming: bool = True
    push_notifications: bool = False
    state_transition_history: bool = True
    extensions: List[str] = field(default_factory=list)
