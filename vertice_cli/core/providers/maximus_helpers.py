"""
MAXIMUS Helpers.

Helper functions for MAXIMUS provider streaming and memory.
Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_enhanced_prompt(
    prompt: str,
    system_prompt: Optional[str],
    context: Optional[List[Dict[str, str]]],
    memory_context: Dict[str, Any],
) -> str:
    """Build enhanced prompt with memory context.

    Combines user prompt with system instructions, conversation
    history, and retrieved memories from MIRIX 6-types.

    Args:
        prompt: Original user prompt.
        system_prompt: System instructions.
        context: Conversation history.
        memory_context: Retrieved memories by type.

    Returns:
        Enhanced prompt string with all context injected.
    """
    parts: List[str] = []

    if system_prompt:
        parts.append(f"[SYSTEM]\n{system_prompt}\n")

    # Inject memory context
    if memory_context:
        if memory_context.get("core"):
            parts.append("[CORE IDENTITY]")
            for mem in memory_context["core"][:3]:
                parts.append(f"- {mem.get('content', '')}")
            parts.append("")

        if memory_context.get("procedural"):
            parts.append("[RELEVANT SKILLS]")
            for mem in memory_context["procedural"][:3]:
                parts.append(f"- {mem.get('content', '')}")
            parts.append("")

    if context:
        parts.append("[CONVERSATION HISTORY]")
        for msg in context[-10:]:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append("")

    parts.append(f"[CURRENT REQUEST]\n{prompt}")

    return "\n".join(parts)


def format_interaction_for_memory(prompt: str, response: str) -> str:
    """Format interaction for memory storage.

    Creates a condensed summary of the interaction for
    episodic memory storage.

    Args:
        prompt: User prompt (truncated to 100 chars).
        response: Agent response (truncated to 100 chars).

    Returns:
        Formatted interaction string.
    """
    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    truncated_response = response[:100] + "..." if len(response) > 100 else response

    return (
        f"User asked: {truncated_prompt}\n" f"I responded with guidance about: {truncated_response}"
    )


def format_execution_log(prompt: str, response: str) -> str:
    """Format execution log for tribunal evaluation.

    Creates a structured log for the Tribunal to evaluate.

    Args:
        prompt: User prompt.
        response: Agent response.

    Returns:
        Formatted execution log string.
    """
    return f"PROMPT: {prompt}\n\nRESPONSE: {response}"
