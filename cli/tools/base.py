"""
Base tool class and utilities for tool-based architecture.

Implements 2025 tool schema standards:
- Anthropic strict mode (structured-outputs-2025-11-13)
- OpenAI function calling
- Google Gemini function declarations

References:
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://openai.github.io/openai-agents-python/
- https://ai.google.dev/gemini-api/docs/function-calling
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ToolCategory(Enum):
    """Tool categories for organization."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_MGMT = "file_mgmt"
    SEARCH = "search"
    EXECUTION = "execution"
    GIT = "git"
    CONTEXT = "context"
    SYSTEM = "system"
    WEB = "web"


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def output(self) -> Any:
        """Alias for data (API compatibility)."""
        return self.data


class Tool(ABC):
    """Base class for all tools.

    Implements 2025 schema standards:
    - strict: true (Anthropic structured outputs)
    - additionalProperties: false (required for strict mode)
    - input_schema format (Anthropic/OpenAI compatible)

    Example:
        >>> class MyTool(Tool):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.description = "Does something useful"
        ...         self.parameters = {
        ...             "query": {"type": "string", "description": "Search query", "required": True}
        ...         }
        ...
        >>> tool = MyTool()
        >>> schema = tool.get_schema()
        >>> schema["strict"]
        True
    """

    def __init__(self) -> None:
        """Initialize tool with auto-generated name from class."""
        import re

        class_name = self.__class__.__name__.replace("Tool", "")
        self.name: str = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        self.category: ToolCategory = ToolCategory.FILE_READ
        self.description: str = ""
        self.parameters: Dict[str, Any] = {}
        self._examples: Optional[List[Dict[str, Any]]] = None

    @abstractmethod
    async def _execute_validated(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute() must be implemented"
        )

    def validate_params(self, **kwargs: Any) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        required = [k for k, v in self.parameters.items() if v.get("required", False)]
        missing = [k for k in required if k not in kwargs]

        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"

        return True, None

    def get_schema(self, strict: bool = True) -> Dict[str, Any]:
        """Get tool schema for LLM tool use.

        Implements Anthropic 2025 structured outputs format:
        - strict: true at top level (constrained decoding)
        - additionalProperties: false (required for strict mode)
        - input_schema format for Anthropic API

        Args:
            strict: Enable strict mode for guaranteed schema compliance.
                    Default True for production reliability.

        Returns:
            Tool schema compatible with Anthropic, OpenAI, and Gemini APIs
        """
        # Build properties without 'required' key (goes in schema level)
        properties = {}
        for name, spec in self.parameters.items():
            prop = {k: v for k, v in spec.items() if k != "required"}
            properties[name] = prop

        # Get required fields
        required = [k for k, v in self.parameters.items() if v.get("required", False)]

        # Build input_schema (Anthropic format)
        input_schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        # Strict mode requires additionalProperties: false
        if strict:
            input_schema["additionalProperties"] = False

        # Build final schema
        schema: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "input_schema": input_schema,
        }

        # Add strict flag at top level (Anthropic 2025 format)
        if strict:
            schema["strict"] = True

        # Add examples if provided (helps model accuracy)
        if self._examples:
            schema["examples"] = self._examples

        return schema

    def get_schema_openai(self) -> Dict[str, Any]:
        """Get OpenAI-compatible function schema.

        Returns:
            Schema in OpenAI function calling format
        """
        base = self.get_schema(strict=True)
        return {
            "type": "function",
            "function": {
                "name": base["name"],
                "description": base["description"],
                "parameters": base["input_schema"],
            },
        }

    def get_schema_gemini(self) -> Dict[str, Any]:
        """Get Google Gemini-compatible function declaration.

        Returns:
            Schema in Gemini function declaration format
        """
        base = self.get_schema(strict=True)
        return {
            "name": base["name"],
            "description": base["description"],
            "parameters": base["input_schema"],
        }

    def set_examples(self, examples: List[Dict[str, Any]]) -> None:
        """Set usage examples for better model accuracy.

        Args:
            examples: List of example inputs/outputs
        """
        self._examples = examples


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_all(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self.tools

    def get_schemas(self) -> list[Dict[str, Any]]:
        """Get all tool schemas for LLM."""
        return [tool.get_schema() for tool in self.tools.values()]

    def get_by_category(self, category: ToolCategory) -> list[Tool]:
        """Get all tools in a category."""
        return [t for t in self.tools.values() if t.category == category]
