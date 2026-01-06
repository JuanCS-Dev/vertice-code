"""
Orchestrator Agent Types

Dataclasses and types for Orchestrator Agent.
Includes Bounded Autonomy types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum


class TaskComplexity(str, Enum):
    """Task complexity levels for routing decisions."""
    TRIVIAL = "trivial"      # Simple formatting, typos
    SIMPLE = "simple"        # Single-file changes
    MODERATE = "moderate"    # Multi-file, clear scope
    COMPLEX = "complex"      # Architecture decisions
    CRITICAL = "critical"    # Production, security


class AutonomyLevel(str, Enum):
    """
    Bounded Autonomy Levels (Three Loops pattern).

    Based on InfoQ "Where Architects Sit in the Era of AI":
    - L0 (Out of loop): Agent operates autonomously
    - L1 (On the loop): Agent executes, human monitors
    - L2 (In the loop): Agent proposes, human approves
    - L3 (Human only): Human executes, agent advises

    Reference: https://www.infoq.com/articles/architects-ai-era/
    """
    L0_AUTONOMOUS = "L0"     # Full autonomy - execute without approval
    L1_NOTIFY = "L1"         # Execute + notify human afterward
    L2_APPROVE = "L2"        # Propose + wait for human approval
    L3_HUMAN_ONLY = "L3"     # Human must execute, agent only advises


class AgentRole(str, Enum):
    """Agent roles in the agency."""
    ORCHESTRATOR = "orchestrator"
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    RESEARCHER = "researcher"
    DEVOPS = "devops"
    PROMETHEUS = "prometheus"


@dataclass
class ApprovalRequest:
    """Request for human approval (L2/L3 operations)."""
    id: str
    task_id: str
    operation: str
    description: str
    autonomy_level: AutonomyLevel
    proposed_action: str
    risk_assessment: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "operation": self.operation,
            "description": self.description,
            "autonomy_level": self.autonomy_level.value,
            "proposed_action": self.proposed_action,
            "risk_assessment": self.risk_assessment,
            "created_at": self.created_at,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }


@dataclass
class Task:
    """A task to be executed by an agent."""
    id: str
    description: str
    complexity: TaskComplexity = TaskComplexity.MODERATE
    autonomy_level: AutonomyLevel = AutonomyLevel.L1_NOTIFY
    assigned_to: Optional[AgentRole] = None
    parent_task: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None
    approval_request: Optional[ApprovalRequest] = None


@dataclass
class Handoff:
    """Handoff between agents (OpenAI pattern)."""
    from_agent: AgentRole
    to_agent: AgentRole
    context: str
    task_id: str
    reason: str


# Type aliases for callbacks
ApprovalCallback = Callable[[ApprovalRequest], bool]
NotifyCallback = Callable[[str, Dict[str, Any]], None]
