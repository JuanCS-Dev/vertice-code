"""
Planner Exploration - Read-Only Analysis Mode (v6.0).

This module provides exploration mode for read-only analysis.
Like Claude Code's Plan Mode, this gathers context and analyzes
the task without making any modifications.

Philosophy:
    "Understand before you act."
"""

from typing import TYPE_CHECKING

from ..base import AgentCapability, AgentResponse
from .types import PlanningMode
from .prompts import build_exploration_prompt
from .utils import robust_json_parse

if TYPE_CHECKING:
    from ..base import AgentTask
    from .agent import PlannerAgent


async def explore(agent: "PlannerAgent", task: "AgentTask") -> AgentResponse:
    """
    Execute in exploration mode - read-only analysis.

    Like Claude Code's Plan Mode, this gathers context and analyzes
    the task without making any modifications.

    Use this before execute() to understand the problem space.

    Args:
        agent: The PlannerAgent instance
        task: The task to explore

    Returns:
        AgentResponse with analysis results
    """
    agent.current_mode = PlanningMode.EXPLORATION

    # Restrict to read-only operations
    original_capabilities = agent.capabilities.copy()
    agent.capabilities = [AgentCapability.READ_ONLY]

    try:
        # Gather context
        context = await agent._gather_context(task)

        # Analyze task requirements
        analysis_prompt = build_exploration_prompt(task.request, context)
        response = await agent._call_llm(analysis_prompt)
        analysis = robust_json_parse(response)

        return AgentResponse(
            success=True,
            data={
                "mode": "exploration",
                "analysis": analysis or {"raw": response},
                "context": context,
            },
            reasoning="Exploration complete. Ready for planning phase.",
            metadata={"mode": PlanningMode.EXPLORATION.value},
        )

    finally:
        # Restore capabilities
        agent.capabilities = original_capabilities
        agent.current_mode = PlanningMode.PLANNING


__all__ = ["explore"]
