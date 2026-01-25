"""
Context Types - Domain models for multi-agent context management.

Enums and dataclasses for the UnifiedContext system.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContextState(str, Enum):
    """State of the context."""

    ACTIVE = "active"
    COMPACTING = "compacting"
    STALE = "stale"
    PERSISTED = "persisted"


class DecisionType(str, Enum):
    """Types of decisions made during execution."""

    ROUTING = "routing"  # Which agent to use
    PLANNING = "planning"  # How to approach task
    EXECUTION = "execution"  # What action to take
    APPROVAL = "approval"  # Human approval
    ROLLBACK = "rollback"  # Undo decision
    HANDOFF = "handoff"  # Transfer to another agent


@dataclass
class Decision:
    """
    A decision made during execution.

    Used for explainability and rollback.
    """

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    decision_type: DecisionType = DecisionType.EXECUTION
    agent_id: str = ""
    description: str = ""
    reasoning: str = ""
    alternatives_considered: List[str] = field(default_factory=list)
    confidence: float = 1.0
    outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.decision_id,
            "type": self.decision_type.value,
            "agent": self.agent_id,
            "description": self.description,
            "reasoning": self.reasoning[:200] if self.reasoning else "",
            "confidence": self.confidence,
            "outcome": self.outcome,
        }


@dataclass
class ErrorContext:
    """
    Context about an error encountered during execution.

    Used for self-correction and debugging.
    """

    error_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    error_type: str = ""
    error_message: str = ""
    agent_id: str = ""
    step_id: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.error_id,
            "type": self.error_type,
            "message": self.error_message[:200],
            "agent": self.agent_id,
            "step": self.step_id,
            "recovered": self.recovery_successful,
        }


@dataclass
class FileContext:
    """
    File added to context with metadata.

    Tracks which files are relevant to current task.
    """

    filepath: str
    content: str = ""
    start_line: int = 1
    end_line: int = 0
    tokens: int = 0
    relevance_score: float = 1.0
    added_by: str = ""  # Agent or user
    added_at: float = field(default_factory=time.time)
    language: str = ""

    def __post_init__(self):
        """Calculate tokens if not provided."""
        if self.tokens == 0 and self.content:
            self.tokens = len(self.content) // 4
        if self.end_line == 0 and self.content:
            self.end_line = self.content.count("\n") + 1
        if not self.language:
            ext = Path(self.filepath).suffix
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".go": "go",
                ".rs": "rust",
                ".java": "java",
            }
            self.language = lang_map.get(ext, "text")


@dataclass
class ExecutionResult:
    """Result of executing a step."""

    step_id: str
    success: bool
    output: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0
    files_modified: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThoughtSignature:
    """
    Thought signature for maintaining reasoning chain.

    Inspired by Gemini 3's encrypted thought signatures.
    """

    signature_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    agent_id: str = ""
    thought_hash: str = ""  # Hash of reasoning state
    key_insights: List[str] = field(default_factory=list)
    next_action: str = ""
    confidence: float = 1.0

    @classmethod
    def from_reasoning(
        cls,
        agent_id: str,
        reasoning: str,
        insights: List[str],
        next_action: str,
    ) -> "ThoughtSignature":
        """Create thought signature from reasoning."""
        thought_hash = hashlib.sha256(reasoning.encode()).hexdigest()[:16]
        return cls(
            agent_id=agent_id,
            thought_hash=thought_hash,
            key_insights=insights[:5],  # Keep top 5 insights
            next_action=next_action,
        )


__all__ = [
    "ContextState",
    "DecisionType",
    "Decision",
    "ErrorContext",
    "FileContext",
    "ExecutionResult",
    "ThoughtSignature",
]
