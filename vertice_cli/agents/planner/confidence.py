"""
planner/confidence.py: Confidence Calculation (v6.0 Devin Pattern).

Pure functions for calculating confidence scores for planning steps.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .types import AgentPriority
from .models import SOPStep


def calculate_step_confidence(
    step: SOPStep, context: Dict[str, Any]
) -> Tuple[float, str, List[str]]:
    """
    Calculate confidence score for a planning step.

    Factors:
    - Role familiarity (how common is this operation)
    - Dependency complexity (more deps = lower confidence)
    - Cost (higher cost = more complex = lower confidence)
    - Priority (critical steps get extra scrutiny)

    Args:
        step: The SOPStep to evaluate
        context: Planning context

    Returns:
        Tuple of (score, reasoning, risk_factors)
    """
    score = 0.8  # Base confidence
    reasoning_parts: List[str] = []
    risks: List[str] = []

    # Factor 1: Role familiarity
    familiar_roles = {"architect", "coder", "tester", "reviewer", "documenter"}
    if step.role.lower() in familiar_roles:
        score += 0.05
        reasoning_parts.append("familiar role")
    else:
        score -= 0.1
        risks.append(f"Unfamiliar role: {step.role}")

    # Factor 2: Dependency complexity
    dep_count = len(step.dependencies)
    if dep_count == 0:
        score += 0.05
        reasoning_parts.append("no dependencies")
    elif dep_count <= 2:
        pass  # Neutral
    else:
        score -= 0.05 * (dep_count - 2)
        risks.append(f"High dependency count: {dep_count}")

    # Factor 3: Cost/complexity
    if step.cost <= 1.0:
        score += 0.05
        reasoning_parts.append("low complexity")
    elif step.cost <= 3.0:
        pass  # Neutral
    else:
        score -= 0.1
        risks.append(f"High complexity (cost={step.cost})")

    # Factor 4: Priority risk
    if step.priority == AgentPriority.CRITICAL:
        score -= 0.05
        risks.append("Critical priority increases risk exposure")

    # Clamp score
    score = max(0.1, min(1.0, score))

    reasoning = (
        f"Confidence {score:.2f}: " + ", ".join(reasoning_parts)
        if reasoning_parts
        else f"Base confidence: {score:.2f}"
    )

    return score, reasoning, risks


def calculate_plan_confidence(steps: List[SOPStep], context: Dict[str, Any]) -> float:
    """
    Calculate overall plan confidence from step confidences.

    Returns weighted average of step confidences.
    """
    if not steps:
        return 0.7  # Default confidence

    total_score = 0.0
    total_weight = 0.0

    for step in steps:
        score, _, _ = calculate_step_confidence(step, context)
        # Weight by cost (more expensive steps matter more)
        weight = step.cost
        total_score += score * weight
        total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0.7


__all__ = [
    "calculate_step_confidence",
    "calculate_plan_confidence",
]
