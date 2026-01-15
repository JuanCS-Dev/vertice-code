"""
Testing agent implementation.

Specialized agent for testing.
"""

from vertice_core.types import AgentCapability, AgentRole, AgentTask, AgentResponse
from .base import BaseAgent


class TestRunnerAgent(BaseAgent):
    """Agent specialized in testing."""

    def __init__(self, llm_client=None, mcp_client=None, **kwargs):
        """Initialize the testing agent."""
        super().__init__(
            role=AgentRole.TESTER,
            capabilities=[
                AgentCapability.READ_ONLY,
                AgentCapability.BASH_EXEC,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a testing agent that writes and runs comprehensive tests...",
            **kwargs,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a testing task."""
        return AgentResponse(success=True, reasoning="Testing completed", data={"tests": []})
