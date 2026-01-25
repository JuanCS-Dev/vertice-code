"""
Tests for Unified Agent System.

Tests the simple Agent class following 2025 standards:
- Agent creation and configuration
- Tool schema generation (multi-provider)
- Handoff definitions
- Agent cloning

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

from typing import Any

import pytest

from core.agents import Agent, AgentConfig, Handoff
from vertice_core.tools.base import Tool, ToolResult


# =============================================================================
# TEST FIXTURES
# =============================================================================


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.description = "Mock tool for testing"
        self.parameters = {
            "query": {"type": "string", "description": "Query", "required": True},
        }

    async def _execute_validated(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data="mock result")


def mock_function(name: str, count: int = 10) -> str:
    """A mock function tool.

    Args:
        name: The name parameter
        count: Optional count
    """
    return f"{name}: {count}"


# =============================================================================
# AGENT CREATION TESTS
# =============================================================================


class TestAgentCreation:
    """Tests for Agent creation."""

    def test_minimal_agent(self) -> None:
        """Agent with only name is valid."""
        agent = Agent(name="test")

        assert agent.name == "test"
        assert agent.instructions == ""
        assert agent.tools == []
        assert agent.handoffs == []

    def test_full_agent(self) -> None:
        """Agent with all fields."""
        agent = Agent(
            name="coder",
            instructions="You write code",
            tools=[MockTool()],
            handoffs=[Handoff(target="reviewer")],
            config=AgentConfig(max_turns=5),
        )

        assert agent.name == "coder"
        assert agent.instructions == "You write code"
        assert len(agent.tools) == 1
        assert len(agent.handoffs) == 1
        assert agent.config.max_turns == 5

    def test_empty_name_raises(self) -> None:
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="name is required"):
            Agent(name="")


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_default_config(self) -> None:
        """Default config has sensible values."""
        config = AgentConfig()

        assert config.max_turns == 10
        assert config.tool_timeout == 30.0
        assert config.enable_tracing is True

    def test_custom_config(self) -> None:
        """Custom config values."""
        config = AgentConfig(max_turns=5, tool_timeout=60.0, enable_tracing=False)

        assert config.max_turns == 5
        assert config.tool_timeout == 60.0
        assert config.enable_tracing is False


# =============================================================================
# TOOL SCHEMA TESTS
# =============================================================================


class TestToolSchemas:
    """Tests for tool schema generation."""

    def test_anthropic_schema(self) -> None:
        """Anthropic format is default."""
        agent = Agent(name="test", tools=[MockTool()])
        schemas = agent.get_tool_schemas()

        assert len(schemas) == 1
        assert schemas[0]["strict"] is True
        assert "input_schema" in schemas[0]

    def test_openai_schema(self) -> None:
        """OpenAI format has function wrapper."""
        agent = Agent(name="test", tools=[MockTool()])
        schemas = agent.get_tool_schemas(provider="openai")

        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert "function" in schemas[0]

    def test_gemini_schema(self) -> None:
        """Gemini format has parameters."""
        agent = Agent(name="test", tools=[MockTool()])
        schemas = agent.get_tool_schemas(provider="gemini")

        assert len(schemas) == 1
        assert "parameters" in schemas[0]
        assert "input_schema" not in schemas[0]

    def test_function_tool_schema(self) -> None:
        """Function tools generate schema from signature."""
        agent = Agent(name="test", tools=[mock_function])
        schemas = agent.get_tool_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "mock_function"
        props = schemas[0]["input_schema"]["properties"]
        assert "name" in props
        assert "count" in props

    def test_function_required_params(self) -> None:
        """Required params extracted from function signature."""
        agent = Agent(name="test", tools=[mock_function])
        schemas = agent.get_tool_schemas()

        required = schemas[0]["input_schema"]["required"]
        assert "name" in required  # No default
        assert "count" not in required  # Has default


# =============================================================================
# HANDOFF TESTS
# =============================================================================


class TestHandoff:
    """Tests for Handoff class."""

    def test_handoff_with_string_target(self) -> None:
        """Handoff with string target."""
        handoff = Handoff(target="reviewer")

        assert handoff.target_name == "reviewer"

    def test_handoff_with_agent_target(self) -> None:
        """Handoff with Agent target."""
        target = Agent(name="reviewer")
        handoff = Handoff(target=target)

        assert handoff.target_name == "reviewer"

    def test_handoff_schema(self) -> None:
        """Handoff generates tool schema."""
        agent = Agent(
            name="test",
            handoffs=[Handoff(target="reviewer", description="For review")],
        )
        schemas = agent.get_handoff_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "transfer_to_reviewer"
        assert schemas[0]["description"] == "For review"

    def test_all_schemas_combines(self) -> None:
        """get_all_schemas combines tools and handoffs."""
        agent = Agent(
            name="test",
            tools=[MockTool()],
            handoffs=[Handoff(target="reviewer")],
        )
        schemas = agent.get_all_schemas()

        assert len(schemas) == 2
        names = [s["name"] for s in schemas]
        assert "mock" in names
        assert "transfer_to_reviewer" in names


# =============================================================================
# FIND METHODS TESTS
# =============================================================================


class TestFindMethods:
    """Tests for find_tool and find_handoff."""

    def test_find_tool_by_name(self) -> None:
        """Find tool by name."""
        agent = Agent(name="test", tools=[MockTool()])
        found = agent.find_tool("mock")

        assert found is not None
        assert found.name == "mock"

    def test_find_function_tool(self) -> None:
        """Find function tool by name."""
        agent = Agent(name="test", tools=[mock_function])
        found = agent.find_tool("mock_function")

        assert found is not None
        assert found == mock_function

    def test_find_tool_not_found(self) -> None:
        """Find returns None if not found."""
        agent = Agent(name="test", tools=[MockTool()])
        found = agent.find_tool("nonexistent")

        assert found is None

    def test_find_handoff(self) -> None:
        """Find handoff by target name."""
        agent = Agent(name="test", handoffs=[Handoff(target="reviewer")])
        found = agent.find_handoff("reviewer")

        assert found is not None
        assert found.target_name == "reviewer"

    def test_find_handoff_with_prefix(self) -> None:
        """Find handoff with transfer_to_ prefix."""
        agent = Agent(name="test", handoffs=[Handoff(target="reviewer")])
        found = agent.find_handoff("transfer_to_reviewer")

        assert found is not None
        assert found.target_name == "reviewer"


# =============================================================================
# CLONE TESTS
# =============================================================================


class TestAgentClone:
    """Tests for agent cloning."""

    def test_clone_preserves_values(self) -> None:
        """Clone preserves all values."""
        original = Agent(
            name="coder",
            instructions="Write code",
            tools=[MockTool()],
        )
        clone = original.clone()

        assert clone.name == "coder"
        assert clone.instructions == "Write code"
        assert len(clone.tools) == 1

    def test_clone_with_overrides(self) -> None:
        """Clone with overrides."""
        original = Agent(name="coder", instructions="Write code")
        clone = original.clone(name="coder_v2", instructions="Better code")

        assert clone.name == "coder_v2"
        assert clone.instructions == "Better code"
        assert original.name == "coder"  # Original unchanged

    def test_clone_tools_independent(self) -> None:
        """Cloned tools list is independent."""
        original = Agent(name="test", tools=[MockTool()])
        clone = original.clone()

        clone.tools.append(mock_function)

        assert len(clone.tools) == 2
        assert len(original.tools) == 1
