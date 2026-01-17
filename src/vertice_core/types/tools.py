# Tool and function calling types - Domain level

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class ToolParameter(TypedDict, total=False):
    """Parameter definition for a tool."""

    type: str
    description: str
    enum: List[str]  # For enum types
    required: bool


class ToolDefinition(TypedDict):
    """Complete tool definition for LLM function calling."""

    name: str
    description: str
    parameters: Dict[str, ToolParameter]


class ToolCall(TypedDict):
    """A tool invocation request from the LLM."""

    id: str
    tool: str
    arguments: Dict[str, Any]


class ToolResult(TypedDict):
    """Result of a tool execution."""

    tool_call_id: str
    success: bool
    output: str
    error: Optional[str]
