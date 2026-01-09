"""
Orchestrator Models - Data structures for execution.

StateTransition, ExecutionStep, ExecutionPlan, and Handoff dataclasses.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from vertice_core.agents.router import AgentType, TaskComplexity
from vertice_core.agents.context import ExecutionResult

from .types import OrchestratorState, HandoffType


@dataclass
class StateTransition:
    """A transition between orchestrator states."""

    from_state: OrchestratorState
    to_state: OrchestratorState
    condition: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """A step in the execution plan."""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    agent_type: AgentType = AgentType.EXECUTOR
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    requires_approval: bool = False
    timeout_seconds: float = 60.0
    retry_count: int = 0
    max_retries: int = 2

    # Status
    status: str = "pending"  # pending, running, completed, failed, skipped
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[ExecutionResult] = None


@dataclass
class ExecutionPlan:
    """A plan consisting of multiple execution steps."""

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str = ""
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    created_by: str = ""
    complexity: TaskComplexity = TaskComplexity.MODERATE

    # Execution state
    current_step_index: int = 0
    completed_steps: int = 0
    failed_steps: int = 0

    def get_current_step(self) -> Optional[ExecutionStep]:
        """Get the current step to execute."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def get_pending_steps(self) -> List[ExecutionStep]:
        """Get steps that are pending execution."""
        return [s for s in self.steps if s.status == "pending"]

    def get_runnable_steps(self) -> List[ExecutionStep]:
        """Get steps that can run now (dependencies met)."""
        completed_ids = {s.step_id for s in self.steps if s.status == "completed"}
        runnable = []
        for step in self.steps:
            if step.status != "pending":
                continue
            if all(dep in completed_ids for dep in step.dependencies):
                runnable.append(step)
        return runnable

    def is_complete(self) -> bool:
        """Check if plan execution is complete."""
        return all(s.status in ("completed", "skipped") for s in self.steps)

    def has_failed(self) -> bool:
        """Check if any step failed without recovery."""
        return any(s.status == "failed" and s.retry_count >= s.max_retries for s in self.steps)


@dataclass
class Handoff:
    """An agent handoff request."""

    handoff_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: AgentType = AgentType.CHAT
    to_agent: AgentType = AgentType.EXECUTOR
    handoff_type: HandoffType = HandoffType.SEQUENTIAL
    reason: str = ""
    context_updates: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
