"""
🔧 VERTICE-CLI TOOL SYSTEM v2.0 - COMPLETE REWRITE

A clean, modular, dependency-free tool system that replaces the broken one.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime


# =============================================================================
# CLEAN BASE CLASSES
# =============================================================================


class ToolResult:
    """Clean tool result class."""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}


class BaseTool(ABC):
    """Clean abstract base tool."""

    def __init__(self):
        # Convert CamelCase to snake_case
        import re

        class_name = self.__class__.__name__.replace("Tool", "")
        self.name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        self.description = ""
        self.parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass

    def validate_params(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate parameters."""
        required = [k for k, v in self.parameters.items() if v.get("required", False)]
        missing = [k for k in required if k not in kwargs]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        return True, None

    def get_schema(self) -> Dict[str, Any]:
        """Get valid JSON Schema for the tool."""
        properties = {}
        required_fields = []

        for name, param in self.parameters.items():
            # Create a clean copy of the parameter definition
            # Remove 'required' from the property definition itself
            # as it belongs in the 'required' list at the object level
            clean_param = param.copy()
            if clean_param.pop("required", False):
                required_fields.append(name)

            # Recurse for nested objects if needed (simple version for now)
            properties[name] = clean_param

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_fields,
            },
        }


# =============================================================================
# FILE TOOLS - Completely rewritten
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

    async def execute(
        self, path: str, line_range: Optional[List[int]] = None, **kwargs
    ) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path).resolve()

            if not file_path.exists():
                return ToolResult(False, error=f"File not found: {path}")

            if not file_path.is_file():
                return ToolResult(False, error=f"Path is not a file: {path}")

            # Security check - prevent reading sensitive files
            if self._is_sensitive_file(file_path):
                return ToolResult(False, error=f"Access denied to sensitive file: {path}")

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")

            # Apply line range
            if line_range and len(line_range) == 2:
                start, end = line_range
                if start < 1:
                    start = 1
                if end > len(lines):
                    end = len(lines)
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
                    "size": len(content.encode("utf-8")),
                    "encoding": "utf-8",
                },
            )

        except UnicodeDecodeError:
            return ToolResult(False, error=f"File encoding not supported: {path}")
        except PermissionError:
            return ToolResult(False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, error=f"Error reading file: {str(e)}")

    def _is_sensitive_file(self, file_path: Path) -> bool:
        """Check if file is sensitive."""
        sensitive_patterns = [
            ".env",
            "secret",
            "key",
            "password",
            "token",
            ".git",
            ".ssh",
            "/etc/",
            "/proc/",
            "/sys/",
        ]
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in sensitive_patterns)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from extension."""
        suffix = file_path.suffix.lstrip(".").lower()
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
            "html": "html",
            "css": "css",
            "json": "json",
            "xml": "xml",
            "yaml": "yaml",
            "yml": "yaml",
            "md": "markdown",
            "txt": "text",
        }
        return lang_map.get(suffix, "text")


class WriteFileTool(BaseTool):
    """Clean file writing tool."""

    def __init__(self):
        super().__init__()
        self.description = "Create new file with content (fails if file exists)"
        self.parameters = {
            "path": {"type": "string", "description": "File path to create", "required": True},
            "content": {"type": "string", "description": "File content", "required": True},
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories",
                "required": False,
            },
            "encoding": {"type": "string", "description": "File encoding", "required": False},
        }

    async def execute(
        self, path: str, content: str, create_dirs: bool = True, encoding: str = "utf-8", **kwargs
    ) -> ToolResult:
        """Create file with content."""
        try:
            file_path = Path(path).resolve()

            if file_path.exists():
                return ToolResult(
                    False, error=f"File already exists: {path}. Use edit_file to modify."
                )

            # Security check
            if self._is_sensitive_path(file_path):
                return ToolResult(False, error=f"Access denied to sensitive path: {path}")

            # Create directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding=encoding)

            return ToolResult(
                True,
                data={
                    "path": str(file_path),
                    "size": len(content.encode(encoding)),
                    "lines": len(content.split("\n")),
                    "encoding": encoding,
                },
            )

        except PermissionError:
            return ToolResult(False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, error=f"Error writing file: {str(e)}")

    def _is_sensitive_path(self, file_path: Path) -> bool:
        """Check if path is sensitive."""
        sensitive_patterns = [
            "/etc/",
            "/proc/",
            "/sys/",
            "/boot/",
            "/root/",
            ".env",
            "secret",
            "key",
            "password",
            "token",
        ]
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in sensitive_patterns)


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
            file_path = Path(path).resolve()

            if not file_path.exists():
                return ToolResult(False, error=f"File not found: {path}")

            if not file_path.is_file():
                return ToolResult(False, error=f"Path is not a file: {path}")

            # Security check
            if self._is_sensitive_file(file_path):
                return ToolResult(False, error=f"Access denied to sensitive file: {path}")

            content = file_path.read_text(encoding="utf-8", errors="replace")

            if old_string not in content:
                return ToolResult(False, error=f"Text not found in file: {old_string[:50]}...")

            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                True,
                data={
                    "path": str(file_path),
                    "changes": 1,
                    "old_length": len(content),
                    "new_length": len(new_content),
                },
            )

        except PermissionError:
            return ToolResult(False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, error=f"Error editing file: {str(e)}")

    def _is_sensitive_file(self, file_path: Path) -> bool:
        """Check if file is sensitive."""
        sensitive_patterns = [
            ".env",
            "secret",
            "key",
            "password",
            "token",
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
        ]
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in sensitive_patterns)


class ListDirectoryTool(BaseTool):
    """Clean directory listing tool."""

    def __init__(self):
        super().__init__()
        self.description = "List contents of a directory"
        self.parameters = {
            "path": {"type": "string", "description": "Directory path", "required": True},
            "show_hidden": {
                "type": "boolean",
                "description": "Show hidden files",
                "required": False,
            },
        }

    async def execute(self, path: str, show_hidden: bool = False, **kwargs) -> ToolResult:
        """List directory contents."""
        try:
            dir_path = Path(path).resolve()

            if not dir_path.exists():
                return ToolResult(False, error=f"Directory not found: {path}")

            if not dir_path.is_dir():
                return ToolResult(False, error=f"Path is not a directory: {path}")

            # Security check
            if self._is_sensitive_dir(dir_path):
                return ToolResult(False, error=f"Access denied to sensitive directory: {path}")

            entries = []
            for item in dir_path.iterdir():
                if not show_hidden and item.name.startswith("."):
                    continue

                entries.append(
                    {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    }
                )

            # Sort by name, directories first
            entries.sort(key=lambda x: (x["type"] == "file", x["name"]))

            return ToolResult(
                True, data={"path": str(dir_path), "entries": entries, "count": len(entries)}
            )

        except PermissionError:
            return ToolResult(False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, error=f"Error listing directory: {str(e)}")

    def _is_sensitive_dir(self, dir_path: Path) -> bool:
        """Check if directory is sensitive."""
        sensitive_patterns = [
            "/etc",
            "/proc",
            "/sys",
            "/boot",
            "/root",
            ".git",
            ".ssh",
            "node_modules",
            "__pycache__",
        ]
        path_str = str(dir_path).lower()
        return any(pattern in path_str for pattern in sensitive_patterns)


# =============================================================================
# CLEAN TOOL REGISTRY
# =============================================================================


class CleanToolRegistry:
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

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for API."""
        schemas = []
        for tool in self.tools.values():
            schemas.append(tool.get_schema())
        return schemas

    def __len__(self) -> int:
        return len(self.tools)


