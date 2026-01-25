"""
Planner Compatibility - Backwards Compatibility Wrappers.

This module provides backwards-compatible method wrappers that delegate
to the modular subpackages. These ensure API stability while allowing
internal refactoring.

Philosophy:
    "Backwards compatibility is a promise to your users."
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SOPStep, ExecutionStage
    from .types import AlternativePlan, PlanStrategy
    from ..base import AgentTask


def calculate_step_confidence_compat(
    step: "SOPStep", context: Dict[str, Any]
) -> Tuple[float, str, List[str]]:
    """Backwards compatibility wrapper for calculate_step_confidence."""
    from .confidence import calculate_step_confidence

    return calculate_step_confidence(step, context)


def generate_confidence_summary_compat(score: float) -> str:
    """Backwards compatibility wrapper for generate_confidence_summary."""
    from .formatting import generate_confidence_summary

    return generate_confidence_summary(score)


def format_plan_as_markdown_compat(plan_data: Dict[str, Any], task: "AgentTask") -> str:
    """Backwards compatibility wrapper for format_plan_as_markdown."""
    from .formatting import format_plan_as_markdown

    return format_plan_as_markdown(plan_data, task)


def create_fallback_plan_compat(task: "AgentTask", strategy: "PlanStrategy") -> "AlternativePlan":
    """Backwards compatibility wrapper for create_fallback_plan."""
    from .multi_planning import create_fallback_plan

    return create_fallback_plan(task, strategy)


def select_best_plan_compat(
    plans: List["AlternativePlan"], task: Optional["AgentTask"] = None
) -> Tuple["PlanStrategy", str]:
    """Backwards compatibility wrapper for select_best_plan."""
    from .multi_planning import select_best_plan

    return select_best_plan(plans)


def build_comparison_summary_compat(plans: List["AlternativePlan"]) -> str:
    """Backwards compatibility wrapper for build_comparison_summary."""
    from .multi_planning import build_comparison_summary

    return build_comparison_summary(plans)


def infer_stage_name_compat(steps: List["SOPStep"]) -> str:
    """Backwards compatibility wrapper for infer_stage_name."""
    from .optimization import infer_stage_name

    return infer_stage_name(steps)


def assess_risk_compat(sops: List["SOPStep"]) -> str:
    """Backwards compatibility wrapper for assess_risk."""
    from .optimization import assess_risk

    return assess_risk(sops)


def generate_stage_description_compat(steps: List["SOPStep"]) -> str:
    """Backwards compatibility wrapper for generate_stage_description."""
    from .optimization import generate_stage_description

    return generate_stage_description(steps)


def calculate_max_parallel_compat(stages: List["ExecutionStage"]) -> int:
    """Backwards compatibility wrapper for calculate_max_parallel."""
    from .optimization import calculate_max_parallel

    return calculate_max_parallel(stages)


def generate_strategy_overview_compat(stages: List["ExecutionStage"]) -> str:
    """Backwards compatibility wrapper for generate_strategy_overview."""
    from .optimization import generate_strategy_overview

    return generate_strategy_overview(stages)


def estimate_duration_compat(stages: List["ExecutionStage"], base_minutes_per_step: int = 5) -> str:
    """Backwards compatibility wrapper for estimate_duration."""
    from .optimization import estimate_duration

    return estimate_duration(stages, base_minutes_per_step)


def identify_checkpoints_compat(stages: List["ExecutionStage"]) -> List[str]:
    """Backwards compatibility wrapper for identify_checkpoints."""
    from .optimization import identify_checkpoints

    return identify_checkpoints(stages)


def robust_json_parse_compat(text: str) -> Optional[Dict[str, Any]]:
    """Backwards compatibility wrapper for robust_json_parse."""
    from .utils import robust_json_parse

    return robust_json_parse(text)


__all__ = [
    "calculate_step_confidence_compat",
    "generate_confidence_summary_compat",
    "format_plan_as_markdown_compat",
    "create_fallback_plan_compat",
    "select_best_plan_compat",
    "build_comparison_summary_compat",
    "infer_stage_name_compat",
    "assess_risk_compat",
    "generate_stage_description_compat",
    "calculate_max_parallel_compat",
    "generate_strategy_overview_compat",
    "estimate_duration_compat",
    "identify_checkpoints_compat",
    "robust_json_parse_compat",
]
