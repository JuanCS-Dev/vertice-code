"""
Session Manager Types - Domain models for session persistence.

Enums and dataclasses for the SessionManager system.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class SessionState(Enum):
    """Session states."""

    NEW = "new"
    ACTIVE = "active"
    PAUSED = "paused"
    CRASHED = "crashed"
    COMPLETED = "completed"
    RECOVERED = "recovered"


@dataclass
class ConversationMessage:
    """A message in the conversation."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Deserialize from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionSnapshot:
    """A snapshot of session state."""

    session_id: str
    state: SessionState
    created_at: float
    updated_at: float
    checksum: str

    # Conversation state
    messages: List[ConversationMessage]
    context: Dict[str, Any]

    # Working state
    working_directory: str
    open_files: List[str]
    pending_operations: List[Dict[str, Any]]

    # File tracking (consolidated from integration/session.py)
    read_files: set[str] = field(default_factory=set)
    modified_files: set[str] = field(default_factory=set)
    deleted_files: set[str] = field(default_factory=set)
    environment_snapshot: Dict[str, str] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "checksum": self.checksum,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "working_directory": self.working_directory,
            "open_files": self.open_files,
            "pending_operations": self.pending_operations,
            "read_files": list(self.read_files),
            "modified_files": list(self.modified_files),
            "deleted_files": list(self.deleted_files),
            "environment_snapshot": self.environment_snapshot,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSnapshot":
        """Deserialize from dictionary."""
        return cls(
            session_id=data["session_id"],
            state=SessionState(data["state"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            checksum=data["checksum"],
            messages=[ConversationMessage.from_dict(m) for m in data.get("messages", [])],
            context=data.get("context", {}),
            working_directory=data.get("working_directory", os.getcwd()),
            open_files=data.get("open_files", []),
            pending_operations=data.get("pending_operations", []),
            read_files=set(data.get("read_files", [])),
            modified_files=set(data.get("modified_files", [])),
            deleted_files=set(data.get("deleted_files", [])),
            environment_snapshot=data.get("environment_snapshot", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionInfo:
    """Summary information about a session."""

    session_id: str
    state: SessionState
    created_at: float
    updated_at: float
    message_count: int
    working_directory: str
    summary: str  # Brief description


__all__ = [
    "SessionState",
    "ConversationMessage",
    "SessionSnapshot",
    "SessionInfo",
]
