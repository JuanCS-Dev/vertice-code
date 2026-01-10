"""
Unit tests for MCP Server tools

This module provides basic unit tests to achieve minimum test coverage
requirements as specified in CODE_CONSTITUTION.md.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from prometheus.mcp_server.tools.base import ToolResult
from prometheus.mcp_server.tools.registry import get_tool_registry


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_registry_initialization(self):
        """Test that tool registry initializes properly."""
        registry = get_tool_registry()
        assert registry is not None
        assert hasattr(registry, "get_tool_count")
        assert hasattr(registry, "get_tool_names")
        assert hasattr(registry, "get_categories")

    def test_registry_has_tools(self):
        """Test that registry contains tools after setup."""
        from vertice_cli.tools.registry_setup import setup_default_tools

        registry, _ = setup_default_tools()
        tool_count = len(registry.tools)
        assert tool_count > 0, "Registry should contain tools"
        assert tool_count >= 10, f"Expected at least 10 tools, got {tool_count}"

    def test_registry_categories(self):
        """Test that registry has expected categories."""
        registry = get_tool_registry()
        categories = registry.get_categories()

        # Check that some categories exist
        if len(categories) > 0:
            # If registry has categories, ensure they're valid strings
            for category in categories:
                assert isinstance(category, str), f"Category should be string, got {type(category)}"
                assert len(category) > 0, "Category should not be empty"
        else:
            # Registry may be empty, that's acceptable for this test
            pass

    def test_registry_tool_names(self):
        """Test that registry contains expected tool names."""
        registry = get_tool_registry()
        tool_names = registry.get_tool_names()

        # Check that tool names are valid strings
        for tool_name in tool_names:
            assert isinstance(tool_name, str), f"Tool name should be string, got {type(tool_name)}"
            assert len(tool_name) > 0, "Tool name should not be empty"


class TestToolResult:
    """Test ToolResult class."""

    def test_success_result(self):
        """Test successful tool result creation."""
        result = ToolResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.metadata == {}

    def test_error_result(self):
        """Test error tool result creation."""
        result = ToolResult(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"
        assert result.data is None
        assert result.metadata == {}

    def test_result_with_metadata(self):
        """Test tool result with metadata."""
        metadata = {"timestamp": "2024-01-01", "duration": 1.5}
        result = ToolResult(success=True, data={"result": "ok"}, metadata=metadata)
        assert result.success is True
        assert result.metadata == metadata


class TestPrometheusTools:
    """Test prometheus tools functionality."""

    @pytest.mark.asyncio
    async def test_prometheus_execute_requires_provider(self):
        """Test that prometheus_execute fails without provider."""
        from prometheus.mcp_server.tools.prometheus_tools import prometheus_execute

        result = await prometheus_execute("test task")
        assert result.success is False
        assert "provider not initialized" in result.error.lower()

    @pytest.mark.asyncio
    async def test_prometheus_memory_query_requires_provider(self):
        """Test that prometheus_memory_query fails without provider."""
        from prometheus.mcp_server.tools.prometheus_tools import prometheus_memory_query

        result = await prometheus_memory_query("test query")
        assert result.success is False
        assert "provider not initialized" in result.error.lower()

    @pytest.mark.asyncio
    async def test_prometheus_simulate_requires_provider(self):
        """Test that prometheus_simulate fails without provider."""
        from prometheus.mcp_server.tools.prometheus_tools import prometheus_simulate

        result = await prometheus_simulate("test plan")
        assert result.success is False
        assert "provider not initialized" in result.error.lower()


class TestMultiEditTools:
    """Test multi-edit tools functionality."""

    def test_multi_edit_validates_inputs(self):
        """Test that multi_edit validates required inputs."""
        from prometheus.mcp_server.tools.multi_edit_tools import multi_edit
        import asyncio

        async def run_test():
            # Test missing file_path
            result = multi_edit("", [])
            assert result.success is False
            assert "file_path is required" in result.error

            # Test missing edits
            result = multi_edit("/tmp/test.txt", [])
            assert result.success is False
            assert "edits list is required" in result.error

        asyncio.run(run_test())

    @pytest.mark.asyncio
    async def test_task_launcher_basic(self):
        """Test basic task launcher functionality."""
        from prometheus.mcp_server.tools.multi_edit_tools import task_launcher

        result = task_launcher("test task", "high")
        assert result.success is True
        assert result.data["task_description"] == "test task"
        assert result.data["priority"] == "high"
        assert "task_id" in result.data


class TestPlanModeTools:
    """Test plan mode tools functionality."""

    @pytest.mark.asyncio
    async def test_enter_plan_mode(self):
        """Test entering plan mode."""
        from prometheus.mcp_server.tools.plan_mode_tools import enter_plan_mode

        result = enter_plan_mode("Test planning task")
        assert result.success is True
        assert "plan_mode_active" in result.data["status"]
        assert result.data["status"] == "plan_mode_active"
        assert result.metadata["task_description"] == "Test planning task"

    @pytest.mark.asyncio
    async def test_get_plan_status_not_active(self):
        """Test getting plan status when not active."""
        from prometheus.mcp_server.tools.plan_mode_tools import get_plan_status

        result = get_plan_status()
        assert result.success is True
        assert result.data["active"] is False
        assert result.data["message"] == "Not in plan mode"
        assert result.data["active"] is False

    @pytest.mark.asyncio
    async def test_add_plan_note_without_plan_mode(self):
        """Test adding plan note without active plan mode."""
        from prometheus.mcp_server.tools.plan_mode_tools import add_plan_note

        result = await add_plan_note("test note")
        assert result.success is False
        assert "not in plan mode" in result.error.lower()


class TestAgentTools:
    """Test agent tools functionality."""

    @pytest.mark.asyncio
    async def test_agent_tools_placeholder_responses(self):
        """Test that agent tools return placeholder responses."""
        from prometheus.mcp_server.tools.agent_tools import (
            execute_with_architect,
            execute_with_executor,
            execute_with_reviewer,
        )

        # Test architect agent
        result = await execute_with_architect("test task")
        assert result.success is True
        assert "placeholder" in result.data["status"]
        assert "architect" in result.data["agent"]

        # Test executor agent
        result = await execute_with_executor("test task")
        assert result.success is True
        assert "placeholder" in result.data["status"]
        assert "executor" in result.data["agent"]

        # Test reviewer agent
        result = await execute_with_reviewer("test task")
        assert result.success is True
        assert "placeholder" in result.data["status"]
        assert "reviewer" in result.data["agent"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
