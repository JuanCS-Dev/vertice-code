"""
REPL Masterpiece Commands - Command Definitions.

This module provides command definitions and metadata
for the REPL shell.

Features:
- Command registry with metadata
- Category-based organization
- Agent command definitions

Philosophy:
    "Commands should be discoverable and intuitive."
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, Any, Callable

from vertice_cli.ui.command_palette import CommandCategory

if TYPE_CHECKING:
    from .repl import MasterpieceREPL


def create_commands(repl: "MasterpieceREPL") -> Dict[str, Dict[str, Any]]:
    """
    Create command registry for REPL.

    Args:
        repl: Reference to MasterpieceREPL instance

    Returns:
        Dictionary of commands with metadata
    """
    from .handlers import (
        cmd_help,
        cmd_exit,
        cmd_clear,
        cmd_status,
        cmd_expand,
        cmd_mode,
        cmd_dream,
    )

    return {
        # System commands
        "/help": {
            "icon": "❓",
            "description": "Show all commands",
            "category": CommandCategory.HELP,
            "handler": lambda msg: cmd_help(repl, msg)
        },
        "/exit": {
            "icon": "👋",
            "description": "Exit shell",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_exit(repl, msg)
        },
        "/quit": {
            "icon": "👋",
            "description": "Exit (alias)",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_exit(repl, msg)
        },
        "/clear": {
            "icon": "🧹",
            "description": "Clear screen",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_clear(repl, msg)
        },
        "/status": {
            "icon": "📊",
            "description": "Show session status",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_status(repl, msg)
        },
        "/expand": {
            "icon": "📖",
            "description": "Show full last response",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_expand(repl, msg)
        },
        "/mode": {
            "icon": "🎛️",
            "description": "Change output mode (auto/full/minimal)",
            "category": CommandCategory.SYSTEM,
            "handler": lambda msg: cmd_mode(repl, msg)
        },

        # Agent commands
        "/architect": {
            "icon": "🏗️",
            "description": "Architect agent - system design",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("architect", msg))
        },
        "/refactor": {
            "icon": "♻️",
            "description": "Refactor agent - improve code",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("refactorer", msg))
        },
        "/test": {
            "icon": "🧪",
            "description": "Test agent - generate tests",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("testing", msg))
        },
        "/review": {
            "icon": "🔍",
            "description": "Review agent - code review",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("reviewer", msg))
        },
        "/docs": {
            "icon": "📚",
            "description": "Documentation agent",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("documentation", msg))
        },
        "/explore": {
            "icon": "🗺️",
            "description": "Explorer agent - navigate code",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("explorer", msg))
        },
        "/plan": {
            "icon": "📋",
            "description": "Planner agent - strategic planning",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("planner", msg))
        },
        "/dream": {
            "icon": "💭",
            "description": "DREAM mode - critical analysis",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: cmd_dream(repl, msg)
        },
        "/performance": {
            "icon": "⚡",
            "description": "Performance agent - optimize speed",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("performance", msg))
        },
        "/security": {
            "icon": "🔒",
            "description": "Security agent - find vulnerabilities",
            "category": CommandCategory.AGENT,
            "handler": lambda msg: asyncio.run(repl.invoke_agent("security", msg))
        },
    }


# Agent icon mapping
AGENT_ICONS = {
    "architect": "🏗️",
    "refactorer": "♻️",
    "refactor": "♻️",
    "testing": "🧪",
    "test": "🧪",
    "reviewer": "🔍",
    "review": "🔍",
    "documentation": "📚",
    "docs": "📚",
    "explorer": "🗺️",
    "explore": "🗺️",
    "planner": "📋",
    "plan": "📋",
    "performance": "⚡",
    "perf": "⚡",
    "security": "🔒",
    "sec": "🔒",
}


__all__ = ["create_commands", "AGENT_ICONS"]
