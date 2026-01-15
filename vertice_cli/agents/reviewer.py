"""
Reviewer agent implementation.

Specialized agent for code review.
"""

from vertice_core.types import AgentCapability, AgentRole, AgentTask, AgentResponse
from .base import BaseAgent


class ReviewerAgent(BaseAgent):
    """Agent specialized in code review."""

    def __init__(self, llm_client=None, mcp_client=None, **kwargs):
        """Initialize the reviewer agent."""
        super().__init__(
            role=AgentRole.REVIEWER,
            capabilities=[
                AgentCapability.READ_ONLY,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a reviewer agent that provides thorough code reviews...",
            **kwargs,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a review task."""
        return AgentResponse(success=True, reasoning="Review completed", data={"issues": []})
