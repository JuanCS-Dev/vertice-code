"""
OrchestratorAgent package (deployable).

This is the Phase 2 "brain" orchestrator, intended to be deployable to Vertex AI
Reasoning Engines. Keep imports light and avoid pulling the local/CLI orchestration
stack from `vertice_core.agents.orchestrator.*`.
"""

from .agent import OrchestratorAgent
from .decomposer import TaskDecomposer
from .router import TaskRouter
from .types import (
    AgentRole,
    ApprovalCallback,
    ApprovalRequest,
    AutonomyLevel,
    Handoff,
    NotifyCallback,
    Task,
    TaskComplexity,
)

__all__ = [
    "OrchestratorAgent",
    "TaskDecomposer",
    "TaskRouter",
    "AgentRole",
    "TaskComplexity",
    "Task",
    "AutonomyLevel",
    "ApprovalRequest",
    "ApprovalCallback",
    "NotifyCallback",
    "Handoff",
]
