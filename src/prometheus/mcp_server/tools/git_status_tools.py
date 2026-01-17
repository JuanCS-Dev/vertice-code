"""
Git Status Tools for MCP Server
Git status and information operations

This module provides git status, diff, and log operations with
safety validation and structured output formatting.
"""

import logging
from typing import Optional
from .base import ToolResult
from .validated import create_validated_tool
from .git_safety import run_git_command

logger = logging.getLogger(__name__)


async def git_status(path: str = ".") -> ToolResult:
    """Get git repository status."""
    try:
        success, stdout, stderr = run_git_command(["git", "status", "--porcelain"], path)
        if not success:
            return ToolResult(success=False, error=f"Git status failed: {stderr}")

        # Get branch info
        branch_success, branch_stdout, _ = run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], path
        )
        branch = branch_stdout.strip() if branch_success else "unknown"

        # Parse status output
        files_changed = []
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    files_changed.append({"status": status, "file": filename})

        return ToolResult(
            success=True,
            data={
                "branch": branch,
                "clean": len(files_changed) == 0,
                "files_changed": files_changed,
                "total_changes": len(files_changed),
            },
            metadata={
                "repo_path": path,
                "command": "git status",
            },
        )
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_diff(path: str = ".", staged: bool = False) -> ToolResult:
    """Get git diff output."""
    try:
        command = ["git", "diff"]
        if staged:
            command.append("--staged")

        success, stdout, stderr = run_git_command(command, path)
        if not success:
            return ToolResult(success=False, error=f"Git diff failed: {stderr}")

        return ToolResult(
            success=True,
            data={
                "diff": stdout,
                "has_changes": bool(stdout.strip()),
                "staged": staged,
            },
            metadata={
                "repo_path": path,
                "command": f"git diff {'--staged' if staged else ''}",
                "diff_size": len(stdout),
            },
        )
    except Exception as e:
        logger.error(f"Git diff error: {e}")
        return ToolResult(success=False, error=str(e))


async def git_log(
    path: str = ".", max_count: int = 10, author: Optional[str] = None, since: Optional[str] = None
) -> ToolResult:
    """Get git commit log."""
    try:
        command = ["git", "log", "--oneline", f"-{max_count}"]

        if author:
            command.extend(["--author", author])
        if since:
            command.extend(["--since", since])

        success, stdout, stderr = run_git_command(command, path)
        if not success:
            return ToolResult(success=False, error=f"Git log failed: {stderr}")

        # Parse log output
        commits = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    commit_hash, message = parts
                    commits.append(
                        {
                            "hash": commit_hash,
                            "message": message,
                        }
                    )

        return ToolResult(
            success=True,
            data={
                "commits": commits,
                "total_commits": len(commits),
                "max_count": max_count,
            },
            metadata={
                "repo_path": path,
                "command": " ".join(command),
                "filters": {
                    "author": author,
                    "since": since,
                },
            },
        )
    except Exception as e:
        logger.error(f"Git log error: {e}")
        return ToolResult(success=False, error=str(e))


# Create and register git status tools
git_status_tools = [
    create_validated_tool(
        name="git_status",
        description="Get git repository status with branch info and changed files",
        category="git",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": ".",
            },
        },
        required_params=[],
        execute_func=git_status,
    ),
    create_validated_tool(
        name="git_diff",
        description="Get git diff output for unstaged or staged changes",
        category="git",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": ".",
            },
            "staged": {
                "type": "boolean",
                "description": "Show staged changes instead of unstaged",
                "default": False,
            },
        },
        required_params=[],
        execute_func=git_diff,
    ),
    create_validated_tool(
        name="git_log",
        description="Get git commit log with filtering options",
        category="git",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": ".",
            },
            "max_count": {
                "type": "integer",
                "description": "Maximum number of commits to show",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "author": {
                "type": "string",
                "description": "Filter by author",
            },
            "since": {
                "type": "string",
                "description": "Show commits since date (e.g., '1 week ago', '2024-01-01')",
            },
        },
        required_params=[],
        execute_func=git_log,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in git_status_tools:
    register_tool(tool)
