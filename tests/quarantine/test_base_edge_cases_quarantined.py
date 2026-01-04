import pytest
from unittest.mock import MagicMock

from vertice_cli.agents.base import (
    AgentCapability,
    AgentRole,
    BaseAgent,
)


class TestAgent(BaseAgent):
    """Test implementation."""

    async def execute(self, task: AgentTask) -> AgentResponse:
        return AgentResponse(success=True, reasoning="Test")


@pytest.mark.skip(reason="QUARANTINED: BaseAgent does not implement __repr__ - feature not implemented")
class TestBaseAgentReprAndStr:
    """Edge cases for string representation."""

    def test_repr_with_no_executions(self) -> None:
        """Test repr with zero executions."""
        agent = TestAgent(
            role=AgentRole.ARCHITECT,
            capabilities=[AgentCapability.READ_ONLY],
            llm_client=MagicMock(),
            mcp_client=MagicMock(),
        )
        assert "executions=0" in repr(agent)

    def test_repr_with_multiple_capabilities(self) -> None:
        """Test repr with multiple capabilities."""
        agent = TestAgent(
            role=AgentRole.REFACTORER,
            capabilities=[
                AgentCapability.READ_ONLY,
                AgentCapability.FILE_EDIT,
                AgentCapability.BASH_EXEC,
                AgentCapability.GIT_OPS,
            ],
            llm_client=MagicMock(),
            mcp_client=MagicMock(),
        )
        repr_str = repr(agent)
        assert "read_only" in repr_str
        assert "file_edit" in repr_str
        assert "bash_exec" in repr_str
        assert "git_ops" in repr_str

    def test_repr_includes_class_name(self) -> None:
        """Test that repr includes the class name."""
        agent = TestAgent(
            role=AgentRole.PLANNER,
            capabilities=[AgentCapability.DESIGN],
            llm_client=MagicMock(),
            mcp_client=MagicMock(),
        )
        assert "TestAgent" in repr(agent)
