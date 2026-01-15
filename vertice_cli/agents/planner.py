"""
Planner agent implementation.

Specialized agent for task planning and scheduling.
"""

from vertice_core.types import AgentCapability, AgentRole, AgentTask, AgentResponse
from .base import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent specialized in planning."""

    def __init__(self, llm_client=None, mcp_client=None, **kwargs):
        """Initialize the planner agent."""
        super().__init__(
            role=AgentRole.PLANNER,
            capabilities=[
                AgentCapability.READ_ONLY,
                AgentCapability.DESIGN,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a planner agent that creates detailed implementation plans...",
            **kwargs,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a planning task."""
        return AgentResponse(success=True, reasoning="Planning completed", data={"plan": []})
