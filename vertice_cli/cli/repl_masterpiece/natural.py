"""
REPL Masterpiece Natural - Natural Language Processing.

This module provides natural language routing and
smart detection for user intents.

Features:
- Context resolution
- Agent auto-routing
- Tool detection from natural language

Philosophy:
    "Natural language should feel natural."
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .repl import MasterpieceREPL


async def process_natural(repl: "MasterpieceREPL", message: str) -> None:
    """
    Process natural language with smart detection.

    Args:
        repl: Reference to MasterpieceREPL
        message: User message
    """
    from .streaming import stream_response
    from .tools import process_tool
    from .commands import AGENT_ICONS

    # Resolve context
    original = message
    message = repl.context.resolve_reference(message)
    if message != original:
        repl.console.print(f"[dim]🔄 Context: {message}[/dim]")

    # PHASE 2: Try coordinator first (agent auto-routing)
    coordinator_response = await repl.coordinator.process_message(message)

    if coordinator_response:
        # Agent handled the message
        repl.console.print(f"\n{coordinator_response}\n")
        return

    # Smart tool detection (fallback if no agent)
    msg_lower = message.lower()

    # File operations
    if any(kw in msg_lower for kw in ["read", "show", "open", "cat"]):
        match = re.search(r"[\w/.]+\.\w+", message)
        if match:
            await process_tool(repl, "/read", match.group(0))
            return

    # Bash execution
    if any(kw in msg_lower for kw in ["run", "execute", "bash"]):
        cmd = re.sub(r"^.*(run|execute|bash)\s+", "", message, flags=re.IGNORECASE)
        await process_tool(repl, "/run", cmd)
        return

    # Git operations
    if "git" in msg_lower:
        if "status" in msg_lower:
            await process_tool(repl, "/git", "status")
            return
        elif "diff" in msg_lower:
            await process_tool(repl, "/git", "diff")
            return

    # FALLBACK: Old agent detection (kept for compatibility)
    should_use_agent, detected_agent = repl.intent_detector.should_use_agent(message)

    if should_use_agent and detected_agent:
        icon = AGENT_ICONS.get(detected_agent, "🤖")
        repl.console.print(f"[dim]{icon} Auto-routing to {detected_agent} agent...[/dim]")
        await repl.invoke_agent(detected_agent, message)
        return

    # Chat mode with streaming
    if repl.dream_mode:
        message = f"[CRITICAL ANALYSIS MODE] {message}"

    await stream_response(repl, message)


__all__ = ["process_natural"]
