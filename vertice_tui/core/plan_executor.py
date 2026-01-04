"""
Plan Executor - Plan execution detection and handling.

Extracted from bridge.py (Dec 2025 Refactoring).

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

# =============================================================================
# PLAN EXECUTION PATTERNS
# =============================================================================

EXECUTE_PATTERNS: List[str] = [
    r"^make\s+it\s+real",
    r"^do\s+it\b",
    r"^build\s+it\b",
    r"^create\s+it\b",
    r"^(go|let'?s\s+go|vamos|bora)\b",
    r"^execute\s+(the\s+)?(plan|plano)",
    r"^run\s+(the\s+)?(plan|plano)",
    r"^implement",
    r"^create\s+(the\s+)?files?",
    r"^write\s+(the\s+)?files?",
    r"^generate\s+(the\s+)?(code|files?)",
    r"^materializ",
    r"^(faz|cria)\s*(isso|os\s*arquivos)?",
]


def is_plan_execution_request(message: str) -> bool:
    """
    Check if user wants to execute a saved plan.

    Args:
        message: User message to check

    Returns:
        True if message indicates plan execution request
    """
    msg_lower = message.lower().strip()
    return any(re.match(p, msg_lower, re.IGNORECASE) for p in EXECUTE_PATTERNS)


def prepare_plan_execution(
    message: str, last_plan: Optional[str]
) -> Tuple[str, bool, Optional[str]]:
    """
    Prepare message for plan execution if applicable.

    Args:
        message: Original user message
        last_plan: Last saved plan (if any)

    Returns:
        Tuple of (modified_message, skip_routing, preamble_to_yield)
    """
    if not last_plan or not is_plan_execution_request(message):
        return message, False, None

    # Build execution prompt
    modified_message = f"""Execute this plan by creating the files using write_file tool:

{last_plan[:3000]}

NOW CREATE ALL THE FILES using write_file tool. Start with mkdir for the directory, then write_file for each file."""

    preamble = "🚀 *Executing saved plan...*\n\n"

    return modified_message, True, preamble
