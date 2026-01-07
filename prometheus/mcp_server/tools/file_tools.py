"""
File Operations Tools for MCP Server
Complete file system manipulation toolkit

This module provides 10 essential file operations tools with
security validation, encoding detection, and safe path handling.
"""

import shutil
import logging
from pathlib import Path
from typing import List, Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


def validate_safe_path(path: str, allow_root: bool = False) -> bool:
    """
    Validate that a path is safe to access.

    Args:
        path: File path to validate
        allow_root: Whether to allow root directory access

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Convert to absolute path
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
        ]

        if not allow_root:
            dangerous_patterns.append("/")

        path_str = str(abs_path)
        for pattern in dangerous_patterns:
            if path_str.startswith(pattern):
                logger.warning(f"Blocked access to dangerous path: {path_str}")
                return False

        # Check for directory traversal attempts
        if ".." in path_str:
            logger.warning(f"Blocked directory traversal attempt: {path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Path validation failed for {path}: {e}")
        return False


def detect_encoding(file_path: str) -> str:
    """
    Detect file encoding.

    Args:
        file_path: Path to file

    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    try:
        import chardet

        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            encoding = result.get("encoding", "utf-8")
            return encoding if encoding else "utf-8"
    except ImportError:
        logger.warning("chardet not available, using utf-8")
        return "utf-8"
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}")
        return "utf-8"


# Tool 1: Read File
async def read_file(
    path: str, offset: Optional[int] = None, limit: Optional[int] = None
) -> ToolResult:
    """Read file contents with optional offset and limit."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {path}")

        encoding = detect_encoding(str(file_path))

        with open(file_path, "r", encoding=encoding) as f:
            if offset is not None and limit is not None:
                lines = f.readlines()
                start = max(0, offset)
                end = min(len(lines), start + limit)
                content = "".join(lines[start:end])
            elif offset is not None:
                lines = f.readlines()
                content = "".join(lines[max(0, offset) :])
            elif limit is not None:
                content = f.read(limit)
            else:
                content = f.read()

        return ToolResult(
            success=True,
            data={"content": content, "encoding": encoding, "path": path},
            metadata={"size": file_path.stat().st_size},
        )

    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return ToolResult(success=False, error=f"Failed to read file: {str(e)}")


# Tool 2: Write File
async def write_file(
    path: str, content: str, encoding: str = "utf-8", create_dirs: bool = False
) -> ToolResult:
    """Write content to file, optionally creating directories."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        file_path = Path(path)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

        return ToolResult(
            success=True,
            data={"path": path, "encoding": encoding, "size": len(content)},
            metadata={"created": not file_path.exists()},
        )

    except Exception as e:
        logger.error(f"Failed to write file {path}: {e}")
        return ToolResult(success=False, error=f"Failed to write file: {str(e)}")


# Tool 3: Edit File
async def edit_file(
    path: str, old_string: str, new_string: str, replace_all: bool = False
) -> ToolResult:
    """Edit file by replacing text."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        encoding = detect_encoding(str(file_path))

        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = content.count(old_string)
        else:
            # Replace only first occurrence
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1 if old_string in content else 0

        if replacements == 0:
            return ToolResult(success=False, error=f"String not found in file: {old_string}")

        with open(file_path, "w", encoding=encoding) as f:
            f.write(new_content)

        return ToolResult(
            success=True,
            data={"path": path, "replacements": replacements},
            metadata={"encoding": encoding},
        )

    except Exception as e:
        logger.error(f"Failed to edit file {path}: {e}")
        return ToolResult(success=False, error=f"Failed to edit file: {str(e)}")


# Tool 4: Delete File
async def delete_file(path: str, force: bool = False) -> ToolResult:
    """Delete a file or directory."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"Path not found: {path}")

        if file_path.is_file():
            file_path.unlink()
            item_type = "file"
        elif file_path.is_dir():
            if force:
                shutil.rmtree(file_path)
            else:
                file_path.rmdir()
            item_type = "directory"
        else:
            return ToolResult(success=False, error=f"Unknown file type: {path}")

        return ToolResult(success=True, data={"path": path, "type": item_type, "force": force})

    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return ToolResult(success=False, error=f"Failed to delete: {str(e)}")


