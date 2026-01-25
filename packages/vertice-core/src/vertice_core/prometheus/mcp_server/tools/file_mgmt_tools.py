"""
File Management Tools for MCP Server
File system operations for management tasks

This module provides file operations like delete, move, copy,
and directory management with safety validation.
"""

import shutil
import logging
from pathlib import Path
from typing import List
from .base import ToolResult
from .validated import create_validated_tool
from .file_rw_tools import detect_encoding

logger = logging.getLogger(__name__)


def validate_file_size(content: str, max_size: int = 100 * 1024 * 1024) -> bool:
    """Validate that content size is within limits."""
    return len(content.encode("utf-8")) <= max_size


def validate_safe_path(path: str, allow_root: bool = False) -> bool:
    """Validate that a path is safe to access."""
    try:
        abs_path = Path(path).resolve()

        # Block dangerous patterns
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

        # Additional safety checks
        if abs_path.is_symlink():
            try:
                target = abs_path.readlink()
                if any(pattern in str(target) for pattern in dangerous_patterns):
                    return False
            except Exception:
                return False

        return True

    except Exception:
        return False


async def delete_file(path: str) -> ToolResult:
    """Delete a file safely."""
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {path}")

        # Additional safety check for critical files
        critical_files = [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "/boot/grub/grub.cfg",
            "/etc/fstab",
        ]
        if str(file_path) in critical_files:
            return ToolResult(success=False, error=f"Cannot delete critical system file: {path}")

        # Get file info before deletion
        file_size = file_path.stat().st_size
        file_path.unlink()

        return ToolResult(
            success=True,
            data={
                "message": "File deleted successfully",
                "path": str(file_path),
            },
            metadata={
                "file_size": file_size,
                "operation": "delete",
            },
        )

    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return ToolResult(success=False, error=str(e))


async def move_file(source: str, destination: str) -> ToolResult:
    """Move/rename a file."""
    try:
        if not validate_safe_path(source) or not validate_safe_path(destination):
            return ToolResult(success=False, error="Access denied to source or destination path")

        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return ToolResult(success=False, error=f"Source file not found: {source}")

        # Create destination directory if it doesn't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        shutil.move(str(src_path), str(dst_path))

        return ToolResult(
            success=True,
            data={
                "message": "File moved successfully",
                "source": str(src_path),
                "destination": str(dst_path),
            },
            metadata={
                "operation": "move",
                "src_exists": src_path.exists(),
                "dst_exists": dst_path.exists(),
            },
        )

    except Exception as e:
        logger.error(f"Move file error: {e}")
        return ToolResult(success=False, error=str(e))


async def copy_file(source: str, destination: str) -> ToolResult:
    """Copy a file."""
    try:
        if not validate_safe_path(source) or not validate_safe_path(destination):
            return ToolResult(success=False, error="Access denied to source or destination path")

        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return ToolResult(success=False, error=f"Source file not found: {source}")

        if not src_path.is_file():
            return ToolResult(success=False, error=f"Source is not a file: {source}")

        # Create destination directory if it doesn't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(str(src_path), str(dst_path))

        return ToolResult(
            success=True,
            data={
                "message": "File copied successfully",
                "source": str(src_path),
                "destination": str(dst_path),
            },
            metadata={
                "operation": "copy",
                "src_size": src_path.stat().st_size,
                "dst_size": dst_path.stat().st_size,
            },
        )

    except Exception as e:
        logger.error(f"Copy file error: {e}")
        return ToolResult(success=False, error=str(e))


async def create_directory(path: str) -> ToolResult:
    """Create a directory."""
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)

        return ToolResult(
            success=True,
            data={
                "message": "Directory created successfully",
                "path": str(dir_path),
            },
            metadata={
                "operation": "mkdir",
                "created": True,
                "parents_created": True,
            },
        )

    except Exception as e:
        logger.error(f"Create directory error: {e}")
        return ToolResult(success=False, error=str(e))


