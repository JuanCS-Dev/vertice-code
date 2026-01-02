"""
Tool Result Formatters - Transform tool results to display strings.

Design Principles:
- Pure functions where possible (easy to test)
- Strategy pattern for tool-specific formatting
- Clear, consistent output format
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class ToolResult(Protocol):
    """Protocol for tool results."""

    success: bool
    data: Any
    metadata: Dict[str, Any]
    error: Optional[str]


@dataclass
class FormattedResult:
    """Formatted tool result."""

    summary: str
    details: Optional[str] = None
    success: bool = True


class ToolFormatter(ABC):
    """Base class for tool-specific formatters."""

    @abstractmethod
    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        """Format tool result for display."""
        pass


class ReadFileFormatter(ToolFormatter):
    """Formatter for read_file tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        path = result.metadata.get("path", args.get("path", "file"))
        lines = result.metadata.get("lines", "?")
        return FormattedResult(
            summary=f"Read {path} ({lines} lines)",
            details=str(result.data) if result.data else None,
        )


class WriteFileFormatter(ToolFormatter):
    """Formatter for write_file and edit_file tools."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        summary = str(result.data)
        details = None
        if result.metadata.get("backup"):
            details = f"Backup: {result.metadata['backup']}"
        return FormattedResult(summary=summary, details=details)


class SearchFormatter(ToolFormatter):
    """Formatter for search_files tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        pattern = args.get("pattern", "?")
        count = result.metadata.get("count", len(result.data) if result.data else 0)
        return FormattedResult(
            summary=f"Found {count} matches for '{pattern}'",
            details=None,
        )


class BashFormatter(ToolFormatter):
    """Formatter for bash_command tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        data = result.data or {}
        exit_code = data.get("exit_code", 0)
        stdout = data.get("stdout", "")
        stderr = data.get("stderr", "")

        details_parts = []
        if stdout:
            details_parts.append(f"stdout:\n{stdout}")
        if stderr:
            details_parts.append(f"stderr:\n{stderr}")

        return FormattedResult(
            summary=f"Exit code: {exit_code}",
            details="\n".join(details_parts) if details_parts else None,
            success=exit_code == 0,
        )


class GitStatusFormatter(ToolFormatter):
    """Formatter for git_status tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        data = result.data or {}
        branch = data.get("branch", "unknown")
        modified = data.get("modified", [])
        untracked = data.get("untracked", [])
        staged = data.get("staged", [])

        details_parts = [f"Branch: {branch}"]
        if modified:
            details_parts.append(f"Modified: {', '.join(modified)}")
        if untracked:
            details_parts.append(f"Untracked: {', '.join(untracked)}")
        if staged:
            details_parts.append(f"Staged: {', '.join(staged)}")

        return FormattedResult(
            summary="Git status retrieved",
            details="\n".join(details_parts),
        )


class GitDiffFormatter(ToolFormatter):
    """Formatter for git_diff tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        if result.data:
            return FormattedResult(
                summary="Diff shown",
                details=str(result.data),
            )
        return FormattedResult(summary="No changes")


class ListDirectoryFormatter(ToolFormatter):
    """Formatter for list_directory tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        file_count = result.metadata.get("file_count", 0)
        dir_count = result.metadata.get("dir_count", 0)
        return FormattedResult(
            summary=f"Listed {file_count} files, {dir_count} directories"
        )


class DirectoryTreeFormatter(ToolFormatter):
    """Formatter for get_directory_tree tool."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        return FormattedResult(
            summary="Directory tree",
            details=str(result.data) if result.data else None,
        )


class TerminalFormatter(ToolFormatter):
    """Formatter for terminal commands (ls, pwd, cd, cat, etc.)."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        if self.tool_name == "ls":
            count = result.metadata.get("count", 0)
            return FormattedResult(summary=f"{count} items")

        elif self.tool_name == "pwd":
            return FormattedResult(
                summary="Current directory shown",
                details=str(result.data),
            )

        elif self.tool_name == "cd":
            new_cwd = result.metadata.get("new_cwd", "")
            return FormattedResult(
                summary=str(result.data),
                details=f"Now in: {new_cwd}" if new_cwd else None,
            )

        elif self.tool_name == "cat":
            lines = result.metadata.get("lines", "?")
            return FormattedResult(
                summary=f"Displayed {lines} lines",
                details=str(result.data) if result.data else None,
            )

        else:
            return FormattedResult(summary=str(result.data))


class DefaultFormatter(ToolFormatter):
    """Default formatter for unknown tools."""

    def format(self, result: ToolResult, args: Dict[str, Any]) -> FormattedResult:
        return FormattedResult(summary=str(result.data))


class ToolResultFormatter:
    """
    Main formatter class using Strategy pattern.

    Maps tool names to their specific formatters.
    Falls back to DefaultFormatter for unknown tools.
    """

    def __init__(self):
        self._formatters: Dict[str, ToolFormatter] = {
            "read_file": ReadFileFormatter(),
            "readfile": ReadFileFormatter(),
            "write_file": WriteFileFormatter(),
            "writefile": WriteFileFormatter(),
            "edit_file": WriteFileFormatter(),
            "editfile": WriteFileFormatter(),
            "search_files": SearchFormatter(),
            "searchfiles": SearchFormatter(),
            "bash_command": BashFormatter(),
            "bash": BashFormatter(),
            "git_status": GitStatusFormatter(),
            "gitstatus": GitStatusFormatter(),
            "git_diff": GitDiffFormatter(),
            "gitdiff": GitDiffFormatter(),
            "list_directory": ListDirectoryFormatter(),
            "listdirectory": ListDirectoryFormatter(),
            "get_directory_tree": DirectoryTreeFormatter(),
            "getdirectorytree": DirectoryTreeFormatter(),
            "ls": TerminalFormatter("ls"),
            "pwd": TerminalFormatter("pwd"),
            "cd": TerminalFormatter("cd"),
            "cat": TerminalFormatter("cat"),
            "mkdir": TerminalFormatter("mkdir"),
            "rm": TerminalFormatter("rm"),
            "cp": TerminalFormatter("cp"),
            "mv": TerminalFormatter("mv"),
            "touch": TerminalFormatter("touch"),
        }
        self._default = DefaultFormatter()

    def format(
        self,
        tool_name: str,
        result: ToolResult,
        args: Dict[str, Any],
    ) -> FormattedResult:
        """Format tool result using appropriate formatter."""
        formatter = self._formatters.get(tool_name.lower(), self._default)
        return formatter.format(result, args)

    def register(self, tool_name: str, formatter: ToolFormatter) -> None:
        """Register a custom formatter for a tool."""
        self._formatters[tool_name.lower()] = formatter