# Tool 5: List Directory
async def list_directory(
    path: str, pattern: Optional[str] = None, recursive: bool = False
) -> ToolResult:
    """List directory contents with optional filtering."""
    if not validate_safe_path(path, allow_root=True):  # Allow root for listing
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")

        if not dir_path.is_dir():
            return ToolResult(success=False, error=f"Path is not a directory: {path}")

        if recursive:
            if pattern:
                items = list(dir_path.rglob(pattern))
            else:
                items = list(dir_path.rglob("*"))
        else:
            if pattern:
                items = list(dir_path.glob(pattern))
            else:
                items = list(dir_path.iterdir())

        # Convert to dict format
        contents = []
        for item in items:
            try:
                stat = item.stat()
                contents.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": stat.st_mtime,
                    }
                )
            except Exception:
                # Skip items we can't stat
                continue

        return ToolResult(
            success=True,
            data={"path": path, "contents": contents, "count": len(contents)},
            metadata={"recursive": recursive, "pattern": pattern},
        )

    except Exception as e:
        logger.error(f"Failed to list directory {path}: {e}")
        return ToolResult(success=False, error=f"Failed to list directory: {str(e)}")


# Tool 6: Move File
async def move_file(source: str, destination: str, overwrite: bool = False) -> ToolResult:
    """Move file or directory to new location."""
    if not validate_safe_path(source) or not validate_safe_path(destination):
        return ToolResult(success=False, error=f"Unsafe path(s): {source} -> {destination}")

    try:
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return ToolResult(success=False, error=f"Source not found: {source}")

        if dst_path.exists() and not overwrite:
            return ToolResult(success=False, error=f"Destination exists: {destination}")

        shutil.move(str(src_path), str(dst_path))

        return ToolResult(
            success=True,
            data={"source": source, "destination": destination, "overwrite": overwrite},
        )

    except Exception as e:
        logger.error(f"Failed to move {source} to {destination}: {e}")
        return ToolResult(success=False, error=f"Failed to move: {str(e)}")


# Tool 7: Copy File
async def copy_file(source: str, destination: str, overwrite: bool = False) -> ToolResult:
    """Copy file or directory to new location."""
    if not validate_safe_path(source) or not validate_safe_path(destination):
        return ToolResult(success=False, error=f"Unsafe path(s): {source} -> {destination}")

    try:
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return ToolResult(success=False, error=f"Source not found: {source}")

        if dst_path.exists() and not overwrite:
            return ToolResult(success=False, error=f"Destination exists: {destination}")

        if src_path.is_file():
            shutil.copy2(str(src_path), str(dst_path))
        elif src_path.is_dir():
            shutil.copytree(str(src_path), str(dst_path))
        else:
            return ToolResult(success=False, error=f"Unknown source type: {source}")

        return ToolResult(
            success=True,
            data={
                "source": source,
                "destination": destination,
                "type": "directory" if src_path.is_dir() else "file",
            },
        )

    except Exception as e:
        logger.error(f"Failed to copy {source} to {destination}: {e}")
        return ToolResult(success=False, error=f"Failed to copy: {str(e)}")


