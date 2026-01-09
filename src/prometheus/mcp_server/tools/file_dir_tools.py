"""
File Listing Tools for MCP Server
Directory listing and file system exploration

This module provides directory listing operations with safety validation
and structured output formatting.
"""

import logging
from pathlib import Path
from typing import List, Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


def validate_safe_path(path: str, allow_root: bool = False) -> bool:
    """Validate that a path is safe to access."""
    try:
        abs_path = Path(path).resolve()

        dangerous_patterns = [
            "/etc/",
            "/proc/",
            "/sys/",
            "/dev/",
            "/boot/",
            "/usr/sbin/",
            "/usr/bin/",
            "/bin/",
            "/sbin/",
            "/var/log/",
            "/var/run/",
            "/var/tmp/",
            "/root/",
            "/home/root/",
        ]

        if not allow_root:
            for pattern in dangerous_patterns:
                if pattern in str(abs_path):
                    return False

        return True

    except Exception:
        return False


async def list_directory(
    path: str = ".", recursive: bool = False, max_depth: int = 3
) -> ToolResult:
    """List directory contents."""
    try:
        if not validate_safe_path(path, allow_root=True):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        dir_path = Path(path)
        if not dir_path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")

        if not dir_path.is_dir():
            return ToolResult(success=False, error=f"Path is not a directory: {path}")

        def get_dir_contents(path_obj: Path, depth: int = 0) -> List[dict]:
            if depth > max_depth:
                return []

            contents = []
            try:
                for item in sorted(path_obj.iterdir()):
                    item_info = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                    }

                    if item.is_dir() and recursive and depth < max_depth:
                        item_info["contents"] = get_dir_contents(item, depth + 1)

                    contents.append(item_info)

            except PermissionError:
                return [{"name": "Access denied", "type": "error"}]

            return contents

        contents = get_dir_contents(dir_path)

        return ToolResult(
            success=True,
            data={
                "path": str(dir_path),
                "contents": contents,
                "total_items": len(contents),
            },
            metadata={
                "recursive": recursive,
                "max_depth": max_depth,
                "operation": "list_dir",
            },
        )

    except Exception as e:
        logger.error(f"List directory error: {e}")
        return ToolResult(success=False, error=str(e))


async def get_directory_tree(path: str = ".", max_depth: int = 3) -> ToolResult:
    """Get a tree-like representation of directory structure."""
    try:
        if not validate_safe_path(path, allow_root=True):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        dir_path = Path(path)
        if not dir_path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")

        def build_tree(path_obj: Path, prefix: str = "", depth: int = 0) -> List[str]:
            if depth > max_depth:
                return []

            lines = []
            try:
                items = sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    next_prefix = prefix + ("    " if is_last else "│   ")

                    line = f"{prefix}{connector}{item.name}"
                    if item.is_dir():
                        line += "/"
                        if depth < max_depth:
                            subtree = build_tree(item, next_prefix, depth + 1)
                            lines.extend([line] + subtree)
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)

            except PermissionError:
                lines.append(f"{prefix}└── [Access denied]")

            return lines

        tree_lines = [str(dir_path) + "/"] + build_tree(dir_path)

        return ToolResult(
            success=True,
            data={
                "path": str(dir_path),
                "tree": "\n".join(tree_lines),
                "lines": len(tree_lines),
            },
            metadata={
                "max_depth": max_depth,
                "operation": "tree",
            },
        )

    except Exception as e:
        logger.error(f"Get directory tree error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register directory tools
dir_tools = [
    create_validated_tool(
        name="list_directory",
        description="List directory contents with optional recursion",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Directory path", "default": "."},
            "recursive": {"type": "boolean", "description": "List recursively", "default": False},
            "max_depth": {
                "type": "integer",
                "description": "Maximum recursion depth",
                "default": 3,
            },
        },
        required_params=[],
        execute_func=list_directory,
    ),
    create_validated_tool(
        name="get_directory_tree",
        description="Get a tree-like representation of directory structure",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Directory path", "default": "."},
            "max_depth": {"type": "integer", "description": "Maximum tree depth", "default": 3},
        },
        required_params=[],
        execute_func=get_directory_tree,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in dir_tools:
    register_tool(tool)
