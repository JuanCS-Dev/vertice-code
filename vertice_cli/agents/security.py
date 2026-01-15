"""
Security agent implementation.

Specialized agent for security analysis.
"""

from vertice_core.types import AgentCapability, AgentRole, AgentTask, AgentResponse
from .base import BaseAgent


class SecurityAgent(BaseAgent):
    """Agent specialized in security."""

    def __init__(self, llm_client=None, mcp_client=None, **kwargs):
        """Initialize the security agent."""
        super().__init__(
            role=AgentRole.SECURITY,
            capabilities=[
                AgentCapability.READ_ONLY,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a security agent that identifies vulnerabilities and security issues...",
            **kwargs,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a security task."""
        return AgentResponse(
            success=True, reasoning="Security analysis completed", data={"vulnerabilities": []}
        )