# Tool 8: Create Directory
async def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> ToolResult:
    """Create a new directory."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=parents, exist_ok=exist_ok)

        return ToolResult(
            success=True,
            data={"path": path, "created": not dir_path.exists()},
            metadata={"parents": parents, "exist_ok": exist_ok},
        )

    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return ToolResult(success=False, error=f"Failed to create directory: {str(e)}")


# Tool 9: Read Multiple Files
async def read_multiple_files(paths: List[str], encoding: Optional[str] = None) -> ToolResult:
    """Read multiple files in batch."""
    results = {}
    errors = []

    for path in paths:
        if not validate_safe_path(path):
            errors.append(f"Unsafe path: {path}")
            continue

        try:
            file_path = Path(path)
            if not file_path.exists():
                errors.append(f"File not found: {path}")
                continue

            file_encoding = encoding or detect_encoding(str(file_path))
            with open(file_path, "r", encoding=file_encoding) as f:
                content = f.read()

            results[path] = {"content": content, "encoding": file_encoding, "size": len(content)}

        except Exception as e:
            errors.append(f"Failed to read {path}: {str(e)}")

    return ToolResult(
        success=len(errors) == 0,
        data={"files": results, "errors": errors},
        metadata={"total_files": len(paths), "successful_reads": len(results)},
    )


# Tool 10: Insert Lines
async def insert_lines(
    path: str, lines: List[str], position: int = -1, encoding: Optional[str] = None
) -> ToolResult:
    """Insert lines at specific position in file."""
    if not validate_safe_path(path):
        return ToolResult(success=False, error=f"Unsafe path: {path}")

    try:
        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        file_encoding = encoding or detect_encoding(str(file_path))

        with open(file_path, "r", encoding=file_encoding) as f:
            existing_lines = f.readlines()

        if position == -1:
            # Append to end
            existing_lines.extend(line + "\n" for line in lines)
        else:
            # Insert at position
            pos = max(0, min(position, len(existing_lines)))
            for i, line in enumerate(lines):
                existing_lines.insert(pos + i, line + "\n")

        with open(file_path, "w", encoding=file_encoding) as f:
            f.writelines(existing_lines)

        return ToolResult(
            success=True,
            data={"path": path, "lines_inserted": len(lines), "position": position},
            metadata={"encoding": file_encoding, "total_lines": len(existing_lines)},
        )

    except Exception as e:
        logger.error(f"Failed to insert lines in {path}: {e}")
        return ToolResult(success=False, error=f"Failed to insert lines: {str(e)}")


# Create and register all file tools
file_tools = [
    create_validated_tool(
        name="read_file",
        description="Read file contents with optional offset and limit",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file to read"},
            "offset": {
                "type": "integer",
                "description": "Line offset to start reading from (0-based)",
            },
            "limit": {"type": "integer", "description": "Maximum number of lines to read"},
        },
        required_params=["path"],
        execute_func=read_file,
    ),
    create_validated_tool(
        name="write_file",
        description="Write content to file, optionally creating directories",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file to write"},
            "content": {"type": "string", "description": "Content to write to file"},
            "encoding": {
                "type": "string",
                "description": "Text encoding (default: utf-8)",
                "default": "utf-8",
            },
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories if they don't exist",
                "default": False,
            },
        },
        required_params=["path", "content"],
        execute_func=write_file,
    ),
    create_validated_tool(
        name="edit_file",
        description="Edit file by replacing text",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file to edit"},
            "old_string": {"type": "string", "description": "String to replace"},
            "new_string": {"type": "string", "description": "Replacement string"},
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences",
                "default": False,
            },
        },
        required_params=["path", "old_string", "new_string"],
        execute_func=edit_file,
    ),
    create_validated_tool(
        name="delete_file",
        description="Delete a file or directory",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file/directory to delete"},
            "force": {
                "type": "boolean",
                "description": "Force delete non-empty directories",
                "default": False,
            },
        },
        required_params=["path"],
        execute_func=delete_file,
    ),
    create_validated_tool(
        name="list_directory",
        description="List directory contents with optional filtering",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to directory to list"},
            "pattern": {"type": "string", "description": "Glob pattern to filter results"},
            "recursive": {"type": "boolean", "description": "List recursively", "default": False},
        },
        required_params=["path"],
        execute_func=list_directory,
    ),
    create_validated_tool(
        name="move_file",
        description="Move file or directory to new location",
        category="file",
        parameters={
            "source": {"type": "string", "description": "Source path"},
            "destination": {"type": "string", "description": "Destination path"},
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite destination if exists",
                "default": False,
            },
        },
        required_params=["source", "destination"],
        execute_func=move_file,
    ),
    create_validated_tool(
        name="copy_file",
        description="Copy file or directory to new location",
        category="file",
        parameters={
            "source": {"type": "string", "description": "Source path"},
            "destination": {"type": "string", "description": "Destination path"},
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite destination if exists",
                "default": False,
            },
        },
        required_params=["source", "destination"],
        execute_func=copy_file,
    ),
    create_validated_tool(
        name="create_directory",
        description="Create a new directory",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to directory to create"},
            "parents": {
                "type": "boolean",
                "description": "Create parent directories",
                "default": True,
            },
            "exist_ok": {
                "type": "boolean",
                "description": "Don't error if directory exists",
                "default": True,
            },
        },
        required_params=["path"],
        execute_func=create_directory,
    ),
    create_validated_tool(
        name="read_multiple_files",
        description="Read multiple files in batch",
        category="file",
        parameters={
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to read",
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding (auto-detect if not specified)",
            },
        },
        required_params=["paths"],
        execute_func=read_multiple_files,
    ),
    create_validated_tool(
        name="insert_lines",
        description="Insert lines at specific position in file",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file to modify"},
            "lines": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lines to insert",
            },
            "position": {
                "type": "integer",
                "description": "Line position to insert at (-1 for append)",
                "default": -1,
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding (auto-detect if not specified)",
            },
        },
        required_params=["path", "lines"],
        execute_func=insert_lines,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in file_tools:
    register_tool(tool)
