"""
Squad Types - Domain models for DevSquad orchestration.

Enums and Pydantic models for the 5-phase workflow.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...agents.base import AgentResponse


class WorkflowPhase(str, Enum):
    """5-phase workflow stages."""

    ARCHITECTURE = "architecture"
    EXPLORATION = "exploration"
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhaseResult(BaseModel):
    """Result of a single workflow phase.

    Attributes:
        phase: Workflow phase identifier
        success: Whether phase succeeded
        agent_response: Underlying agent execution response
        started_at: Phase start timestamp
        completed_at: Phase completion timestamp
        duration_seconds: Execution duration
    """

    phase: WorkflowPhase
    success: bool
    agent_response: AgentResponse
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WorkflowResult(BaseModel):
    """Complete workflow execution result.

    Attributes:
        workflow_id: Unique workflow identifier
        request: Original user request
        status: Overall workflow status
        phases: Results from each phase
        artifacts: Generated artifacts (files, reports, etc.)
        total_duration_seconds: Total execution time
        metadata: Arbitrary metadata
    """

    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: str
    status: WorkflowStatus
    phases: List[PhaseResult] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    total_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "WorkflowPhase",
    "WorkflowStatus",
    "PhaseResult",
    "WorkflowResult",
]
