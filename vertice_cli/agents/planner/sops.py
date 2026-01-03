"""
Planner SOPs - SOP Step Generation and Conversion.

This module handles SOP (Standard Operating Procedure) step generation:
- Convert GOAP actions to SOP steps
- LLM-based planning fallback
- Basic plan generation

Philosophy:
    "Each step should be atomic, verifiable, and completable by one agent."
"""

from typing import Any, Dict, List, TYPE_CHECKING

from .models import SOPStep
from .goap import Action
from .prompts import build_planning_prompt, generate_basic_plan
from .utils import robust_json_parse

if TYPE_CHECKING:
    from ..base import AgentTask
    from .agent import PlannerAgent


def actions_to_sops(actions: List[Action]) -> List[SOPStep]:
    """Convert GOAP actions to SOP steps.

    Args:
        actions: List of GOAP actions

    Returns:
        List of SOP steps with dependencies
    """
    sops = []

    for idx, action in enumerate(actions):
        # Find dependencies (actions whose effects match our preconditions)
        deps = []
        for prev_idx, prev_action in enumerate(actions[:idx]):
            # Check if previous action's effects satisfy our preconditions
            if any(
                key in prev_action.effects and
                prev_action.effects[key] == value
                for key, value in action.preconditions.items()
            ):
                deps.append(f"step-{prev_idx}")

        sop = SOPStep(
            id=f"step-{idx}",
            role=action.agent_role,
            action=action.description,
            objective=f"Execute {action.id}",
            definition_of_done=f"Action {action.id} completed successfully",
            preconditions=action.preconditions,
            effects=action.effects,
            cost=action.cost,
            dependencies=deps,
            context_isolation=True,
            max_tokens=4000,
            correlation_id=f"action-{action.id}"
        )
        sops.append(sop)

    return sops


async def llm_planning_fallback(
    agent: "PlannerAgent",
    task: "AgentTask",
    context: Dict[str, Any],
    agents: List[str]
) -> List[SOPStep]:
    """Fallback to LLM planning if GOAP fails.

    Args:
        agent: The PlannerAgent instance
        task: The task to plan
        context: Current context
        agents: Available agents

    Returns:
        List of SOP steps
    """
    prompt = build_planning_prompt(task.request, context, agents)
    raw_response = await agent._call_llm(prompt)

    # Parse and validate
    plan_data = robust_json_parse(raw_response)

    if plan_data and "sops" in plan_data:
        return [SOPStep(**sop) for sop in plan_data["sops"]]

    # Emergency fallback: basic sequential plan
    return generate_basic_plan(agents)


__all__ = [
    "actions_to_sops",
    "llm_planning_fallback",
]