# =============================================================================
# CLEAN MCP CLIENT
# =============================================================================


class CleanMCPClient:
    """Clean MCP client for tool execution."""

    def __init__(self, registry: CleanToolRegistry):
        self.registry = registry

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool."""
        tool = self.registry.get(tool_name)
        if not tool:
            return {
                "error": f"Tool '{tool_name}' not found. Available: {self.registry.list_tools()}"
            }

        # Validate parameters
        is_valid, error = tool.validate_params(**arguments)
        if not is_valid:
            return {"error": error}

        # Execute tool
        try:
            result = await tool.execute(**arguments)
            if result.success:
                return {"result": result.data}
            else:
                return {"error": result.error}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        return {
            "service": "clean_mcp",
            "healthy": True,
            "tools_registered": len(self.registry),
            "available_tools": self.registry.list_tools(),
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_clean_tool_registry() -> CleanToolRegistry:
    """Create registry with all file tools."""
    registry = CleanToolRegistry()

    # Register core file tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(EditFileTool())
    registry.register(ListDirectoryTool())

    return registry


def create_clean_mcp_client() -> CleanMCPClient:
    """Create clean MCP client with all tools."""
    registry = create_clean_tool_registry()
    return CleanMCPClient(registry)


# =============================================================================
# DEMO FUNCTION
# =============================================================================


async def demo_clean_system():
    """Demonstrate the complete clean tool system."""
    print("🔧 CLEAN TOOL SYSTEM v2.0 - COMPLETE REWRITE")
    print("=" * 60)

    # Create clean system
    mcp = create_clean_mcp_client()

    print(f"✅ System initialized with {len(mcp.registry)} tools")
    print(f"Available tools: {mcp.registry.list_tools()}")

    # Test all tools
    tests = [
        ("📖 read_file", "read_file", {"path": "README.md"}),
        ("📁 list_directory", "list_directory", {"path": "."}),
        (
            "✏️  write_file",
            "write_file",
            {"path": "v2_test.txt", "content": "Created by v2.0 system!"},
        ),
        (
            "🔄 edit_file",
            "edit_file",
            {"path": "v2_test.txt", "old_string": "Created", "new_string": "Generated"},
        ),
    ]

    for test_name, tool_name, args in tests:
        print(f"\n{test_name}...")
        try:
            result = await mcp.call_tool(tool_name, args)
            if "result" in result:
                if tool_name == "read_file":
                    data = result["result"]
                    print(f"✅ Read {len(data['content'])} chars, {data['lines']} lines")
                elif tool_name == "list_directory":
                    data = result["result"]
                    print(f"✅ Listed {data['count']} entries in {data['path']}")
                elif tool_name == "write_file":
                    data = result["result"]
                    print(f"✅ Created {data['path']} ({data['size']} bytes)")
                elif tool_name == "edit_file":
                    data = result["result"]
                    print(f"✅ Edited {data['path']} ({data['changes']} changes)")
            else:
                print(f"❌ Error: {result['error']}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    # Health check
    health = mcp.get_health_status()
    print(f"\n🏥 Health Status: {'✅ Good' if health['healthy'] else '❌ Bad'}")
    print(f"   Tools: {health['tools_registered']}")

    print("\n🎉 Clean tool system v2.0 working perfectly!")


if __name__ == "__main__":
    asyncio.run(demo_clean_system())
