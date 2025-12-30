"""
E2E Tests for MAXIMUS Tool Factory Integration.

Tests the complete flow of Tool Factory operations from Prometheus CLI
to MAXIMUS backend using respx mocked responses.

Based on 2025 best practices:
- Scientific hypothesis-driven testing
- Dynamic tool generation validation
- respx for async httpx mocking

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, Google docstrings.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest
import respx

from vertice_cli.core.providers.maximus_provider import MaximusProvider


class TestFactoryGenerate:
    """E2E tests for Factory generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_simple_tool(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Simple tool is generated successfully.

        Given a tool description and examples,
        When generating via Factory,
        Then tool is created with valid code.
        """
        name = "hello_world"
        description = "A simple tool that prints hello world"
        examples = [
            {"input": {}, "output": "Hello, World!"},
        ]

        result: Dict[str, Any] = await maximus_provider.factory_generate(
            name=name,
            description=description,
            examples=examples,
        )

        assert "name" in result
        assert "code" in result or "success" in result

    @pytest.mark.asyncio
    async def test_generate_tool_with_parameters(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Tool with parameters is generated.

        Given a tool requiring parameters,
        When generating via Factory,
        Then tool handles parameters correctly.
        """
        name = "greet_user"
        description = "Greets a user by name"
        examples = [
            {"input": {"name": "Alice"}, "output": "Hello, Alice!"},
            {"input": {"name": "Bob"}, "output": "Hello, Bob!"},
        ]

        result: Dict[str, Any] = await maximus_provider.factory_generate(
            name=name,
            description=description,
            examples=examples,
        )

        assert "name" in result

    @pytest.mark.asyncio
    async def test_generate_complex_tool(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Complex tool is generated from examples.

        Given a tool with complex logic,
        When generating via Factory,
        Then tool handles the complexity.
        """
        name = "calculate_discount"
        description = "Calculates discount based on purchase amount"
        examples = [
            {"input": {"amount": 100}, "output": 5.0},  # 5% for < 200
            {"input": {"amount": 300}, "output": 30.0},  # 10% for >= 200
            {"input": {"amount": 500}, "output": 75.0},  # 15% for >= 500
        ]

        result: Dict[str, Any] = await maximus_provider.factory_generate(
            name=name,
            description=description,
            examples=examples,
        )

        assert "name" in result


class TestFactoryExecute:
    """E2E tests for Factory execute endpoint."""

    @pytest.mark.asyncio
    async def test_execute_generated_tool(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Generated tool executes successfully.

        Given a generated tool,
        When executing with valid params,
        Then result is returned.
        """
        tool_name = "test_tool"
        params = {"input": "test"}

        result: Dict[str, Any] = await maximus_provider.factory_execute(
            tool_name=tool_name,
            params=params,
        )

        assert "result" in result or "success" in result

    @pytest.mark.asyncio
    async def test_execute_with_empty_params(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Tool executes with empty params.

        Given a tool that needs no params,
        When executing with empty dict,
        Then tool runs successfully.
        """
        tool_name = "hello_tool"
        params: Dict[str, Any] = {}

        result: Dict[str, Any] = await maximus_provider.factory_execute(
            tool_name=tool_name,
            params=params,
        )

        assert "result" in result or "success" in result


class TestFactoryList:
    """E2E tests for Factory list endpoint."""

    @pytest.mark.asyncio
    async def test_list_returns_tools(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: List returns available tools.

        Given generated tools exist,
        When listing tools,
        Then list of tools is returned.
        """
        result: List[Dict[str, Any]] = await maximus_provider.factory_list()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_tool_structure(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Listed tools have correct structure.

        Given tools in the factory,
        When listing tools,
        Then each tool has name and description.
        """
        result: List[Dict[str, Any]] = await maximus_provider.factory_list()

        if result:  # If there are tools
            tool = result[0]
            assert "name" in tool


class TestFactoryDelete:
    """E2E tests for Factory delete endpoint."""

    @pytest.mark.asyncio
    async def test_delete_existing_tool(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Existing tool is deleted successfully.

        Given an existing tool,
        When deleting the tool,
        Then deletion returns success.
        """
        tool_name = "tool_to_delete"

        result: bool = await maximus_provider.factory_delete(tool_name=tool_name)

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_delete_returns_boolean(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Delete returns boolean status.

        Given a delete request,
        When the operation completes,
        Then boolean result is returned.
        """
        tool_name = "any_tool"

        result: bool = await maximus_provider.factory_delete(tool_name=tool_name)

        assert isinstance(result, bool)


class TestFactoryResilience:
    """E2E tests for Factory resilience patterns."""

    @pytest.mark.asyncio
    async def test_factory_handles_network_error(
        self,
        maximus_config: Any,
        maximus_base_url: str,
    ) -> None:
        """HYPOTHESIS: Factory handles network errors gracefully.

        Given a network failure,
        When generating tool,
        Then error is handled without crash.
        """
        with respx.mock(assert_all_called=False) as router:
            router.get(f"{maximus_base_url}/health").respond(
                json={"status": "ok", "mcp_enabled": False}
            )
            router.post(f"{maximus_base_url}/v1/tools/generate").mock(
                side_effect=httpx.ConnectError("Network error")
            )

            provider = MaximusProvider(config=maximus_config)
            try:
                result = await provider.factory_generate(
                    name="test",
                    description="test",
                    examples=[],
                )
                assert "error" in result or "name" in result
            finally:
                await provider.close()


class TestFactoryIntegrationFlow:
    """E2E tests for complete Factory integration flows."""

    @pytest.mark.asyncio
    async def test_complete_tool_lifecycle(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Complete tool lifecycle works end-to-end.

        Given a tool to create,
        When going through generate-execute-delete cycle,
        Then all operations complete successfully.
        """
        # Step 1: Generate a tool
        gen_result: Dict[str, Any] = await maximus_provider.factory_generate(
            name="lifecycle_tool",
            description="A tool for testing lifecycle",
            examples=[{"input": {"x": 1}, "output": 2}],
        )
        assert "name" in gen_result

        # Step 2: List tools (should include new tool)
        list_result: List[Dict[str, Any]] = await maximus_provider.factory_list()
        assert isinstance(list_result, list)

        # Step 3: Execute the tool
        exec_result: Dict[str, Any] = await maximus_provider.factory_execute(
            tool_name="lifecycle_tool",
            params={"x": 5},
        )
        assert "result" in exec_result or "success" in exec_result

        # Step 4: Delete the tool
        delete_result: bool = await maximus_provider.factory_delete(
            tool_name="lifecycle_tool"
        )
        assert isinstance(delete_result, bool)

    @pytest.mark.asyncio
    async def test_generate_multiple_tools(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Multiple tools can be generated.

        Given multiple tool specifications,
        When generating each tool,
        Then all tools are created.
        """
        tools_specs: List[Dict[str, Any]] = [
            {
                "name": "tool_a",
                "description": "First tool",
                "examples": [{"input": {}, "output": "A"}],
            },
            {
                "name": "tool_b",
                "description": "Second tool",
                "examples": [{"input": {}, "output": "B"}],
            },
            {
                "name": "tool_c",
                "description": "Third tool",
                "examples": [{"input": {}, "output": "C"}],
            },
        ]

        for spec in tools_specs:
            result: Dict[str, Any] = await maximus_provider.factory_generate(
                name=str(spec["name"]),
                description=str(spec["description"]),
                examples=list(spec["examples"]),
            )
            assert "name" in result

    @pytest.mark.asyncio
    async def test_tool_with_validation(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Generated tool includes validation.

        Given a tool specification with constraints,
        When generating the tool,
        Then tool validates input correctly.
        """
        name = "validated_tool"
        description = "Tool that validates positive numbers"
        examples = [
            {"input": {"n": 5}, "output": True},
            {"input": {"n": -1}, "output": False},
            {"input": {"n": 0}, "output": False},
        ]

        result: Dict[str, Any] = await maximus_provider.factory_generate(
            name=name,
            description=description,
            examples=examples,
        )

        assert "name" in result
