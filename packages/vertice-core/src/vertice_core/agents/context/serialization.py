"""
Context Serialization - Prompt generation and persistence.

Functions for converting UnifiedContext to/from various formats.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .unified import UnifiedContext


def generate_prompt_context(ctx: "UnifiedContext") -> str:
    """
    Generate context string for LLM prompt.

    This is the main output used when calling LLMs.

    Args:
        ctx: UnifiedContext instance.

    Returns:
        Formatted context string.
    """
    parts = []

    # User request
    if ctx.user_request:
        parts.append(f"## User Request\n{ctx.user_request}")

    if ctx.user_intent:
        parts.append(f"## Intent\n{ctx.user_intent}")

    # Summary from compaction
    if ctx._summary:
        parts.append(f"## Previous Context (Summary)\n{ctx._summary}")

    # Codebase awareness
    if ctx.codebase_summary:
        parts.append(f"## Codebase Context\n{ctx.codebase_summary}")

    # Files in context
    if ctx._files:
        file_parts = ["## Files in Context"]
        for filepath, file_ctx in ctx._files.items():
            file_parts.append(f"\n### {filepath}")
            file_parts.append(f"```{file_ctx.language}")
            file_parts.append(file_ctx.content)
            file_parts.append("```")
        parts.append("\n".join(file_parts))

    # Context variables (non-sensitive)
    safe_vars = {
        k: v
        for k, v in ctx._variables.items()
        if not any(s in k.lower() for s in ["key", "secret", "token", "password"])
    }
    if safe_vars:
        parts.append(f"## Context Variables\n{json.dumps(safe_vars, indent=2)}")

    # Recent decisions
    if ctx._decisions:
        recent_decisions = ctx._decisions[-5:]
        decision_str = "\n".join(
            f"- [{d.decision_type.value if hasattr(d.decision_type, 'value') else d.decision_type}] {d.description}"
            for d in recent_decisions
        )
        parts.append(f"## Recent Decisions\n{decision_str}")

    # Thought chain
    if ctx._thoughts:
        recent_thoughts = ctx._thoughts[-3:]
        thought_str = "\n".join(
            f"- {t.key_insights[0] if t.key_insights else 'N/A'} → {t.next_action}"
            for t in recent_thoughts
        )
        parts.append(f"## Reasoning Chain\n{thought_str}")

    # Errors
    if ctx._errors:
        recent_errors = ctx._errors[-3:]
        error_str = "\n".join(f"- [{e.error_type}] {e.error_message[:100]}" for e in recent_errors)
        parts.append(f"## Recent Errors\n{error_str}")

    return "\n\n".join(parts)


def context_to_dict(ctx: "UnifiedContext") -> Dict[str, Any]:
    """Serialize entire context to dictionary."""
    return {
        "session_id": ctx.session_id,
        "created_at": ctx.created_at,
        "state": ctx.state.value,
        "user_request": ctx.user_request,
        "user_intent": ctx.user_intent,
        "variables": ctx._variables,
        "summary": ctx._summary,
        "messages": ctx._messages,
        "files": {
            fp: {"tokens": f.tokens, "lines": f"{f.start_line}-{f.end_line}"}
            for fp, f in ctx._files.items()
        },
        "current_agent": ctx.current_agent,
        "current_plan_id": ctx.current_plan_id,
        "completed_steps": len(ctx.completed_steps),
        "decisions": [asdict(d) for d in ctx._decisions[-10:]],
        "errors": [e.to_dict() for e in ctx._errors[-5:]],
        "execution_results": [asdict(result) for result in ctx.get_execution_results()],
        "token_usage": ctx._token_usage,
        "max_tokens": ctx.max_tokens,
    }


def context_from_dict(data: Dict[str, Any]) -> "UnifiedContext":
    """Deserialize from dictionary."""
    from .unified import UnifiedContext

    return UnifiedContext.from_dict(data)


__all__ = [
    "generate_prompt_context",
    "context_to_dict",
    "context_from_dict",
]
