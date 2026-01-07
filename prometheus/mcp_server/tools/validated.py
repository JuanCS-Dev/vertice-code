"""
Validated Tool Wrapper
Automatic parameter validation for MCP tools

This module provides a wrapper class that adds automatic parameter
validation against JSON schemas, ensuring type safety and constraint
enforcement for all MCP tools.
"""

import logging
from typing import Dict, Any, List
from .base import BaseTool, ToolResult, ToolDefinition

logger = logging.getLogger(__name__)


class ValidatedTool(BaseTool):
    """
    Wrapper that adds automatic parameter validation to any tool.

    Provides:
    - JSON Schema validation
    - Type checking
    - Constraint enforcement
    - Structured error messages
    """

    def __init__(self, tool_definition: ToolDefinition):
        """
        Initialize validated tool.

        Args:
            tool_definition: Complete tool definition with schema
        """
        self._definition = tool_definition

    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        return self._definition

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against tool schema.

        Args:
            params: Parameters to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return self._definition.validate_params(params)

    async def execute_validated(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute tool with parameter validation.

        This is the main entry point that should be used instead of
        direct tool execution.

        Args:
            params: Tool parameters

        Returns:
            Tool execution result
        """
        # Validate parameters first
        validation_errors = self.validate_parameters(params)
        if validation_errors:
            error_msg = f"Parameter validation failed: {'; '.join(validation_errors)}"
            logger.warning(error_msg)
            return ToolResult(
                success=False, error=error_msg, metadata={"validation_errors": validation_errors}
            )

        # Execute tool if validation passes
        try:
            result = await self.execute(**params)  # Add await here
            logger.info(f"Tool executed successfully: {self._definition.name}")
            return result

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"{error_msg} (tool: {self._definition.name})", exc_info=True)
            return ToolResult(success=False, error=error_msg, metadata={"exception": str(e)})

        # Execute tool if validation passes
        try:
            result = self.execute(**params)
            logger.info(f"Tool executed successfully: {self._definition.name}")
            return result

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"{error_msg} (tool: {self._definition.name})", exc_info=True)
            return ToolResult(success=False, error=error_msg, metadata={"exception": str(e)})

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool logic.

        This method should be overridden by subclasses to implement
        the actual tool functionality.

        Args:
            **kwargs: Validated tool parameters

        Returns:
            Tool execution result
        """
        raise NotImplementedError("Subclasses must implement execute method")


# Convenience function for creating validated tools
def create_validated_tool(
    name: str,
    description: str,
    category: str,
    parameters: Dict[str, Any],
    required_params: List[str],
    execute_func: callable,
) -> ValidatedTool:
    """
    Create a validated tool from components.

    Args:
        name: Tool name
        description: Tool description
        category: Tool category
        parameters: Parameter schema
        required_params: List of required parameter names
        execute_func: Function that implements tool logic

    Returns:
        ValidatedTool instance
    """

    # Import here to avoid circular imports
    from .base import ToolCategory

    # Map category string to enum
    category_enum = ToolCategory(category.lower()) if isinstance(category, str) else category

    # Create tool definition
    definition = ToolDefinition(
        name=name,
        description=description,
        category=category_enum,
        parameters=parameters,
        required_params=required_params,
    )

    # Create validated tool
    class DynamicValidatedTool(ValidatedTool):
        def __init__(self):
            super().__init__(definition)
            self._execute_func = execute_func

        async def execute(self, **kwargs):
            return await self._execute_func(**kwargs)

    return DynamicValidatedTool()
