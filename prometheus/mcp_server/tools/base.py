"""
MCP Tool Base Classes
Core abstractions for MCP Server tools

This module provides the foundational classes for all tools
exposed through the MCP Server, ensuring consistent interfaces
and schema generation.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories for tool organization."""

    FILE = "file"
    SEARCH = "search"
    EXECUTION = "execution"
    GIT = "git"
    WEB = "web"
    MEDIA = "media"
    CONTEXT = "context"
    SYSTEM = "system"
    PROMETHEUS = "prometheus"
    NOTEBOOK = "notebook"
    ADVANCED = "advanced"


@dataclass
class ToolResult:
    """Standardized result format for all tools."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_mcp_response(self) -> Dict[str, Any]:
        """Convert to MCP protocol response format."""
        if self.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            json.dumps(self.data, indent=2)
                            if isinstance(self.data, (dict, list))
                            else str(self.data)
                        ),
                    }
                ]
            }
        else:
            return {"isError": True, "content": [{"type": "text", "text": f"Error: {self.error}"}]}


@dataclass
class ToolDefinition:
    """Complete tool definition for MCP protocol."""

    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params,
            },
        }

    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters against schema."""
        errors = []

        # Check required parameters
        for required in self.required_params:
            if required not in params:
                errors.append(f"Missing required parameter: {required}")

        # Validate parameter types and constraints
        for param_name, param_config in self.parameters.items():
            if param_name in params:
                value = params[param_name]
                param_type = param_config.get("type")

                # Basic type validation
                if param_type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {param_name} must be string, got {type(value)}")
                elif param_type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter {param_name} must be integer, got {type(value)}")
                elif param_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {param_name} must be boolean, got {type(value)}")

        return errors


class BaseTool(ABC):
    """Abstract base class for all MCP tools."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Tool definition for MCP schema."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def validate_and_execute(self, params: Dict[str, Any]) -> ToolResult:
        """Validate parameters and execute tool."""
        # Validate parameters
        validation_errors = self.definition.validate_params(params)
        if validation_errors:
            return ToolResult(
                success=False, error=f"Parameter validation failed: {'; '.join(validation_errors)}"
            )

        # Execute tool
        try:
            return self.execute(**params)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Tool execution failed: {str(e)}")
