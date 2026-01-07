"""
Tool Registry System for MCP Server
Unified tool management and routing

This module provides a centralized registry for all tools available
through the MCP Server, ensuring consistent discovery, validation,
and execution across all interfaces (CLI, TUI, Web App).
"""

import logging
from typing import Dict, List, Any, Optional, Type
from .base import BaseTool, ToolDefinition, ToolResult
from .validated import ValidatedTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Centralized registry for all MCP tools.

    Provides unified interface for:
    - Tool discovery and listing
    - Parameter validation
    - Tool execution routing
    - Schema generation for MCP protocol
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.info("ToolRegistry initialized")

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register
        """
        tool_name = tool.definition.name

        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered, replacing")

        self._tools[tool_name] = tool

        # Add to category index
        category = tool.definition.category.value
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)

        logger.info(f"Registered tool: {tool_name} (category: {category})")

    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools[tool_name]
        category = tool.definition.category.value

        # Remove from category index
        if category in self._categories and tool_name in self._categories[category]:
            self._categories[category].remove(tool_name)

        # Remove tool
        del self._tools[tool_name]

        logger.info(f"Unregistered tool: {tool_name}")
        return True

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools in MCP schema format.

        Returns:
            List of tool schemas for MCP tools/list response
        """
        tools = []
        for tool in self._tools.values():
            tools.append(tool.definition.to_mcp_schema())
        return tools

    def list_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List tools filtered by category."""
        if category not in self._categories:
            return []

        tools = []
        for tool_name in self._categories[category]:
            tool = self._tools[tool_name]
            tools.append(tool.definition.to_mcp_schema())
        return tools

    def get_categories(self) -> Dict[str, int]:
        """Get category counts."""
        return {cat: len(tools) for cat, tools in self._categories.items()}

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments (async version)."""
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            MCP response format
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        try:
            # Execute tool with validation
            if isinstance(tool, ValidatedTool):
                # ValidatedTool with parameter validation
                result = await tool.execute_validated(arguments)
            else:
                # BaseTool - execute directly
                result = await tool.execute(**arguments)

            # Convert to MCP response format
            response = result.to_mcp_response()

            logger.info(f"Tool executed successfully: {tool_name}")
            return {"jsonrpc": "2.0", "result": response}

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Tool execution failed: {str(e)}"},
            }

    def get_tool_count(self) -> int:
        """Get total number of registered tools."""
        return len(self._tools)

    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def validate_registry(self) -> List[str]:
        """
        Validate the registry for consistency and completeness.

        Returns:
            List of validation issues (empty if all good)
        """
        issues = []

        # Check for duplicate tool names (shouldn't happen due to dict)
        names = set()
        for tool in self._tools.values():
            if tool.definition.name in names:
                issues.append(f"Duplicate tool name: {tool.definition.name}")
            names.add(tool.definition.name)

        # Check for tools without proper schemas
        for tool_name, tool in self._tools.items():
            try:
                schema = tool.definition.to_mcp_schema()
                if not schema.get("name") or not schema.get("description"):
                    issues.append(f"Tool {tool_name} missing required schema fields")
            except Exception as e:
                issues.append(f"Tool {tool_name} schema generation failed: {e}")

        # Check category consistency
        for category, tools in self._categories.items():
            for tool_name in tools:
                if tool_name not in self._tools:
                    issues.append(f"Category {category} references non-existent tool: {tool_name}")

        if not issues:
            logger.info("Registry validation passed")
        else:
            logger.warning(f"Registry validation found {len(issues)} issues")

        return issues

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": self.get_tool_count(),
            "categories": self.get_categories(),
            "validation_issues": len(self.validate_registry()),
        }


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: BaseTool) -> None:
    """Convenience function to register a tool globally."""
    registry = get_tool_registry()
    registry.register_tool(tool)


def list_all_tools() -> List[Dict[str, Any]]:
    """Convenience function to list all tools."""
    registry = get_tool_registry()
    return registry.list_tools()
