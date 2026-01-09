"""
🔧 TOOL SYSTEM REFACTOR - Phase 1: Break Circular Dependencies

This module provides a clean tool system without circular imports.
We separate concerns and use dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path


# =============================================================================
# BASE TOOL INTERFACE
# =============================================================================


class ToolResult:
    """Standardized tool result."""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}


class BaseTool(ABC):
    """Abstract base tool without framework dependencies."""

    def __init__(self):
        # Convert CamelCase to snake_case properly
        import re

        class_name = self.__class__.__name__.replace("Tool", "")
        self.name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        self.description = ""
        self.parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def validate_params(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate parameters."""
        required = [k for k, v in self.parameters.items() if v.get("required", False)]
        missing = [k for k in required if k not in kwargs]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        return True, None


# =============================================================================
# CLEAN TOOL REGISTRY
# =============================================================================


class ToolRegistry:
    """Clean tool registry without circular dependencies."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self.tools.keys())

    def get_all(self) -> Dict[str, BaseTool]:
        """Get all tools."""
        return self.tools.copy()


# =============================================================================
# CLEAN FILE TOOLS
# =============================================================================


class ReadFileTool(BaseTool):
    """Clean file reading tool."""

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

    async def execute(self, path: str, line_range: Optional[tuple] = None, **kwargs) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path)

            if not file_path.exists():
                return ToolResult(False, error=f"File not found: {path}")

            if not file_path.is_file():
                return ToolResult(False, error=f"Path is not a file: {path}")

            content = file_path.read_text()
            lines = content.split("\n")

            # Apply line range
            if line_range and len(line_range) == 2:
                start, end = line_range
                lines = lines[start - 1 : end]
                content = "\n".join(lines)

            # Detect language
            language = self._detect_language(file_path)

            return ToolResult(
                True,
                data={
                    "content": content,
                    "lines": len(lines),
                    "path": str(file_path),
                    "language": language,
                    "size": file_path.stat().st_size,
                },
            )

        except Exception as e:
            return ToolResult(False, error=str(e))

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language."""
        suffix = file_path.suffix.lstrip(".")
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "php": "php",
        }
        return lang_map.get(suffix, "text")


class WriteFileTool(BaseTool):
    """Clean file writing tool."""

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

    async def execute(
        self, path: str, content: str, create_dirs: bool = True, **kwargs
    ) -> ToolResult:
        """Create file with content."""
        try:
            file_path = Path(path)

            if file_path.exists():
                return ToolResult(False, error=f"File already exists: {path}")

            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content)

            return ToolResult(
                True,
                data={
                    "path": str(file_path),
                    "size": len(content),
                    "lines": len(content.split("\n")),
                },
            )

        except Exception as e:
            return ToolResult(False, error=str(e))


class EditFileTool(BaseTool):
    """Clean file editing tool."""

    def __init__(self):
        super().__init__()
        self.description = "Edit file by replacing text"
        self.parameters = {
            "path": {"type": "string", "description": "File path to edit", "required": True},
            "old_string": {"type": "string", "description": "Text to replace", "required": True},
            "new_string": {"type": "string", "description": "Replacement text", "required": True},
        }

    async def execute(self, path: str, old_string: str, new_string: str, **kwargs) -> ToolResult:
        """Edit file by replacing text."""
        try:
            file_path = Path(path)

            if not file_path.exists():
                return ToolResult(False, error=f"File not found: {path}")

            content = file_path.read_text()

            if old_string not in content:
                return ToolResult(False, error=f"Text not found in file: {old_string[:50]}...")

            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content)

            return ToolResult(
                True,
                data={
                    "path": str(file_path),
                    "changes": 1,
                    "old_length": len(content),
                    "new_length": len(new_content),
                },
            )

        except Exception as e:
            return ToolResult(False, error=str(e))


# =============================================================================
# CLEAN MCP CLIENT
# =============================================================================


class CleanMCPClient:
    """Clean MCP client without circular dependencies."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool."""
        tool = self.registry.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        # Validate parameters
        is_valid, error = tool.validate_params(**arguments)
        if not is_valid:
            return {"error": error}

        # Execute tool
        result = await tool.execute(**arguments)

        if result.success:
            return {"result": result.data}
        else:
            return {"error": result.error}


# =============================================================================
# FACTORY FUNCTIONS - DEPENDENCY INJECTION
# =============================================================================


def create_basic_tool_registry() -> ToolRegistry:
    """Create registry with basic tools."""
    registry = ToolRegistry()

    # Register basic file tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(EditFileTool())

    return registry


def create_clean_mcp_client() -> CleanMCPClient:
    """Create clean MCP client with basic tools."""
    registry = create_basic_tool_registry()
    return CleanMCPClient(registry)


# =============================================================================
# DEMO FUNCTION
# =============================================================================


async def demo_clean_tools():
    """Demonstrate the clean tool system."""
    print("🔧 CLEAN TOOL SYSTEM DEMO")
    print("=" * 40)

    # Create clean MCP client
    mcp = create_clean_mcp_client()

    print(f"Available tools: {mcp.registry.list_tools()}")

    # Test read_file
    print("\n📖 Testing read_file...")
    result = await mcp.call_tool("read_file", {"path": "README.md"})
    if "result" in result:
        print(f"✅ Read {len(result['result']['content'])} characters")
    else:
        print(f"❌ Error: {result['error']}")

    # Test write_file
    print("\n✏️  Testing write_file...")
    result = await mcp.call_tool(
        "write_file", {"path": "clean_test.txt", "content": "Created by clean tool system!"}
    )
    if "result" in result:
        print(f"✅ Created file: {result['result']['path']}")
    else:
        print(f"❌ Error: {result['error']}")

    # Test edit_file
    print("\n🔄 Testing edit_file...")
    result = await mcp.call_tool(
        "edit_file", {"path": "clean_test.txt", "old_string": "Created", "new_string": "Generated"}
    )
    if "result" in result:
        print(f"✅ Edited file: {result['result']['path']}")
    else:
        print(f"❌ Error: {result['error']}")

    # Test write_file
    print("\n✏️  Testing write_file...")
    result = await mcp.call_tool(
        "write_file", {"path": "clean_test.txt", "content": "Created by clean tool system!"}
    )
    if "result" in result:
        print(f"✅ Created file: {result['result']['path']}")
    else:
        print(f"❌ Error: {result['error']}")

    print("\n🎉 Clean tool system working!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_clean_tools())
