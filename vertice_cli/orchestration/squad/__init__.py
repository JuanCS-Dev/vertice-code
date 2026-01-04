"""
Squad Module - Multi-Agent Orchestration System.

This package provides the DevSquad multi-agent orchestration system.

Submodules:
    - types: Domain models (WorkflowPhase, WorkflowResult, etc.)
    - validation: Input validation for Pipeline Blindado
    - phases: Individual phase execution
    - devsquad: DevSquad class

Usage:
    from vertice_cli.orchestration.squad import DevSquad
    from vertice_cli.orchestration.squad import WorkflowResult, WorkflowStatus
"""

from .types import (
    WorkflowPhase,
    WorkflowStatus,
    PhaseResult,
    WorkflowResult,
)
from .validation import (
    DANGEROUS_PATTERNS,
    validate_input,
)
from .phases import (
    phase_architecture,
    phase_exploration,
    phase_planning,
    phase_execution,
    phase_review,
)
from .devsquad import DevSquad


__all__ = [
    # Types
    "WorkflowPhase",
    "WorkflowStatus",
    "PhaseResult",
    "WorkflowResult",
    # Validation
    "DANGEROUS_PATTERNS",
    "validate_input",
    # Phases
    "phase_architecture",
    "phase_exploration",
    "phase_planning",
    "phase_execution",
    "phase_review",
    # Main class
    "DevSquad",
]
