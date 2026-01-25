"""
A2A Task Implementation

Task lifecycle management per A2A specification.

Reference:
- A2A Specification: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime

from .types import (
    MessageRole,
    TaskStatus,
    A2AMessage,
    TaskArtifact,
)

logger = logging.getLogger(__name__)


@dataclass
class A2ATask:
    """
    A2A Task with full lifecycle management.

    Tasks progress through states: submitted → working → completed.
    Supports streaming updates via SSE.
    """

    id: str
    status: TaskStatus
    messages: List[A2AMessage] = field(default_factory=list)
    artifacts: List[TaskArtifact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: MessageRole, content: str) -> A2AMessage:
        """Add a message to the task."""
        message = A2AMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        return message

    def add_artifact(self, name: str, content: str, mime_type: str = "text/plain") -> TaskArtifact:
        """Add an artifact to the task."""
        artifact = TaskArtifact(
            id=str(uuid.uuid4()),
            name=name,
            mime_type=mime_type,
            content=content,
        )
        self.artifacts.append(artifact)
        self.updated_at = datetime.now().isoformat()
        return artifact

    def transition_to(self, status: TaskStatus) -> None:
        """Transition task to a new status."""
        valid_transitions = {
            TaskStatus.SUBMITTED: [TaskStatus.WORKING, TaskStatus.REJECTED],
            TaskStatus.WORKING: [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.INPUT_REQUIRED,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.INPUT_REQUIRED: [TaskStatus.WORKING, TaskStatus.CANCELLED],
        }

        allowed = valid_transitions.get(self.status, [])
        if status not in allowed and self.status != status:
            logger.warning(f"Invalid task transition: {self.status.value} → {status.value}")

        self.status = status
        self.updated_at = datetime.now().isoformat()

    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.REJECTED,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A-compliant dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "parts": m.parts,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp,
                }
                for m in self.messages
            ],
            "artifacts": [
                {
                    "id": a.id,
                    "name": a.name,
                    "mimeType": a.mime_type,
                    "content": a.content,
                    "metadata": a.metadata,
                }
                for a in self.artifacts
            ],
            "metadata": self.metadata,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