async def read_multiple_files(paths: List[str]) -> ToolResult:
    """Read multiple files efficiently."""
    try:
        results = {}

        for path in paths:
            if not validate_safe_path(path):
                results[path] = {"error": "Access denied"}
                continue

            file_path = Path(path)
            if not file_path.exists():
                results[path] = {"error": "File not found"}
                continue

            if not file_path.is_file():
                results[path] = {"error": "Not a file"}
                continue

            # Check file size
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit per file
                results[path] = {"error": f"File too large: {file_size} bytes"}
                continue

            try:
                # Detect encoding for better compatibility
                encoding = detect_encoding(str(file_path))

                content = file_path.read_text(encoding=encoding, errors="replace")
                results[path] = {
                    "content": content,
                    "size": len(content),
                    "encoding": encoding,
                    "success": True,
                }
            except Exception as e:
                results[path] = {"error": str(e)}

        return ToolResult(
            success=True,
            data={
                "results": results,
                "total_files": len(paths),
                "successful_reads": sum(1 for r in results.values() if r.get("success")),
            },
            metadata={
                "operation": "read_multiple",
                "batch_size": len(paths),
            },
        )

    except Exception as e:
        logger.error(f"Read multiple files error: {e}")
        return ToolResult(success=False, error=str(e))


async def insert_lines(path: str, line_number: int, content: str) -> ToolResult:
    """Insert content at specific line in file."""
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        # Read all lines
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Validate line number
        if line_number < 1 or line_number > len(lines) + 1:
            return ToolResult(
                success=False,
                error=f"Invalid line number {line_number}. File has {len(lines)} lines.",
            )

        # Validate content doesn't already have newline at end
        if not content.endswith("\n"):
            content += "\n"

        # Insert content
        insert_index = line_number - 1
        lines.insert(insert_index, content)

        # Validate resulting file size
        new_content = "".join(lines)
        new_size = len(new_content.encode("utf-8"))
        if new_size > 100 * 1024 * 1024:  # 100MB limit
            return ToolResult(success=False, error=f"Result too large: {new_size} bytes")

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return ToolResult(
            success=True,
            data={
                "message": "Content inserted successfully",
                "path": str(file_path),
                "line_number": line_number,
                "inserted_content": content,
            },
            metadata={
                "operation": "insert_lines",
                "original_lines": len(lines) - 1,  # -1 because we added one
                "new_lines": len(lines),
            },
        )

    except Exception as e:
        logger.error(f"Insert lines error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register file management tools
file_mgmt_tools = [
    create_validated_tool(
        name="delete_file",
        description="Delete a file safely with security validation",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file to delete", "required": True},
        },
        required_params=["path"],
        execute_func=delete_file,
    ),
    create_validated_tool(
        name="move_file",
        description="Move or rename a file",
        category="file",
        parameters={
            "source": {"type": "string", "description": "Source file path", "required": True},
            "destination": {
                "type": "string",
                "description": "Destination file path",
                "required": True,
            },
        },
        required_params=["source", "destination"],
        execute_func=move_file,
    ),
    create_validated_tool(
        name="copy_file",
        description="Copy a file to a new location",
        category="file",
        parameters={
            "source": {"type": "string", "description": "Source file path", "required": True},
            "destination": {
                "type": "string",
                "description": "Destination file path",
                "required": True,
            },
        },
        required_params=["source", "destination"],
        execute_func=copy_file,
    ),
    create_validated_tool(
        name="create_directory",
        description="Create a directory and parent directories if needed",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Directory path to create", "required": True},
        },
        required_params=["path"],
        execute_func=create_directory,
    ),
    create_validated_tool(
        name="read_multiple_files",
        description="Read multiple files efficiently in batch",
        category="file",
        parameters={
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to read",
                "required": True,
            },
        },
        required_params=["paths"],
        execute_func=read_multiple_files,
    ),
    create_validated_tool(
        name="insert_lines",
        description="Insert content at specific line number in file",
        category="file",
        parameters={
            "path": {"type": "string", "description": "File path", "required": True},
            "line_number": {
                "type": "integer",
                "description": "Line number to insert at",
                "required": True,
            },
            "content": {"type": "string", "description": "Content to insert", "required": True},
        },
        required_params=["path", "line_number", "content"],
        execute_func=insert_lines,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in file_mgmt_tools:
    register_tool(tool)
