"""
planner/optimization.py: Stage Building and Optimization.

Pure functions for building execution stages, estimating resources,
and generating plan metadata.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from .types import (
    AgentPriority,
    ExecutionStrategy,
)
from .models import (
    SOPStep,
    ExecutionStage,
    ExecutionPlan,
)

if TYPE_CHECKING:
    from .dependency import DependencyAnalyzer


def build_stages(
    sops: List[SOPStep],
    parallel_groups: List[List[str]],
) -> List[ExecutionStage]:
    """
    Group SOPs into execution stages.

    Args:
        sops: List of SOP steps
        parallel_groups: Groups of step IDs that can run in parallel

    Returns:
        List of ExecutionStage objects
    """
    stages = []
    sop_map = {sop.id: sop for sop in sops}

    for level_idx, group in enumerate(parallel_groups):
        stage_steps = [sop_map[sid] for sid in group if sid in sop_map]

        if not stage_steps:
            continue

        # Determine strategy
        strategy = ExecutionStrategy.PARALLEL if len(group) > 1 else ExecutionStrategy.SEQUENTIAL

        # Check if stage has checkpoint
        has_checkpoint = any(step.checkpoint is not None for step in stage_steps)

        stage = ExecutionStage(
            name=f"Stage {level_idx + 1}: {infer_stage_name(stage_steps)}",
            description=generate_stage_description(stage_steps),
            steps=stage_steps,
            strategy=strategy,
            checkpoint=has_checkpoint,
            required=all(
                step.priority in [AgentPriority.CRITICAL, AgentPriority.HIGH]
                for step in stage_steps
            ),
        )
        stages.append(stage)

    return stages


def infer_stage_name(steps: List[SOPStep]) -> str:
    """Infer human-readable stage name from steps."""
    roles = list(set(step.role for step in steps))
    if len(roles) == 1:
        return f"{roles[0].title()} Phase"
    return "Multi-Agent Phase"


def generate_stage_description(steps: List[SOPStep]) -> str:
    """Generate description for stage."""
    if len(steps) == 1:
        return steps[0].objective
    return f"Parallel execution of {len(steps)} tasks: {', '.join(s.action[:30] for s in steps)}"


def assess_risk(sops: List[SOPStep]) -> str:
    """
    Assess overall plan risk level.

    Considers:
    - Number of critical steps
    - Presence of security-related steps
    - Total execution cost
    """
    critical_count = sum(1 for s in sops if s.priority == AgentPriority.CRITICAL)
    has_security = any("security" in s.role.lower() for s in sops)
    total_cost = sum(s.cost for s in sops)

    if critical_count > 5 or not has_security or total_cost > 50:
        return "HIGH"
    elif critical_count > 2 or total_cost > 20:
        return "MEDIUM"
    else:
        return "LOW"


def generate_rollback_strategy(stages: List[ExecutionStage], sops: List[SOPStep]) -> str:
    """Generate comprehensive rollback strategy."""
    checkpoints = [stage.name for stage in stages if stage.checkpoint]

    if not checkpoints:
        return "Full rollback to initial state if any step fails."

    strategy_parts = [
        "Staged rollback strategy:",
        f"- Checkpoints at: {', '.join(checkpoints)}",
        "- On failure: Restore to last successful checkpoint",
        "- Critical steps have automatic retry (max 3 attempts)",
        "- All changes tracked for point-in-time recovery",
    ]

    return "\n".join(strategy_parts)


def identify_checkpoints(stages: List[ExecutionStage]) -> List[str]:
    """Identify checkpoint stages."""
    return [stage.name for stage in stages if stage.checkpoint]


def estimate_duration(
    sops: List[SOPStep], parallel_groups: List[List[str]], dependency_analyzer: "DependencyAnalyzer"
) -> str:
    """
    Estimate total execution time accounting for parallelism.

    Uses critical path analysis for accurate duration estimation.
    """
    # Sum of critical path (longest sequential chain)
    critical_path = dependency_analyzer.find_critical_path(sops)
    sop_map = {s.id: s for s in sops}

    total_cost = sum(sop_map[sid].cost for sid in critical_path if sid in sop_map)

    # Convert cost to time (rough heuristic: 1 cost = 5 minutes)
    minutes = int(total_cost * 5)

    if minutes < 10:
        return "< 10 minutes"
    elif minutes < 30:
        return "10-30 minutes"
    elif minutes < 60:
        return "30-60 minutes"
    elif minutes < 120:
        return "1-2 hours"
    else:
        return f"~{minutes // 60} hours"


def calculate_max_parallel(parallel_groups: List[List[str]]) -> int:
    """Calculate maximum parallel agents needed."""
    if not parallel_groups:
        return 1
    return max(len(group) for group in parallel_groups)


def generate_strategy_overview(stages: List[ExecutionStage]) -> str:
    """Generate high-level strategy description."""
    parallel_stages = sum(1 for s in stages if s.strategy == ExecutionStrategy.PARALLEL)
    total_stages = len(stages)

    overview_parts = [
        f"Multi-stage execution plan with {total_stages} stages.",
    ]

    if parallel_stages > 0:
        overview_parts.append(f"{parallel_stages} stages use parallel execution for efficiency.")

    overview_parts.append("Each stage has clear success criteria and rollback capability.")

    return " ".join(overview_parts)


def generate_reasoning(plan: ExecutionPlan) -> str:
    """Generate human-readable reasoning about the plan."""
    parts = [
        f"Generated {len(plan.sops)}-step plan across {len(plan.stages)} stages.",
        f"Risk level: {plan.risk_assessment}.",
        f"Estimated duration: {plan.estimated_duration}.",
    ]

    if plan.parallel_execution_opportunities:
        max_parallel = max(len(g) for g in plan.parallel_execution_opportunities)
        parts.append(f"Detected {max_parallel}-way parallelism opportunities.")

    if plan.metadata.get("goap_used"):
        parts.append("Used GOAP (Goal-Oriented Action Planning) for optimal path finding.")
    else:
        parts.append("Used LLM-based planning (GOAP unavailable).")

    return " ".join(parts)


__all__ = [
    "build_stages",
    "infer_stage_name",
    "generate_stage_description",
    "assess_risk",
    "generate_rollback_strategy",
    "identify_checkpoints",
    "estimate_duration",
    "calculate_max_parallel",
    "generate_strategy_overview",
    "generate_reasoning",
]
