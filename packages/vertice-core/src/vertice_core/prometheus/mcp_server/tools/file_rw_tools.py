"""
File Read/Write Tools for MCP Server
Basic file operations with security validation

This module provides safe file reading and writing operations
with encoding detection and path validation.
"""

import logging
from pathlib import Path
from typing import Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


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
            # Resolve symlink to check target
            try:
                target = abs_path.readlink()
                if any(pattern in str(target) for pattern in dangerous_patterns):
                    return False
            except Exception as e:
                return False

        return True

    except Exception as e:
        return False


def detect_encoding(file_path: str) -> str:
    """Detect file encoding using chardet."""
    try:
        import chardet

        with open(file_path, "rb") as f:
            raw_data = f.read(10240)  # Read first 10KB
            result = chardet.detect(raw_data)
            encoding = result.get("encoding", "utf-8")
            confidence = result.get("confidence", 0.0)

            # Use detected encoding only if confidence is high enough
            if confidence > 0.7 and encoding:
                return encoding.lower()

    except ImportError:
        logger.warning("chardet not available, falling back to utf-8")
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}")

    return "utf-8"


async def read_file(
    path: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    encoding: Optional[str] = None,
) -> ToolResult:
    """Read file content with safety validation."""
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return ToolResult(success=False, error=f"File too large: {file_size} bytes")

        # Detect encoding if not provided
        if encoding is None:
            encoding = detect_encoding(str(file_path))

        # Read file content
        try:
            with open(file_path, "r", encoding=encoding) as f:
                if offset is not None or limit is not None:
                    # Partial read
                    start = offset or 0
                    end = (start + limit) if limit else None

                    f.seek(start)
                    if end:
                        content = f.read(end - start)
                    else:
                        content = f.read()
                else:
                    content = f.read()

        except UnicodeDecodeError:
            return ToolResult(success=False, error=f"Cannot decode file with {encoding} encoding")

        return ToolResult(
            success=True,
            data={
                "content": content,
                "path": str(file_path),
                "encoding": encoding,
                "size": len(content),
            },
            metadata={
                "file_size": file_size,
                "offset": offset,
                "limit": limit,
                "encoding_detected": encoding,
            },
        )

    except Exception as e:
        logger.error(f"Read file error: {e}")
        return ToolResult(success=False, error=str(e))


async def write_file(
    path: str, content: str, encoding: str = "utf-8", create_dirs: bool = False
) -> ToolResult:
    """Write content to file with safety validation."""
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        file_path = Path(path)

        # Create parent directories if requested
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Validate parent directory exists for writing
        if not file_path.parent.exists():
            return ToolResult(
                success=False, error=f"Parent directory does not exist: {file_path.parent}"
            )

        # Check if we're overwriting a critical file
        if file_path.exists():
            # Additional safety check for existing files
            critical_files = [
                "/etc/passwd",
                "/etc/shadow",
                "/etc/sudoers",
                "/boot/grub/grub.cfg",
                "/etc/fstab",
            ]
            if str(file_path) in critical_files:
                return ToolResult(
                    success=False, error=f"Cannot modify critical system file: {path}"
                )

        # Write file
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

        return ToolResult(
            success=True,
            data={
                "message": "File written successfully",
                "path": str(file_path),
                "size": len(content),
                "encoding": encoding,
            },
            metadata={
                "create_dirs": create_dirs,
                "overwritten": file_path.exists(),
            },
        )

    except Exception as e:
        logger.error(f"Write file error: {e}")
        return ToolResult(success=False, error=str(e))


async def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    encoding: str = "utf-8",
    replace_all: bool = False,
    create_backup: bool = True,
) -> ToolResult:
    """
    Edit file content by replacing strings with enhanced safety and flexibility.

    Args:
        path: File path to edit
        old_string: String to replace (cannot be empty)
        new_string: Replacement string
        encoding: File encoding
        replace_all: If True, replace all occurrences instead of just first
        create_backup: If True, create .bak file before editing
    """
    try:
        if not validate_safe_path(path):
            return ToolResult(success=False, error=f"Access denied to path: {path}")

        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {path}")

        # Validate old_string
        if not old_string:
            return ToolResult(success=False, error="old_string cannot be empty")

        # Read current content
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            return ToolResult(success=False, error=f"Cannot decode file with {encoding} encoding")

        original_size = len(content)

        # Check file size limits
        if original_size > 50 * 1024 * 1024:  # 50MB limit
            return ToolResult(success=False, error=f"File too large to edit: {original_size} bytes")

        # Find all occurrences for better error reporting
        occurrences = content.count(old_string)
        if occurrences == 0:
            return ToolResult(success=False, error=f"String '{old_string}' not found in file")

        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                backup_path.write_text(content, encoding=encoding)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                backup_path = None

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replaced_count = occurrences
        else:
            new_content = content.replace(old_string, new_string, 1)
            replaced_count = 1

        # Validate new content size
        new_size = len(new_content)
        if new_size > 100 * 1024 * 1024:  # 100MB limit for result
            # Clean up backup if created
            if backup_path and backup_path.exists():
                backup_path.unlink()
            return ToolResult(success=False, error=f"Result too large: {new_size} bytes")

        # Write back
        try:
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)
        except Exception as e:
            # Restore from backup if available
            if backup_path and backup_path.exists():
                try:
                    backup_content = backup_path.read_text(encoding=encoding)
                    file_path.write_text(backup_content, encoding=encoding)
                    backup_path.unlink()
                except Exception as e:
                    pass  # Backup restoration failed
            raise e

        return ToolResult(
            success=True,
            data={
                "message": "File edited successfully",
                "path": str(file_path),
                "old_string": old_string,
                "new_string": new_string,
                "occurrences_found": occurrences,
                "occurrences_replaced": replaced_count,
                "backup_created": backup_path.name if backup_path else None,
            },
            metadata={
                "encoding": encoding,
                "original_size": original_size,
                "new_size": new_size,
                "replace_all": replace_all,
                "create_backup": create_backup,
            },
        )

    except Exception as e:
        logger.error(f"Edit file error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register file read/write tools
file_rw_tools = [
    create_validated_tool(
        name="read_file",
        description="Read file content with encoding detection and safety validation",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file", "required": True},
            "offset": {"type": "integer", "description": "Start offset for partial read"},
            "limit": {"type": "integer", "description": "Maximum bytes to read"},
            "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
        },
        required_params=["path"],
        execute_func=read_file,
    ),
    create_validated_tool(
        name="write_file",
        description="Write content to file with safety validation",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file", "required": True},
            "content": {"type": "string", "description": "Content to write", "required": True},
            "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories",
                "default": False,
            },
        },
        required_params=["path", "content"],
        execute_func=write_file,
    ),
    create_validated_tool(
        name="edit_file",
        description="Edit file content by replacing strings with safety features",
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to file", "required": True},
            "old_string": {"type": "string", "description": "String to replace", "required": True},
            "new_string": {"type": "string", "description": "Replacement string", "required": True},
            "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences instead of just first",
                "default": False,
            },
            "create_backup": {
                "type": "boolean",
                "description": "Create backup file before editing",
                "default": True,
            },
        },
        required_params=["path", "old_string", "new_string"],
        execute_func=edit_file,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in file_rw_tools:
    register_tool(tool)
