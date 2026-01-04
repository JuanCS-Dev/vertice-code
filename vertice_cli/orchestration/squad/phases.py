"""
Squad Phases - Individual phase execution for DevSquad.

Each phase delegates to a specialist agent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from ...agents.base import AgentTask
from .types import PhaseResult, WorkflowPhase

if TYPE_CHECKING:
    from ...agents.architect import ArchitectAgent
    from ...agents.explorer import ExplorerAgent
    from ...agents.planner import PlannerAgent
    from ...agents.refactorer import RefactorerAgent
    from ...agents.reviewer import ReviewerAgent


async def phase_architecture(
    architect: "ArchitectAgent",
    request: str,
    context: Dict[str, Any],
    session_id: str,
) -> PhaseResult:
    """Phase 1: Architecture analysis with Architect agent."""
    phase_start = datetime.now()

    task = AgentTask(
        request=request,
        context=context,
        session_id=session_id,
    )

    agent_response = await architect.execute(task)
    phase_end = datetime.now()

    return PhaseResult(
        phase=WorkflowPhase.ARCHITECTURE,
        success=agent_response.success,
        agent_response=agent_response,
        started_at=phase_start,
        completed_at=phase_end,
        duration_seconds=(phase_end - phase_start).total_seconds(),
    )


async def phase_exploration(
    explorer: "ExplorerAgent",
    request: str,
    arch_output: Dict[str, Any],
    session_id: str,
) -> PhaseResult:
    """Phase 2: Context exploration with Explorer agent."""
    phase_start = datetime.now()

    context = {
        "architecture": arch_output.get("architecture", {}),
        "project_type": arch_output.get("project_type"),
    }

    task = AgentTask(
        request=request,
        context=context,
        session_id=session_id,
    )

    agent_response = await explorer.execute(task)
    phase_end = datetime.now()

    return PhaseResult(
        phase=WorkflowPhase.EXPLORATION,
        success=agent_response.success,
        agent_response=agent_response,
        started_at=phase_start,
        completed_at=phase_end,
        duration_seconds=(phase_end - phase_start).total_seconds(),
    )


async def phase_planning(
    planner: "PlannerAgent",
    request: str,
    explore_output: Dict[str, Any],
    session_id: str,
) -> PhaseResult:
    """Phase 3: Execution planning with Planner agent."""
    phase_start = datetime.now()

    context = {
        "context_map": explore_output.get("context", {}),
        "relevant_files": explore_output.get("files", []),
    }

    task = AgentTask(
        request=request,
        context=context,
        session_id=session_id,
    )

    agent_response = await planner.execute(task)
    phase_end = datetime.now()

    return PhaseResult(
        phase=WorkflowPhase.PLANNING,
        success=agent_response.success,
        agent_response=agent_response,
        started_at=phase_start,
        completed_at=phase_end,
        duration_seconds=(phase_end - phase_start).total_seconds(),
    )


async def phase_execution(
    refactorer: "RefactorerAgent",
    plan_output: Dict[str, Any],
    session_id: str,
) -> PhaseResult:
    """Phase 4: Code execution with Refactorer agent."""
    phase_start = datetime.now()

    plan = plan_output.get("plan", {})

    task = AgentTask(
        request="Execute the planned changes",
        context={"plan": plan},
        session_id=session_id,
    )

    agent_response = await refactorer.execute(task)
    phase_end = datetime.now()

    return PhaseResult(
        phase=WorkflowPhase.EXECUTION,
        success=agent_response.success,
        agent_response=agent_response,
        started_at=phase_start,
        completed_at=phase_end,
        duration_seconds=(phase_end - phase_start).total_seconds(),
    )


async def phase_review(
    reviewer: "ReviewerAgent",
    exec_output: Dict[str, Any],
    session_id: str,
) -> PhaseResult:
    """Phase 5: Quality review with Reviewer agent."""
    phase_start = datetime.now()

    changed_files = exec_output.get("modified_files", [])

    task = AgentTask(
        request="Review code changes for quality",
        context={"files": changed_files},
        session_id=session_id,
    )

    agent_response = await reviewer.execute(task)
    phase_end = datetime.now()

    return PhaseResult(
        phase=WorkflowPhase.REVIEW,
        success=agent_response.success,
        agent_response=agent_response,
        started_at=phase_start,
        completed_at=phase_end,
        duration_seconds=(phase_end - phase_start).total_seconds(),
    )


__all__ = [
    "phase_architecture",
    "phase_exploration",
    "phase_planning",
    "phase_execution",
    "phase_review",
]
