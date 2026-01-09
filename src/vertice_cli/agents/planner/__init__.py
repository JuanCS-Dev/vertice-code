"""
planner: Goal-Oriented Action Planning System.

This package provides a comprehensive planning system based on:
- GOAP (Goal-Oriented Action Planning) from F.E.A.R.
- Claude Code Plan Mode patterns
- Cursor 2.1 Clarifying Questions
- Devin Confidence Ratings
- Verbalized Sampling (Zhang et al. 2025)

Modules:
- agent: The main PlannerAgent class
- types: Domain types (Enums, Pydantic models)
- models: Domain models (SOPStep, ExecutionPlan, etc.)
- goap: GOAP planning with A* pathfinding
- dependency: Dependency graph analysis
- validation: Plan validation
- monitoring: Execution monitoring

Example:
    from vertice_cli.agents.planner import PlannerAgent
    from vertice_cli.agents.planner import ExecutionPlan, SOPStep
    from vertice_cli.agents.planner.goap import GOAPPlanner, WorldState
"""

# Re-export types (enums and lightweight models)
from .types import (
    # Enums
    ExecutionStrategy,
    AgentPriority,
    CheckpointType,
    PlanningMode,
    ConfidenceLevel,
    PlanStrategy,
    # Dataclasses
    StepConfidence,
    PlanProbabilities,
    # Pydantic Models (lightweight)
    ClarifyingQuestion,
    ClarificationResponse,
    AlternativePlan,
    MultiPlanResult,
)

# Re-export domain models
from .models import (
    SOPStep,
    ExecutionStage,
    ExecutionPlan,
)

# Re-export GOAP
from .goap import (
    WorldState,
    GoalState,
    Action,
    GOAPPlanner,
)

# Re-export dependency analysis
from .dependency import DependencyAnalyzer

# Re-export validation
from .validation import PlanValidator

# Re-export monitoring
from .monitoring import (
    ExecutionEvent,
    ExecutionMonitor,
)

# Re-export formatting utilities
from .formatting import (
    format_plan_as_markdown,
    generate_confidence_summary,
)

# Re-export multi-planning utilities
from .multi_planning import (
    generate_multi_plan,
    create_fallback_plan,
    select_best_plan,
    build_comparison_summary,
)

# Re-export PlannerAgent from agent module
from .agent import PlannerAgent

# Re-export from base for backwards compatibility
from ..base import AgentTask, AgentResponse, AgentCapability

__all__ = [
    # Main Agent
    "PlannerAgent",
    # Base re-exports
    "AgentTask",
    "AgentResponse",
    "AgentCapability",
    # Types - Enums
    "ExecutionStrategy",
    "AgentPriority",
    "CheckpointType",
    "PlanningMode",
    "ConfidenceLevel",
    "PlanStrategy",
    # Types - Dataclasses
    "StepConfidence",
    "PlanProbabilities",
    # Types - Pydantic
    "ClarifyingQuestion",
    "ClarificationResponse",
    "AlternativePlan",
    "MultiPlanResult",
    # Domain Models
    "SOPStep",
    "ExecutionStage",
    "ExecutionPlan",
    # GOAP
    "WorldState",
    "GoalState",
    "Action",
    "GOAPPlanner",
    # Dependency
    "DependencyAnalyzer",
    # Validation
    "PlanValidator",
    # Monitoring
    "ExecutionEvent",
    "ExecutionMonitor",
    # Formatting
    "format_plan_as_markdown",
    "generate_confidence_summary",
    # Multi-Planning
    "generate_multi_plan",
    "create_fallback_plan",
    "select_best_plan",
    "build_comparison_summary",
]
