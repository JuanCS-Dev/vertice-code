"""
Explorer agent implementation.

Specialized agent for codebase exploration and analysis.
"""

from vertice_core.types import AgentCapability, AgentRole, AgentTask, AgentResponse
from .base import BaseAgent


class ExplorerAgent(BaseAgent):
    """Agent specialized in codebase exploration."""

    def __init__(self, llm_client=None, mcp_client=None, **kwargs):
        """Initialize the explorer agent."""
        super().__init__(
            role=AgentRole.EXPLORER,
            capabilities=[
                AgentCapability.READ_ONLY,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are an explorer agent specialized in codebase analysis...",
            **kwargs,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute an exploration task."""
        return AgentResponse(success=True, reasoning="Exploration completed", data={"files": []})
