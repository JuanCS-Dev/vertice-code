"""File management tools - move, copy, create dirs."""

import shutil
from pathlib import Path
from typing import Any, Dict

from .base import ToolResult, ToolCategory
from .validated import ValidatedTool
from ..core.validation import (
    InputValidator,
    ValidationResult,
    Required,
    TypeCheck,
)


class MoveFileTool(ValidatedTool):
    """Move or rename file."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.FILE_MGMT
        self.description = "Move or rename file"
        self.parameters = {
            "source": {"type": "string", "description": "Source file path", "required": True},
            "destination": {
                "type": "string",
                "description": "Destination file path",
                "required": True,
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite if destination exists",
                "required": False,
            },
        }

    def get_validators(self) -> Dict[str, Any]:
        """Validate parameters - P1 FIX: Proper validation."""
        return {
            "source": Required("source"),
            "destination": Required("destination"),
        }

    async def _execute_validated(
        self, source: str, destination: str, overwrite: bool = False
    ) -> ToolResult:
        """Move/rename file."""
        try:
            src = Path(source)
            dst = Path(destination)

            # P1: Path validation
            if not src.exists():
                return ToolResult(success=False, error=f"Source not found: {source}")

            if dst.exists() and not overwrite:
                return ToolResult(success=False, error=f"Destination exists: {destination}")

            shutil.move(str(src), str(dst))

            return ToolResult(
                success=True,
                data=f"Moved {source} → {destination}",
                metadata={"source": str(src), "destination": str(dst)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CopyFileTool(ValidatedTool):
    """Copy file to new location."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.FILE_MGMT
        self.description = "Copy file to new location"
        self.parameters = {
            "source": {"type": "string", "description": "Source file path", "required": True},
            "destination": {
                "type": "string",
                "description": "Destination file path",
                "required": True,
            },
        }

    def get_validators(self) -> Dict[str, Any]:
        """Validate parameters - P1 FIX: Proper validation."""
        return {
            "source": Required("source"),
            "destination": Required("destination"),
        }

    async def _execute_validated(self, source: str, destination: str) -> ToolResult:
        """Copy file."""
        try:
            src = Path(source)
            dst = Path(destination)

            # P1: Path validation
            if not src.exists():
                return ToolResult(success=False, error=f"Source not found: {source}")

            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                shutil.copy2(str(src), str(dst))

            return ToolResult(
                success=True,
                data=f"Copied {source} → {destination}",
                metadata={"source": str(src), "destination": str(dst)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateDirectoryTool(ValidatedTool):
    """Create new directory."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.FILE_MGMT
        self.description = "Create new directory"
        self.parameters = {
            "path": {"type": "string", "description": "Directory path to create", "required": True},
            "recursive": {
                "type": "boolean",
                "description": "Create parent directories if needed",
                "required": False,
            },
        }

    def get_validators(self) -> Dict[str, Any]:
        """Validate parameters - P1 FIX: Proper validation."""
        return {
            "path": Required("path"),
        }

    async def _execute_validated(self, path: str, recursive: bool = True) -> ToolResult:
        """Create directory."""
        try:
            dir_path = Path(path)

            if dir_path.exists():
                return ToolResult(success=False, error=f"Directory already exists: {path}")

            dir_path.mkdir(parents=recursive, exist_ok=False)

            return ToolResult(
                success=True, data=f"Created directory: {path}", metadata={"path": str(dir_path)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadMultipleFilesTool(ValidatedTool):
    """Read multiple files at once."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.FILE_READ
        self.description = "Read multiple files at once (batch operation)"
        self.parameters = {
            "paths": {
                "type": "array",
                "description": "Array of file paths to read",
                "required": True,
            },
            "max_files": {
                "type": "integer",
                "description": "Maximum number of files to read",
                "required": False,
            },
        }

    def get_validators(self) -> Dict[str, Any]:
        """Validate parameters - P1 FIX: Proper validation."""
        return {
            "paths": Required("paths"),
        }

    async def _execute_validated(self, paths: list[str], max_files: int = 10) -> ToolResult:
        """Read multiple files."""
        try:
            if len(paths) > max_files:
                return ToolResult(
                    success=False, error=f"Too many files requested (max {max_files})"
                )

            results = []
            for path in paths:
                file_path = Path(path)

                if not file_path.exists():
                    results.append({"path": path, "error": "File not found"})
                    continue

                try:
                    content = file_path.read_text()
                    results.append(
                        {
                            "path": path,
                            "content": content,
                            "lines": len(content.split("\n")),
                            "size": file_path.stat().st_size,
                        }
                    )
                except Exception as e:
                    results.append({"path": path, "error": str(e)})

            # P1 FIX: Properly report partial failures
            files_read = len([r for r in results if "content" in r])
            files_failed = len([r for r in results if "error" in r])

            return ToolResult(
                success=files_read > 0,  # Only success if at least one file read
                data=results,
                metadata={
                    "files_read": files_read,
                    "files_failed": files_failed,
                    "partial_failure": files_failed > 0 and files_read > 0,
                },
                error=f"{files_failed} file(s) failed to read" if files_failed > 0 else None,
            )
        except (OSError, IOError, ValueError, TypeError) as e:
            return ToolResult(success=False, error=str(e))


class InsertLinesTool(ValidatedTool):
    """Insert lines at specific position in file."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.FILE_WRITE
        self.description = "Insert lines at specific position in file"
        self.parameters = {
            "path": {"type": "string", "description": "File path", "required": True},
            "line_number": {
                "type": "integer",
                "description": "Line number to insert before (1-indexed)",
                "required": True,
            },
            "content": {"type": "string", "description": "Content to insert", "required": True},
        }

    def get_validators(self) -> Dict[str, Any]:
        """Validate parameters - P1 FIX: Proper validation."""
        return {
            "path": Required("path"),
            "line_number": Required("line_number"),
            "content": Required("content"),
        }

    async def _execute_validated(self, path: str, line_number: int, content: str) -> ToolResult:
        """Insert lines at position."""
        try:
            file_path = Path(path)

            # P1: File existence validation
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")

            # P1: Line number must be positive
            if line_number < 1:
                return ToolResult(
                    success=False, error=f"Line number must be >= 1, got {line_number}"
                )

            # Read current content
            lines = file_path.read_text().split("\n")

            # P1 FIX: Bounds validation - line_number must be within valid range
            # Allow inserting at end (line_number == len(lines) + 1)
            if line_number > len(lines) + 1:
                return ToolResult(
                    success=False,
                    error=f"Line number {line_number} exceeds file length ({len(lines)} lines). "
                    f"Use line_number {len(lines) + 1} to append at end.",
                )

            # Insert new content
            insert_lines = content.split("\n")
            lines[line_number - 1 : line_number - 1] = insert_lines

            # Write back
            file_path.write_text("\n".join(lines))

            return ToolResult(
                success=True,
                data=f"Inserted {len(insert_lines)} lines at line {line_number}",
                metadata={
                    "path": str(file_path),
                    "line_number": line_number,
                    "lines_inserted": len(insert_lines),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
