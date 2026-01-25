"""
Formatting Helpers - Convenience functions and stream-safe markup.

Quick helpers and plain text markup for streaming output.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, Optional, Dict

from rich.panel import Panel

from .formatter import OutputFormatter


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def response_panel(text: str, title: str = "Response") -> Panel:
    """Quick helper for response panels."""
    return OutputFormatter.format_response(text, title)


def tool_panel(name: str, success: bool, data: Any = None, error: Optional[str] = None) -> Panel:
    """Quick helper for tool result panels."""
    return OutputFormatter.format_tool_result(name, success, data, error)


def code_panel(code: str, language: str = "python") -> Panel:
    """Quick helper for code panels."""
    return OutputFormatter.format_code_block(code, language)


# =============================================================================
# STREAM-SAFE MARKUP HELPERS - Plain text with emojis for streaming
# =============================================================================
# IMPORTANT: These return PLAIN TEXT, not Rich markup!
# The streaming system uses RichMarkdown which does NOT process [bold] tags.
# Use emojis and plain text for Claude-Code-Web style output.

# Action verb mappings for tool results
_TOOL_ACTION_MAP: Dict[str, str] = {
    "write_file": "CREATED",
    "edit_file": "UPDATED",
    "read_file": "READ",
    "delete_file": "DELETED",
    "bash_command": "EXECUTED",
    "mkdir": "CREATED",
    "create_directory": "CREATED",
    "search_files": "SEARCHED",
    "git_status": "CHECKED",
    "git_diff": "DIFFED",
}


def tool_executing_markup(tool_name: str) -> str:
    """Return plain text for tool execution (streaming safe)."""
    return f"• **{tool_name}**"


def tool_success_markup(tool_name: str) -> str:
    """Return plain text for tool success (streaming safe)."""
    action = _TOOL_ACTION_MAP.get(tool_name, "SUCCESS")
    return f"[{action}] {tool_name}"


def tool_error_markup(tool_name: str, error: str) -> str:
    """Return plain text for tool error (streaming safe)."""
    return f"[FAILED] {tool_name}: {error[:80]}"


def agent_routing_markup(agent_name: str, confidence: float) -> str:
    """Return plain text for agent routing (streaming safe)."""
    confidence_pct = int(confidence * 100)
    return f"🔀 Auto-routing to **{agent_name.title()}Agent** (confidence: {confidence_pct}%)"
