"""
planner/models.py: Domain Models for Planning System.

Contains the core Pydantic models that define the structure of plans:
- SOPStep: Standard Operating Procedure step with GOAP integration
- ExecutionStage: Groups related steps for workflow management
- ExecutionPlan: Complete execution plan with all metadata

These models are the heart of the planning system, representing
the output artifacts that drive multi-agent orchestration.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero TODOs
- Clear docstrings
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .types import (
    AgentPriority,
    CheckpointType,
    ClarificationResponse,
    ClarifyingQuestion,
    ExecutionStrategy,
    PlanningMode,
)


class SOPStep(BaseModel):
    """
    Standard Operating Procedure Step with GOAP integration.

    Represents an atomic unit of work in a plan, with:
    - GOAP preconditions and effects for state tracking
    - Orchestration fields for multi-agent coordination
    - Safety mechanisms (checkpoints, rollback)
    - Observability hooks (correlation ID, telemetry)
    - Confidence ratings (v6.0 Devin pattern)

    Attributes:
        id: Unique identifier for the step
        role: Agent role responsible (e.g., "coder", "reviewer")
        action: Verb describing what to do
        objective: What this step aims to achieve
        definition_of_done: Clear success criteria
    """

    id: str
    role: str
    action: str
    objective: str
    definition_of_done: str

    # GOAP fields - for state machine tracking
    preconditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Required world state before execution",
    )
    effects: Dict[str, Any] = Field(
        default_factory=dict,
        description="Changes to world state after execution",
    )
    cost: float = Field(
        default=1.0,
        description="Execution cost (time/tokens/complexity)",
    )

    # Orchestration fields - for multi-agent coordination
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of steps that must complete first",
    )
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    priority: AgentPriority = AgentPriority.MEDIUM

    # Context isolation - Anthropic SDK best practice
    context_isolation: bool = Field(
        default=True,
        description="Isolate agent context for this step",
    )
    max_tokens: int = Field(
        default=4000,
        description="Token budget for this step",
    )

    # Safety mechanisms
    checkpoint: Optional[CheckpointType] = None
    rollback_on_error: bool = False
    retry_count: int = 0

    # Observability hooks
    correlation_id: Optional[str] = None
    telemetry_tags: Dict[str, str] = Field(default_factory=dict)

    # Confidence Rating (v6.0 - Devin pattern)
    confidence_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence in successful execution (0.0-1.0)",
    )
    confidence_reasoning: str = Field(
        default="",
        description="Explanation for confidence level",
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Known risks that affect confidence",
    )


class ExecutionStage(BaseModel):
    """
    Stage in the workflow - groups related steps.

    Inspired by Claude-Flow's stage system, a stage represents
    a logical phase of work (e.g., "Analysis", "Implementation", "Testing").

    Attributes:
        name: Human-readable stage name
        description: What this stage accomplishes
        steps: List of SOPSteps in this stage
        strategy: How to execute steps (sequential/parallel)
        checkpoint: Whether to checkpoint before continuing
        required: Whether stage must succeed for plan to continue
    """

    name: str
    description: str
    steps: List[SOPStep]
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    checkpoint: bool = False
    required: bool = True


class ExecutionPlan(BaseModel):
    """
    Comprehensive execution plan with enterprise features.

    This is the main output artifact of the PlannerAgent, containing:
    - GOAP state tracking (initial/goal states)
    - Multi-stage execution structure
    - Safety and recovery mechanisms
    - Resource planning and coordination
    - v6.0 enhancements (clarifying questions, confidence)

    The plan serves as a contract between the planner and executor,
    providing all information needed for reliable multi-agent orchestration.
    """

    plan_id: str
    goal: str
    strategy_overview: str

    # GOAP state tracking
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    goal_state: Dict[str, Any] = Field(default_factory=dict)
    estimated_cost: float = 0.0

    # Multi-stage execution structure
    stages: List[ExecutionStage] = Field(default_factory=list)

    # Legacy SOPs (backward compatibility)
    sops: List[SOPStep] = Field(default_factory=list)

    # Safety & Recovery
    rollback_strategy: str = "Restore from last checkpoint"
    checkpoints: List[str] = Field(default_factory=list)
    risk_assessment: str = "MEDIUM"

    # Coordination
    parallel_execution_opportunities: List[List[str]] = Field(
        default_factory=list,
        description="Groups of steps that can run in parallel",
    )
    critical_path: List[str] = Field(
        default_factory=list,
        description="Longest dependency chain (bottleneck)",
    )

    # Resource planning
    estimated_duration: str = "30-60 minutes"
    token_budget: int = 50000
    max_parallel_agents: int = 4

    # Observability
    plan_version: str = "6.0"
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # v6.0: Planning Mode (Claude Code pattern)
    mode: PlanningMode = Field(
        default=PlanningMode.PLANNING,
        description="Current planning mode",
    )

    # v6.0: Clarifying Questions (Cursor 2.1 pattern)
    clarifying_questions: List[ClarifyingQuestion] = Field(
        default_factory=list,
        description="Questions asked before planning",
    )
    clarification_responses: List[ClarificationResponse] = Field(
        default_factory=list,
        description="User's answers to clarifying questions",
    )

    # v6.0: Overall Confidence (Devin pattern)
    overall_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weighted average confidence across all steps",
    )
    confidence_summary: str = Field(
        default="",
        description="Human-readable confidence assessment",
    )

    # v6.0: Plan Artifact Path (Claude Code pattern)
    plan_artifact_path: Optional[str] = Field(
        default=None,
        description="Path to generated plan.md file",
    )


__all__ = [
    "SOPStep",
    "ExecutionStage",
    "ExecutionPlan",
]
