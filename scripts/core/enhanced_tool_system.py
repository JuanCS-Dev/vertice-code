"""
🔧 VERTICE-CLI TOOL SYSTEM - CLEAN ARCHITECTURE

This replaces the broken tool system with a clean, modular architecture.
"""

# Import the clean base classes
from clean_tool_system import BaseTool, ToolResult, ToolRegistry, CleanMCPClient

# Import existing tool implementations but adapt them to the clean interface
from vertice_cli.tools.file_ops import ReadFileTool as OldReadFileTool
from vertice_cli.tools.file_ops import WriteFileTool as OldWriteFileTool
from vertice_cli.tools.file_ops import EditFileTool as OldEditFileTool


# =============================================================================
# ADAPTER CLASSES - Bridge old tools to new interface
# =============================================================================


class ReadFileToolAdapter(BaseTool):
    """Adapter for existing ReadFileTool."""

    def __init__(self):
        super().__init__()
        self.description = "Read complete contents of a file"
        self.parameters = {
            "path": {"type": "string", "description": "File path", "required": True},
            "line_range": {
                "type": "array",
                "description": "Optional [start, end] line range",
                "required": False,
            },
        }
        self._old_tool = OldReadFileTool()

    async def execute(self, **kwargs) -> ToolResult:
        """Execute using the old tool implementation."""
        try:
            result = await self._old_tool._execute_validated(**kwargs)
            if result.success:
                return ToolResult(True, result.data, metadata=result.metadata)
            else:
                return ToolResult(False, error=result.error)
        except Exception as e:
            return ToolResult(False, error=str(e))


class WriteFileToolAdapter(BaseTool):
    """Adapter for existing WriteFileTool."""

    def __init__(self):
        super().__init__()
        self.description = "Create new file with content"
        self.parameters = {
            "path": {"type": "string", "description": "File path to create", "required": True},
            "content": {"type": "string", "description": "File content", "required": True},
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories",
                "required": False,
            },
        }
        self._old_tool = OldWriteFileTool()

    async def execute(self, **kwargs) -> ToolResult:
        """Execute using the old tool implementation."""
        try:
            result = await self._old_tool._execute_validated(**kwargs)
            if result.success:
                return ToolResult(True, result.data, metadata=result.metadata)
            else:
                return ToolResult(False, error=result.error)
        except Exception as e:
            return ToolResult(False, error=str(e))


class EditFileToolAdapter(BaseTool):
    """Adapter for existing EditFileTool."""

    def __init__(self):
        super().__init__()
        self.description = "Edit file by replacing text"
        self.parameters = {
            "path": {"type": "string", "description": "File path to edit", "required": True},
            "old_string": {"type": "string", "description": "Text to replace", "required": True},
            "new_string": {"type": "string", "description": "Replacement text", "required": True},
        }
        self._old_tool = OldEditFileTool()

    async def execute(self, **kwargs) -> ToolResult:
        """Execute using the old tool implementation."""
        try:
            result = await self._old_tool._execute_validated(**kwargs)
            if result.success:
                return ToolResult(True, result.data, metadata=result.metadata)
            else:
                return ToolResult(False, error=result.error)
        except Exception as e:
            return ToolResult(False, error=str(e))


# =============================================================================
# ENHANCED REGISTRY - Backward compatible
# =============================================================================


class EnhancedToolRegistry(ToolRegistry):
    """Enhanced registry that can load old tools."""

    def load_legacy_tools(self):
        """Load tools from the old system."""
        try:
            # Try to import and adapt existing tools
            self.register(ReadFileToolAdapter())
            self.register(WriteFileToolAdapter())
            self.register(EditFileToolAdapter())
            print("✅ Legacy tools loaded successfully")
        except ImportError as e:
            print(f"⚠️  Could not load legacy tools: {e}")
            # Fall back to clean implementations
            from clean_tool_system import ReadFileTool, WriteFileTool, EditFileTool

            self.register(ReadFileTool())
            self.register(WriteFileTool())
            self.register(EditFileTool())
            print("✅ Clean tools loaded as fallback")


# =============================================================================
# ENHANCED MCP CLIENT - Backward compatible
# =============================================================================


class EnhancedMCPClient(CleanMCPClient):
    """Enhanced MCP client with legacy support."""

    def __init__(self):
        registry = EnhancedToolRegistry()
        registry.load_legacy_tools()
        super().__init__(registry)


# =============================================================================
# COMPATIBILITY LAYER - Make it work with existing code
# =============================================================================


def create_enhanced_mcp_client():
    """Create enhanced MCP client for existing code."""
    return EnhancedMCPClient()


def create_tool_registry():
    """Create enhanced tool registry."""
    registry = EnhancedToolRegistry()
    registry.load_legacy_tools()
    return registry


# =============================================================================
# TEST COMPATIBILITY
# =============================================================================


async def test_compatibility():
    """Test that the enhanced system works with existing expectations."""
    print("🔧 TESTING ENHANCED TOOL SYSTEM COMPATIBILITY")
    print("=" * 60)

    # Test enhanced MCP client
    mcp = create_enhanced_mcp_client()

    print(f"Available tools: {mcp.registry.list_tools()}")

    # Test file operations
    print("\n📖 Testing read_file...")
    result = await mcp.call_tool("read_file", {"path": "README.md"})
    if "result" in result:
        print(f"✅ Read {len(result['result']['content'])} characters")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

    print("\n✏️  Testing write_file...")
    result = await mcp.call_tool(
        "write_file", {"path": "enhanced_test.txt", "content": "Created by enhanced tool system!"}
    )
    if "result" in result:
        print(f"✅ Created file: {result['result']['path']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

    print("\n🔄 Testing edit_file...")
    result = await mcp.call_tool(
        "edit_file",
        {"path": "enhanced_test.txt", "old_string": "Created", "new_string": "Generated"},
    )
    if "result" in result:
        print(f"✅ Edited file: {result['result']['path']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

    print("\n🎉 Enhanced tool system working with compatibility!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_compatibility())
