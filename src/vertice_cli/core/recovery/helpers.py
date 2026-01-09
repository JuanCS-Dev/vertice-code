"""
Recovery Helpers - Utility Functions.

Helper functions for shell integration and context creation.
"""

from typing import Any, Dict

from .types import RecoveryContext
from .engine import ErrorRecoveryEngine


async def create_recovery_context(
    conversation_manager: Any,
    turn: Any,
    failed_tool: str,
    failed_args: Dict[str, Any],
    error: str,
    max_attempts: int = 2,
) -> RecoveryContext:
    """Create recovery context from conversation turn.

    Args:
        conversation_manager: Conversation manager
        turn: Current conversation turn
        failed_tool: Tool that failed
        failed_args: Arguments that failed
        error: Error message
        max_attempts: Max recovery attempts

    Returns:
        Recovery context
    """
    # Categorize error using temporary engine
    engine = ErrorRecoveryEngine(llm_client=None)
    category = engine.categorize_error(error)

    # Get previous commands
    previous_cmds = []
    for prev_turn in conversation_manager.turns[-3:]:
        for tool_result in prev_turn.tool_results:
            previous_cmds.append(
                {
                    "tool": tool_result["tool"],
                    "args": tool_result["args"],
                    "success": tool_result["success"],
                }
            )

    return RecoveryContext(
        attempt_number=1,
        max_attempts=max_attempts,
        error=error,
        error_category=category,
        failed_tool=failed_tool,
        failed_args=failed_args,
        previous_result=None,
        user_intent=turn.user_input,
        previous_commands=previous_cmds,
    )
