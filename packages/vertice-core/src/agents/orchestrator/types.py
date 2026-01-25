"""
Orchestrator Types - core orchestration domain.

This module is used by the deployable `agents.orchestrator.*` implementation.

Notes:
- Keep this module dependency-light (stdlib only) to remain Reasoning Engine friendly.
- `Task` is intentionally mutable for bounded-autonomy enrichment (e.g. `autonomy_level`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class OrchestratorState(str, Enum):
    """States in the orchestration state machine."""

    # Initial states
    IDLE = "idle"
    INITIALIZING = "initializing"

    # Main loop states
    GATHERING = "gathering"  # Collecting context
    ROUTING = "routing"  # Deciding which agent
    PLANNING = "planning"  # Creating execution plan
    EXECUTING = "executing"  # Running actions
    VERIFYING = "verifying"  # Checking results
    REVIEWING = "reviewing"  # Human/agent review

    # Handoff states
    HANDOFF_PENDING = "handoff_pending"
    HANDOFF_COMPLETE = "handoff_complete"

    # Terminal states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    # Error states
    ERROR_RECOVERY = "error_recovery"
    AWAITING_APPROVAL = "awaiting_approval"


class HandoffType(str, Enum):
    """Types of agent handoffs."""

    SEQUENTIAL = "sequential"  # A → B → C
    PARALLEL = "parallel"  # A + B + C simultaneously
    CONDITIONAL = "conditional"  # A → (B if X else C)
    ESCALATION = "escalation"  # A failed → B (more capable)


class TaskComplexity(str, Enum):
    """Complexity tiers used for routing decisions."""

    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    """Core agent roles available to the OrchestratorAgent."""

    ORCHESTRATOR = "orchestrator"
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    RESEARCHER = "researcher"
    DEVOPS = "devops"
    PROMETHEUS = "prometheus"


class AutonomyLevel(str, Enum):
    """Bounded autonomy levels (L0-L3)."""

    L0_AUTONOMOUS = "L0_AUTONOMOUS"
    L1_NOTIFY = "L1_NOTIFY"
    L2_APPROVE = "L2_APPROVE"
    L3_HUMAN_ONLY = "L3_HUMAN_ONLY"


@dataclass
class Task:
    """A unit of work to be routed/executed by the orchestrator."""

    id: str
    description: str
    complexity: TaskComplexity = TaskComplexity.MODERATE
    parent_task: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)

    autonomy_level: AutonomyLevel = AutonomyLevel.L1_NOTIFY
    approval_request: Optional["ApprovalRequest"] = None


@dataclass
class Handoff:
    """Record representing an orchestrator handoff between agents."""

    from_agent: AgentRole
    to_agent: AgentRole
    context: str
    task_id: str
    reason: str
    handoff_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class ApprovalRequest:
    """Approval request created by BoundedAutonomyMixin (L2/L3)."""

    id: str
    task_id: str
    operation: str
    description: str
    autonomy_level: AutonomyLevel
    proposed_action: str
    risk_assessment: str

    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "operation": self.operation,
            "description": self.description,
            "autonomy_level": self.autonomy_level.value,
            "proposed_action": self.proposed_action,
            "risk_assessment": self.risk_assessment,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }


ApprovalCallback = Callable[[ApprovalRequest], bool]
NotifyCallback = Callable[[str, Dict[str, Any]], None]
