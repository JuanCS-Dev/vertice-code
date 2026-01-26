"""
Test tool for MCP Universal Gateway integration
"""

from .base import BaseTool, ToolCategory, ToolDefinition, ToolResult


class TestTool(BaseTool):
    """Simple test tool for registry validation."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="test_tool",
            description="A simple test tool for registry validation",
            category=ToolCategory.SYSTEM,
            parameters={
                "message": {
                    "type": "string",
                    "description": "Message to echo back",
                    "required": True,
                }
            },
            required_params=["message"],
        )

    async def execute(self, message: str) -> ToolResult:
        """Execute the test tool."""
        return ToolResult(
            success=True,
            data=f"Echo: {message}",
            metadata={"tool": "test_tool", "timestamp": "2026-01-01"},
        )
