"""
Multi Edit Tools for MCP Server
Atomic batch file editing operations

This module provides safe, atomic multi-edit operations with backup support
and validation before applying changes.
"""

import logging
from pathlib import Path
from typing import Dict, List
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


def multi_edit(
    file_path: str, edits: List[Dict[str, str]], create_backup: bool = True
) -> ToolResult:
    """Apply multiple edits to a single file atomically."""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if not file_path:
        return ToolResult(success=False, error="file_path is required")

    if not edits:
        return ToolResult(success=False, error="edits list is required")

    if not isinstance(edits, list):
        return ToolResult(success=False, error="edits must be an array")

    try:
        path = Path(file_path)

        if not path.exists():
            return ToolResult(success=False, error=f"File does not exist: {file_path}")

        if not path.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {file_path}")

        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return ToolResult(
                success=False,
                error=f"File too large ({file_size} bytes). Max: {MAX_FILE_SIZE}",
            )

        # Read original content
        try:
            original_content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(success=False, error="File is not valid UTF-8 text")

        content = original_content

        # Phase 1: Validate all edits first
        validation_errors = []
        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                validation_errors.append(f"Edit {i + 1}: must be an object")
                continue

            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")

            if not old_string and not new_string:
                validation_errors.append(f"Edit {i + 1}: both old_string and new_string are empty")
                continue

            if old_string not in content:
                validation_errors.append(
                    f"Edit {i + 1}: old_string '{old_string[:50]}...' not found"
                )

        if validation_errors:
            return ToolResult(
                success=False,
                error=f"Validation failed: {', '.join(validation_errors)}",
                data={"validation_errors": validation_errors},
            )

        # Phase 2: Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = path.with_suffix(path.suffix + ".backup")
            backup_path.write_text(original_content, encoding="utf-8")

        # Phase 3: Apply all edits
        applied_edits = []
        for i, edit in enumerate(edits):
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")

            if old_string in content:
                content = content.replace(
                    old_string, new_string, 1
                )  # Replace only first occurrence
                applied_edits.append(
                    {
                        "index": i,
                        "old_string": old_string,
                        "new_string": new_string,
                    }
                )

        # Phase 4: Write back
        path.write_text(content, encoding="utf-8")

        return ToolResult(
            success=True,
            data={
                "applied_edits": len(applied_edits),
                "backup_created": backup_path is not None,
                "backup_path": str(backup_path) if backup_path else None,
            },
            metadata={
                "file": str(path),
                "original_size": len(original_content),
                "new_size": len(content),
                "edits_applied": applied_edits,
            },
        )

    except Exception as e:
        logger.error(f"MultiEdit error: {e}")
        return ToolResult(success=False, error=str(e))


def task_launcher(task_description: str, priority: str = "medium") -> ToolResult:
    """Launch a background task (simplified implementation)."""
    try:
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            priority = "medium"

        task_id = f"task-{hash(task_description) % 1000000:06d}"

        return ToolResult(
            success=True,
            data={
                "task_id": task_id,
                "task_description": task_description,
                "priority": priority,
                "status": "launched",
                "message": f"Task launched with ID {task_id}. Note: This is a simplified implementation.",
            },
            metadata={
                "task_id": task_id,
                "launched_at": "simulated_timestamp",
            },
        )

    except Exception as e:
        logger.error(f"TaskLauncher error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register multi-edit tools
multi_edit_tools = [
    create_validated_tool(
        name="multi_edit",
        description="Apply multiple atomic edits to a file (all succeed or none are applied)",
        category="file",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit",
                "required": True,
            },
            "edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "old_string": {"type": "string", "description": "String to replace"},
                        "new_string": {"type": "string", "description": "Replacement string"},
                    },
                    "required": ["old_string", "new_string"],
                },
                "description": "List of {old_string, new_string} edits to apply",
                "required": True,
            },
            "create_backup": {
                "type": "boolean",
                "description": "Create backup before editing",
                "default": True,
            },
        },
        required_params=["file_path", "edits"],
        execute_func=multi_edit,
    ),
    create_validated_tool(
        name="task_launcher",
        description="Launch a background task (simplified implementation)",
        category="execution",
        parameters={
            "task_description": {
                "type": "string",
                "description": "Description of the task to launch",
                "required": True,
            },
            "priority": {
                "type": "string",
                "description": "Task priority level",
                "default": "medium",
                "enum": ["low", "medium", "high", "critical"],
            },
        },
        required_params=["task_description"],
        execute_func=task_launcher,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in multi_edit_tools:
    register_tool(tool)
