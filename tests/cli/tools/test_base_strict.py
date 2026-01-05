"""
Tests for Tool Base Class - Schema and Validation.

Tests the current Tool API:
- Schema generation with parameters
- Parameter validation
- Tool registry
- Tool result structure

Author: JuanCS Dev
Date: 2025-12-30
Updated: 2026-01-02 (Sprint 0 - Match actual API)
"""

from __future__ import annotations

from typing import Any


from vertice_cli.tools.base import Tool, ToolResult, ToolCategory, ToolRegistry


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
# SCHEMA STRUCTURE TESTS
# =============================================================================


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

    def test_schema_has_parameters(self) -> None:
        """Schema includes parameters object."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"

    def test_schema_has_properties(self) -> None:
        """Schema includes properties from tool parameters."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "properties" in schema["parameters"]
        assert "query" in schema["parameters"]["properties"]
        assert "limit" in schema["parameters"]["properties"]

    def test_schema_required_fields_extracted(self) -> None:
        """Required fields are properly extracted."""
        tool = MockTool()
        schema = tool.get_schema()

        assert "query" in schema["parameters"]["required"]
        assert "limit" not in schema["parameters"]["required"]

    def test_schema_properties_cleaned(self) -> None:
        """Properties don't include 'required' key (goes at schema level)."""
        tool = MockTool()
        schema = tool.get_schema()

        for prop in schema["parameters"]["properties"].values():
            assert "required" not in prop

    def test_empty_parameters_schema(self) -> None:
        """Tool with no params has valid schema."""
        tool = NoParamTool()
        schema = tool.get_schema()

        assert schema["parameters"]["properties"] == {}
        assert schema["parameters"]["required"] == []

    def test_property_types_preserved(self) -> None:
        """Property types are preserved in schema."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["parameters"]["properties"]["query"]["type"] == "string"
        assert schema["parameters"]["properties"]["limit"]["type"] == "integer"

    def test_property_descriptions_preserved(self) -> None:
        """Property descriptions are preserved in schema."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["parameters"]["properties"]["query"]["description"] == "Search query"
        assert schema["parameters"]["properties"]["limit"]["description"] == "Max results"


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

    def test_get_schemas_returns_all(self) -> None:
        """get_schemas returns schemas for all tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        schemas = registry.get_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "mock"
        assert "parameters" in schemas[0]

    def test_get_by_category(self) -> None:
        """Can filter tools by category."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(NoParamTool())

        search_tools = registry.get_by_category(ToolCategory.SEARCH)
        assert len(search_tools) == 1
        assert search_tools[0].name == "mock"

    def test_get_all_returns_dict(self) -> None:
        """get_all returns dictionary of all tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(NoParamTool())

        all_tools = registry.get_all()
        assert len(all_tools) == 2
        assert "mock" in all_tools
        assert "no_param" in all_tools


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

    def test_default_values(self) -> None:
        """ToolResult has correct defaults."""
        result = ToolResult(success=True)

        assert result.data is None
        assert result.error is None
        assert result.metadata == {}


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

    def test_validate_with_optional_params(self) -> None:
        """Validation passes with both required and optional params."""
        tool = MockTool()
        valid, error = tool.validate_params(query="test", limit=10)

        assert valid is True
        assert error is None


# =============================================================================
# TOOL NAME TESTS
# =============================================================================


class TestToolNaming:
    """Tests for tool name generation."""

    def test_name_from_class_name(self) -> None:
        """Tool name is derived from class name."""
        tool = MockTool()
        assert tool.name == "mock"

    def test_name_snake_case_conversion(self) -> None:
        """CamelCase is converted to snake_case."""
        tool = NoParamTool()
        assert tool.name == "no_param"

    def test_tool_suffix_removed(self) -> None:
        """'Tool' suffix is removed from name."""
        # Both MockTool and NoParamTool remove the Tool suffix
        tool1 = MockTool()
        tool2 = NoParamTool()

        assert "tool" not in tool1.name
        assert "tool" not in tool2.name


# =============================================================================
# TOOL CATEGORY TESTS
# =============================================================================


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_all_categories_exist(self) -> None:
        """All expected categories exist."""
        expected = [
            "FILE_READ", "FILE_WRITE", "FILE_MGMT",
            "SEARCH", "EXECUTION", "GIT", "CONTEXT", "SYSTEM"
        ]
        for cat in expected:
            assert hasattr(ToolCategory, cat)

    def test_category_values(self) -> None:
        """Category values are lowercase strings."""
        assert ToolCategory.FILE_READ.value == "file_read"
        assert ToolCategory.SEARCH.value == "search"
        assert ToolCategory.GIT.value == "git"

    def test_default_category(self) -> None:
        """Tools have FILE_READ as default category."""
        tool = NoParamTool()
        assert tool.category == ToolCategory.FILE_READ
