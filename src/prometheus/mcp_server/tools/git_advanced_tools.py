"""
Git Advanced Operations for MCP Server
Commit, branch, and advanced git operations

This module provides advanced git operations with safety validation
and proper error handling.
"""

import logging
from typing import List, Optional
from .base import ToolResult
from .validated import create_validated_tool
from .git_safety import run_git_command, get_current_branch

logger = logging.getLogger(__name__)


def validate_commit_message(message: str) -> tuple[bool, str]:
    """Validate commit message according to standards."""
    if not message or not message.strip():
        return False, "Commit message cannot be empty"

    if len(message) > 50000:  # Reasonable limit
        return False, "Commit message too long"

    # Basic checks
    lines = message.split("\n")
    if len(lines) > 1 and lines[1].strip():  # Should have empty line after subject
        pass  # Allow multi-line for now

    return True, "Valid commit message"


async def git_add(path: str = ".", files: Optional[List[str]] = None) -> ToolResult:
    """Stage files for commit."""
    try:
        cmd = ["git", "-C", path, "add"]
        if files:
            cmd.extend(files)
        else:
            cmd.append(".")

        success, stdout, stderr = run_git_command(cmd)
        if not success:
            return ToolResult(success=False, error=f"Git add failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "message": "Files staged successfully",
                "files": files or ["."],
            },
            metadata={"repo_path": path, "operation": "add"},
        )

    except Exception as e:
        logger.error(f"Git add error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_reset(
    path: str = ".", files: Optional[List[str]] = None, mode: str = "mixed"
) -> ToolResult:
    """Reset files or commits."""
    try:
        # Safety check for dangerous operations
        if mode in ["hard", "merge", "keep"]:
            return ToolResult(
                success=False, error=f"Reset mode '{mode}' not allowed for safety reasons"
            )

        cmd = ["git", "-C", path, "reset", f"--{mode}"]
        if files:
            cmd.extend(files)

        success, stdout, stderr = run_git_command(cmd)
        if not success:
            return ToolResult(success=False, error=f"Git reset failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "message": f"Reset completed with mode '{mode}'",
                "files": files or ["all"],
                "mode": mode,
            },
            metadata={"repo_path": path, "operation": "reset", "mode": mode},
        )

    except Exception as e:
        logger.error(f"Git reset error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_commit(
    message: str, path: str = ".", amend: bool = False, allow_empty: bool = False
) -> ToolResult:
    """Create a git commit."""
    try:
        # Validate commit message
        is_valid, error_msg = validate_commit_message(message)
        if not is_valid:
            return ToolResult(success=False, error=error_msg)

        cmd = ["git", "-C", path, "commit", "-m", message]

        if amend:
            cmd.append("--amend")
        if allow_empty:
            cmd.append("--allow-empty")

        success, stdout, stderr = run_git_command(cmd)
        if not success:
            return ToolResult(success=False, error=f"Git commit failed: {stderr}")

        # Extract commit hash from output
        commit_hash = None
        for line in stdout.split("\n"):
            if line.startswith("[") and "]" in line:
                # Format: [branch hash] message
                parts = line.split()
                if len(parts) >= 2 and len(parts[1]) >= 7:  # hash should be at least 7 chars
                    commit_hash = parts[1][:7]  # Short hash
                    break

        return ToolResult(
            success=True,
            data={
                "message": "Commit created successfully",
                "commit_hash": commit_hash,
                "amended": amend,
                "allow_empty": allow_empty,
            },
            metadata={
                "repo_path": path,
                "operation": "commit",
                "commit_hash": commit_hash,
            },
        )

    except Exception as e:
        logger.error(f"Git commit error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_branch_create(
    name: str, path: str = ".", start_point: Optional[str] = None
) -> ToolResult:
    """Create a new git branch."""
    try:
        if not name or not name.strip():
            return ToolResult(success=False, error="Branch name cannot be empty")

        # Validate branch name (basic check)
        if any(
            char in name for char in [" ", "\t", "\n", "\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        ):
            return ToolResult(success=False, error="Branch name contains invalid characters")

        cmd = ["git", "-C", path, "checkout", "-b", name]
        if start_point:
            cmd = ["git", "-C", path, "checkout", "-b", name, start_point]

        success, stdout, stderr = run_git_command(cmd)
        if not success:
            return ToolResult(success=False, error=f"Git branch creation failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "message": f"Branch '{name}' created successfully",
                "branch_name": name,
                "start_point": start_point,
            },
            metadata={"repo_path": path, "operation": "branch_create"},
        )

    except Exception as e:
        logger.error(f"Git branch create error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_branch_switch(name: str, path: str = ".") -> ToolResult:
    """Switch to a git branch."""
    try:
        current_branch = get_current_branch(path)

        cmd = ["git", "-C", path, "checkout", name]
        success, stdout, stderr = run_git_command(cmd)

        if not success:
            return ToolResult(success=False, error=f"Git checkout failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "message": f"Switched to branch '{name}'",
                "previous_branch": current_branch,
                "current_branch": name,
            },
            metadata={"repo_path": path, "operation": "checkout"},
        )

    except Exception as e:
        logger.error(f"Git checkout error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_merge(source: str, path: str = ".", strategy: Optional[str] = None) -> ToolResult:
    """Merge a branch into current branch."""
    try:
        cmd = ["git", "-C", path, "merge", source]

        if strategy:
            cmd.extend(["--strategy", strategy])

        success, stdout, stderr = run_git_command(cmd)
        if not success:
            return ToolResult(success=False, error=f"Git merge failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "message": f"Merge of '{source}' completed",
                "source_branch": source,
                "strategy": strategy,
            },
            metadata={"repo_path": path, "operation": "merge"},
        )

    except Exception as e:
        logger.error(f"Git merge error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register advanced git tools
git_advanced_tools = [
    create_validated_tool(
        name="git_add",
        description="Stage files for commit",
        category="git",
        parameters={
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to stage (empty stages all changes)",
            },
        },
        required_params=[],
        execute_func=git_add,
    ),
    create_validated_tool(
        name="git_reset",
        description="Reset files or commits (safe modes only)",
        category="git",
        parameters={
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to reset (empty resets all)",
            },
            "mode": {
                "type": "string",
                "description": "Reset mode",
                "default": "mixed",
                "enum": ["soft", "mixed", "hard"],
            },
        },
        required_params=[],
        execute_func=git_reset,
    ),
    create_validated_tool(
        name="git_commit",
        description="Create a git commit with message validation",
        category="git",
        parameters={
            "message": {"type": "string", "description": "Commit message", "required": True},
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
            "amend": {
                "type": "boolean",
                "description": "Amend previous commit",
                "default": False,
            },
            "allow_empty": {
                "type": "boolean",
                "description": "Allow empty commits",
                "default": False,
            },
        },
        required_params=["message"],
        execute_func=git_commit,
    ),
    create_validated_tool(
        name="git_branch_create",
        description="Create a new git branch",
        category="git",
        parameters={
            "name": {"type": "string", "description": "Branch name", "required": True},
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
            "start_point": {"type": "string", "description": "Starting point (commit/branch)"},
        },
        required_params=["name"],
        execute_func=git_branch_create,
    ),
    create_validated_tool(
        name="git_branch_switch",
        description="Switch to a different git branch",
        category="git",
        parameters={
            "name": {"type": "string", "description": "Branch name to switch to", "required": True},
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
        },
        required_params=["name"],
        execute_func=git_branch_switch,
    ),
    create_validated_tool(
        name="git_merge",
        description="Merge a branch into current branch",
        category="git",
        parameters={
            "source": {"type": "string", "description": "Source branch to merge", "required": True},
            "path": {"type": "string", "description": "Path to git repository", "default": "."},
            "strategy": {"type": "string", "description": "Merge strategy"},
        },
        required_params=["source"],
        execute_func=git_merge,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in git_advanced_tools:
    register_tool(tool)
