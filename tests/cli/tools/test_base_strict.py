"""
Tests for Tool Base Class - Strict Mode (2025 Standards).

Tests Anthropic structured-outputs-2025-11-13 compliance:
- strict: true at top level
- additionalProperties: false
- Multi-provider schema generation

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

from typing import Any

import pytest

from cli.tools.base import Tool, ToolResult, ToolCategory, ToolRegistry


# =============================================================================
# TEST FIXTURES
# =============================================================================


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.category = ToolCategory.SEARCH
        self.description = "Search for files"
        self.parameters = {
            "query": {"type": "string", "description": "Search query", "required": True},
            "limit": {"type": "integer", "description": "Max results", "required": False},
        }

    async def _execute_validated(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data=["file1.py", "file2.py"])


class NoParamTool(Tool):
    """Tool with no parameters."""

    def __init__(self) -> None:
        super().__init__()
        self.description = "Tool without params"
        self.parameters = {}

    async def _execute_validated(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True)


# =============================================================================
# STRICT MODE TESTS
# =============================================================================


class TestToolStrictMode:
    """Tests for Anthropic 2025 strict mode compliance."""

    def test_schema_has_strict_true(self) -> None:
        """Schema includes strict: true at top level."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema.get("strict") is True

    def test_schema_has_additional_properties_false(self) -> None:
        """Schema includes additionalProperties: false."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["input_schema"].get("additionalProperties") is False

    def test_schema_required_fields_extracted(self) -> None:
        """Required fields are properly extracted."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "query" in schema["input_schema"]["required"]
        assert "limit" not in schema["input_schema"]["required"]

    def test_schema_properties_cleaned(self) -> None:
        """Properties don't include 'required' key (goes at schema level)."""
        tool = MockTool()
        schema = tool.get_schema()

        for prop in schema["input_schema"]["properties"].values():
            assert "required" not in prop

    def test_strict_false_disables_strict_mode(self) -> None:
        """strict=False removes strict mode flags."""
        tool = MockTool()
        schema = tool.get_schema(strict=False)

        assert "strict" not in schema
        assert "additionalProperties" not in schema["input_schema"]


class TestToolSchemaStructure:
    """Tests for schema structure."""

    def test_schema_has_name(self) -> None:
        """Schema includes tool name."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["name"] == "mock"

    def test_schema_has_description(self) -> None:
        """Schema includes description."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["description"] == "Search for files"

    def test_schema_has_input_schema(self) -> None:
        """Schema includes input_schema (Anthropic format)."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "input_schema" in schema
        assert schema["input_schema"]["type"] == "object"

    def test_empty_parameters_schema(self) -> None:
        """Tool with no params has valid schema."""
        tool = NoParamTool()
        schema = tool.get_schema()

        assert schema["input_schema"]["properties"] == {}
        assert schema["input_schema"]["required"] == []


# =============================================================================
# MULTI-PROVIDER TESTS
# =============================================================================


class TestToolMultiProvider:
    """Tests for multi-provider schema generation."""

    def test_openai_schema_format(self) -> None:
        """OpenAI schema has correct structure."""
        tool = MockTool()
        schema = tool.get_schema_openai()

        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "mock"
        assert "parameters" in schema["function"]

    def test_gemini_schema_format(self) -> None:
        """Gemini schema has correct structure."""
        tool = MockTool()
        schema = tool.get_schema_gemini()

        assert schema["name"] == "mock"
        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"

    def test_all_providers_have_same_properties(self) -> None:
        """All providers have same property definitions."""
        tool = MockTool()

        anthropic = tool.get_schema()["input_schema"]["properties"]
        openai = tool.get_schema_openai()["function"]["parameters"]["properties"]
        gemini = tool.get_schema_gemini()["parameters"]["properties"]

        assert anthropic == openai == gemini


# =============================================================================
# EXAMPLES TESTS
# =============================================================================


class TestToolExamples:
    """Tests for tool examples."""

    def test_set_examples(self) -> None:
        """Examples can be set and retrieved."""
        tool = MockTool()
        examples = [
            {"input": {"query": "test"}, "output": ["result.py"]},
        ]
        tool.set_examples(examples)
        schema = tool.get_schema()

        assert schema["examples"] == examples

    def test_no_examples_by_default(self) -> None:
        """Schema has no examples by default."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "examples" not in schema


# =============================================================================
# TOOL REGISTRY TESTS
# =============================================================================


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_get(self) -> None:
        """Can register and retrieve tools."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        assert registry.get("mock") is tool

    def test_get_unknown_returns_none(self) -> None:
        """Getting unknown tool returns None."""
        registry = ToolRegistry()

        assert registry.get("unknown") is None

    def test_get_schemas_returns_strict(self) -> None:
        """get_schemas returns strict mode schemas."""
        registry = ToolRegistry()
        registry.register(MockTool())
        schemas = registry.get_schemas()

        assert len(schemas) == 1
        assert schemas[0]["strict"] is True

    def test_get_by_category(self) -> None:
        """Can filter tools by category."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(NoParamTool())

        search_tools = registry.get_by_category(ToolCategory.SEARCH)
        assert len(search_tools) == 1
        assert search_tools[0].name == "mock"


# =============================================================================
# TOOL RESULT TESTS
# =============================================================================


class TestToolResult:
    """Tests for ToolResult."""

    def test_success_result(self) -> None:
        """Success result has correct structure."""
        result = ToolResult(success=True, data="test")

        assert result.success is True
        assert result.data == "test"
        assert result.output == "test"  # Alias

    def test_error_result(self) -> None:
        """Error result has correct structure."""
        result = ToolResult(success=False, error="Failed")

        assert result.success is False
        assert result.error == "Failed"

    def test_metadata(self) -> None:
        """Metadata is accessible."""
        result = ToolResult(success=True, metadata={"time": 1.5})

        assert result.metadata["time"] == 1.5


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestToolValidation:
    """Tests for parameter validation."""

    def test_validate_with_required_params(self) -> None:
        """Validation passes with required params."""
        tool = MockTool()
        valid, error = tool.validate_params(query="test")

        assert valid is True
        assert error is None

    def test_validate_missing_required(self) -> None:
        """Validation fails without required params."""
        tool = MockTool()
        valid, error = tool.validate_params(limit=10)

        assert valid is False
        assert "query" in error

    def test_validate_empty_params_tool(self) -> None:
        """Tool without required params validates empty input."""
        tool = NoParamTool()
        valid, error = tool.validate_params()

        assert valid is True
