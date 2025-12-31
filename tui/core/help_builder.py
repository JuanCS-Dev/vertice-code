"""
Help Builder - Tool and command help generation.

Extracted from bridge.py (Dec 2025 Refactoring).

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, Dict, List

from .governance import ELP


# =============================================================================
# TOOL CATEGORIES
# =============================================================================

TOOL_CATEGORIES: Dict[str, List[str]] = {
    "File": [
        "read_file", "write_file", "edit_file", "list_directory", "delete_file",
        "move_file", "copy_file", "create_directory", "read_multiple_files", "insert_lines"
    ],
    "Terminal": ["cd", "ls", "pwd", "mkdir", "rm", "cp", "mv", "touch", "cat"],
    "Execution": ["bash_command"],
    "Search": ["search_files", "get_directory_tree"],
    "Git": ["git_status", "git_diff"],
    "Context": ["get_context", "save_session", "restore_backup"],
    "Web": [
        "web_search", "search_documentation", "fetch_url", "download_file",
        "http_request", "package_search"
    ],
}


# =============================================================================
# AGENT COMMANDS
# =============================================================================

AGENT_COMMANDS: Dict[str, str] = {
    "/plan": "planner",
    "/execute": "executor",
    "/architect": "architect",
    "/review": "reviewer",
    "/explore": "explorer",
    "/refactor": "refactorer",
    "/test": "testing",
    "/security": "security",
    "/docs": "documentation",
    "/perf": "performance",
    "/devops": "devops",
    "/justica": "justica",
    "/sofia": "sofia",
    "/data": "data",
}


def build_tool_list(tools: List[str]) -> str:
    """
    Build formatted list of tools organized by category.

    Args:
        tools: List of available tool names

    Returns:
        Formatted markdown string with tool list
    """
    if not tools:
        return "No tools loaded."

    lines = [f"## {ELP['tool']} Tools ({len(tools)} available)\n"]

    for category, expected_tools in TOOL_CATEGORIES.items():
        available = [t for t in expected_tools if t in tools]
        if available:
            lines.append(f"### {category}")
            lines.append(", ".join(f"`{t}`" for t in available))
            lines.append("")

    # Uncategorized tools
    all_categorized: set[str] = set()
    for cat_tools in TOOL_CATEGORIES.values():
        all_categorized.update(cat_tools)

    uncategorized = [t for t in tools if t not in all_categorized]
    if uncategorized:
        lines.append("### Other")
        lines.append(", ".join(f"`{t}`" for t in uncategorized))

    return "\n".join(lines)


def build_command_help(agent_registry: Dict[str, Any]) -> str:
    """
    Build help text for agent commands.

    Args:
        agent_registry: Registry mapping agent names to AgentInfo

    Returns:
        Formatted markdown string with command help
    """
    lines = ["## Agent Commands\n"]

    for cmd, agent in AGENT_COMMANDS.items():
        info = agent_registry.get(agent)
        if info:
            lines.append(f"| `{cmd}` | {info.description} |")

    return "\n".join(lines)


def get_agent_commands() -> Dict[str, str]:
    """Get mapping of slash commands to agents."""
    return AGENT_COMMANDS.copy()
