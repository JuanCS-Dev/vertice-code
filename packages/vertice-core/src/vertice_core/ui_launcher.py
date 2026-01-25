"""
UI Launcher - Lazy TUI imports to break circular dependency.

This module provides lazy loading of vertice_core.tui components to prevent
circular imports between vertice_core and vertice_core.tui.

The dependency direction should be:
    vertice_core.tui → vertice_core  (TUI imports CLI)
    vertice_core → vertice_core.tui  (CLI should NOT import TUI directly)

This launcher provides the bridge for CLI to launch TUI when needed.

Author: Boris Cherny style
Date: 2025-11-26
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from vertice_core.tui.core.bridge import Bridge


def launch_tui() -> None:
    """
    Launch the Textual TUI application.

    Lazy import to avoid circular dependency.
    """
    from vertice_core.tui.app import VerticeApp

    app = VerticeApp()
    app.run()


def get_bridge() -> "Bridge":
    """
    Get the TUI bridge instance.

    Lazy import to avoid circular dependency.

    Returns:
        Bridge instance for CLI-TUI communication
    """
    from vertice_core.tui.core.bridge import get_bridge

    return get_bridge()


def get_agent_registry() -> dict:
    """
    Get the agent registry from TUI.

    Lazy import to avoid circular dependency.

    Returns:
        Dictionary of registered agents
    """
    from vertice_core.tui.core.bridge import AGENT_REGISTRY

    return AGENT_REGISTRY


async def chat_via_bridge(prompt: str) -> AsyncGenerator[Any, None]:
    """
    Chat via the TUI bridge.

    Lazy import to avoid circular dependency.

    Args:
        prompt: User prompt to send

    Yields:
        Response chunks from the LLM
    """
    bridge = get_bridge()
    async for chunk in bridge.chat(prompt):
        yield chunk


__all__ = [
    "launch_tui",
    "get_bridge",
    "get_agent_registry",
    "chat_via_bridge",
]
