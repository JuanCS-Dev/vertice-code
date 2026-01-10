"""
Hierarchical Strategy - Multi-level context summarization.

Creates hierarchical summaries: recent verbatim, older summarized.
"""

import logging
import time
from typing import TYPE_CHECKING

from .base import CompactionStrategy_ABC

if TYPE_CHECKING:
    from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
    from vertice_core.agents.context import UnifiedContext

logger = logging.getLogger(__name__)


class HierarchicalStrategy(CompactionStrategy_ABC):
    """
    Hierarchical compaction strategy.

    Maintains multiple levels of detail:
    - Recent: Verbatim preservation
    - Medium: Structured summaries
    - Old: High-level summaries only
    """

    def compact(
        self,
        context: "UnifiedContext",
        config: "CompactionConfig",
    ) -> "CompactionResult":
        """Apply hierarchical compaction."""
        start_time = time.time()
        tokens_before = context._token_usage
        messages_removed = 0

        messages = context._messages.copy()
        processed_messages = []

        # Define time windows
        recent_threshold = config.keep_recent_messages
        medium_threshold = recent_threshold + config.keep_decisions

        for i, msg in enumerate(messages):
            age = len(messages) - i - 1  # How old is this message?

            if age < recent_threshold:
                # Recent: keep verbatim
                processed_messages.append(msg)
            elif age < medium_threshold:
                # Medium: create structured summary
                summary = self._create_structured_summary(msg, config)
                processed_messages.append(
                    {**msg, "content": summary, "_summarized": "true", "_level": "medium"}
                )
            else:
                # Old: high-level summary only
                summary = self._create_high_level_summary(msg)
                if summary:  # Only keep if summarizable
                    processed_messages.append(
                        {**msg, "content": summary, "_summarized": "true", "_level": "high"}
                    )
                else:
                    messages_removed += 1

        # Update context
        context._messages = processed_messages
        tokens_after = context._token_usage
        compression_ratio = tokens_after / tokens_before if tokens_before > 0 else 1.0

        return CompactionResult(
            success=True,
            strategy_used=config.fallback_strategy,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio,
            duration_ms=(time.time() - start_time) * 1000,
            messages_removed=messages_removed,
        )

    def _create_structured_summary(self, message: dict, config: "CompactionConfig") -> str:
        """Create structured summary for medium-term messages."""
        content = message.get("content", "")
        role = message.get("role", "")

        if role == "user":
            return f"User query: {content[:100]}{'...' if len(content) > 100 else ''}"
        elif role == "assistant":
            return f"Assistant response: {content[:200]}{'...' if len(content) > 200 else ''}"
        elif role == "tool":
            return self._summarize_tool_call(message, config)
        else:
            return f"Message ({role}): {content[:150]}{'...' if len(content) > 150 else ''}"

    def _create_high_level_summary(self, message: dict) -> str:
        """Create high-level summary for old messages."""
        role = message.get("role", "")

        if role == "user":
            return "User interaction"
        elif role == "assistant":
            return "Assistant response"
        elif role == "tool":
            return "Tool execution"
        else:
            return f"{role.title()} message"

    def _summarize_tool_call(self, message: dict, config: "CompactionConfig") -> str:
        """Summarize tool call results."""
        content = message.get("content", "")

        # Extract tool name if available
        tool_name = message.get("tool_call", {}).get("name", "tool")
        if not tool_name or tool_name == "tool":
            tool_name = "unknown tool"

        # Check for success/failure
        if "error" in content.lower() or "exception" in content.lower():
            status = "failed"
        elif "success" in content.lower() or "completed" in content.lower():
            status = "succeeded"
        else:
            status = "executed"

        return f"Tool '{tool_name}' {status}"
