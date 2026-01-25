"""
Workflow Types - Domain models for workflow visualization.

Extracted from workflow_visualizer.py for modularity.
Single responsibility: Define workflow data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from collections import deque


class StepStatus(Enum):
    """Workflow step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class WorkflowStep:
    """
    Represents a single workflow step.

    Attributes:
        id: Unique step identifier
        name: Human-readable step name
        status: Current execution status
        dependencies: List of step IDs this step depends on
        start_time: When execution started
        end_time: When execution completed
        error: Error message if failed
        progress: Completion progress (0.0 to 1.0)
        streaming_tokens: Buffer for streaming LLM output
        changes: Tracked file/state changes
        ai_suggestion: AI-generated suggestion for errors
        checkpoint_id: Associated checkpoint if any
    """

    id: str
    name: str
    status: StepStatus = StepStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0

    # Streaming updates (Cursor/Claude style)
    streaming_tokens: deque = field(default_factory=lambda: deque(maxlen=100))

    # Change tracking (diff-style)
    changes: List[Dict[str, str]] = field(default_factory=list)

    # AI suggestions
    ai_suggestion: Optional[str] = None

    # Checkpoint data
    checkpoint_id: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Calculate step duration in seconds."""
        if self.start_time:
            end = self.end_time or datetime.now()
            return (end - self.start_time).total_seconds()
        return None

    @property
    def status_emoji(self) -> str:
        """Get emoji for current status."""
        return {
            StepStatus.PENDING: "...",
            StepStatus.RUNNING: ">>>",
            StepStatus.COMPLETED: "[OK]",
            StepStatus.FAILED: "[X]",
            StepStatus.SKIPPED: "[->]",
            StepStatus.BLOCKED: "[!]",
        }[self.status]

    def add_streaming_token(self, token: str) -> None:
        """Add streaming token (Cursor/Claude style)."""
        self.streaming_tokens.append((datetime.now(), token))

    def add_change(self, change_type: str, before: str, after: str) -> None:
        """Track changes diff-style."""
        self.changes.append(
            {
                "type": change_type,
                "before": before,
                "after": after,
                "timestamp": datetime.now().isoformat(),
            }
        )


@dataclass
class Checkpoint:
    """
    Workflow checkpoint for undo/rollback support.

    Attributes:
        checkpoint_id: Unique checkpoint identifier
        timestamp: When checkpoint was created
        description: Human-readable description
        steps_state: Snapshot of all step states
    """

    checkpoint_id: str
    timestamp: str
    description: str
    steps_state: Dict[str, Dict]


__all__ = ["StepStatus", "WorkflowStep", "Checkpoint"]
