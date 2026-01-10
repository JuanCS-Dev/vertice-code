"""Types and enums for agent handoffs."""

from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from ..router import AgentType


class HandoffStatus(str, Enum):
    """Status of a handoff."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class HandoffReason(str, Enum):
    """Reason for handoff."""

    TASK_COMPLETION = "task_completion"
    CAPABILITY_REQUIRED = "capability_required"
    ESCALATION = "escalation"
    SPECIALIZATION = "specialization"
    PARALLEL_EXECUTION = "parallel_execution"
    USER_REQUEST = "user_request"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class AgentCapability:
    """Capabilities of an agent."""

    agent_type: AgentType
    capabilities: Set[str] = field(default_factory=set)
    max_complexity: str = "complex"
    can_plan: bool = False
    can_execute: bool = True
    can_review: bool = False
    priority: int = 0
    description: str = ""

    def can_handle(self, required: Set[str]) -> bool:
        """Check if agent can handle required capabilities."""
        return required.issubset(self.capabilities)


@dataclass
class HandoffRequest:
    """A request to hand off to another agent."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: AgentType = AgentType.CHAT
    to_agent: Optional[AgentType] = None
    reason: HandoffReason = HandoffReason.TASK_COMPLETION
    required_capabilities: Set[str] = field(default_factory=set)
    message: str = ""
    context_updates: Dict[str, Any] = field(default_factory=dict)
    preserve_history: bool = True
    timeout_seconds: float = 60.0
    allow_escalation: bool = True
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    actual_to_agent: Optional[AgentType] = None
    error: Optional[str] = None


@dataclass
class HandoffResult:
    """Result of a handoff operation."""

    request_id: str
    success: bool
    from_agent: AgentType
    to_agent: AgentType
    duration_ms: float = 0.0
    message: str = ""
    error: Optional[str] = None


@dataclass
class EscalationChain:
    """Chain of agents for escalation."""

    name: str
    chain: List[AgentType]
    description: str = ""

    def get_next(self, current: AgentType) -> Optional[AgentType]:
        """Get next agent in escalation chain."""
        try:
            idx = self.chain.index(current)
            if idx + 1 < len(self.chain):
                return self.chain[idx + 1]
        except ValueError:
            pass
        return None
