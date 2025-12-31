"""
Context Compaction - Claude Code Parity.

Token-aware context window management with summarization.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class CompactionMixin:
    """
    Mixin for context compaction functionality.

    Claude Code Pattern:
    - Preserves recent messages (last N)
    - Summarizes older messages into a single context message
    - Token-aware utilization tracking
    """

    # Context compaction thresholds
    MAX_CONTEXT_TOKENS: int = 32000  # Default context window
    COMPACTION_THRESHOLD: float = 0.60  # Trigger compaction at 60%
    CHARS_PER_TOKEN: int = 4  # Rough estimate for token counting

    def _init_compaction(self, max_context_tokens: int = 32000) -> None:
        """Initialize compaction tracking.

        Args:
            max_context_tokens: Maximum tokens for context window
        """
        self.max_context_tokens = max_context_tokens
        self._token_count = 0
        self._compaction_count = 0

    def estimate_tokens(self) -> Dict[str, Any]:
        """
        Estimate token count for current context.

        Uses character-based heuristic (4 chars ≈ 1 token).

        Returns:
            Token estimation with utilization metrics
        """
        # Requires self.context from HistoryManager
        context: List[Dict[str, str]] = getattr(self, 'context', [])

        total_chars = sum(len(msg.get("content", "")) for msg in context)
        estimated_tokens = total_chars // self.CHARS_PER_TOKEN
        utilization = (
            estimated_tokens / self.max_context_tokens
            if self.max_context_tokens > 0 else 0
        )

        return {
            "estimated_tokens": estimated_tokens,
            "total_chars": total_chars,
            "max_tokens": self.max_context_tokens,
            "utilization_percent": round(utilization * 100, 1),
            "needs_compaction": utilization > self.COMPACTION_THRESHOLD,
            "messages_count": len(context)
        }

    def needs_compaction(self) -> bool:
        """Check if context needs compaction (>60% utilization)."""
        stats = self.estimate_tokens()
        return stats["needs_compaction"]

    def compact(
        self,
        focus: Optional[str] = None,
        preserve_recent: int = 5,
        summary_fn: Optional[Callable[[List[Dict[str, str]], Optional[str]], str]] = None
    ) -> Dict[str, Any]:
        """
        Compact conversation context by summarizing older messages.

        Claude Code Pattern:
        - Preserves recent messages (last N)
        - Summarizes older messages into a single context message
        - Optionally focuses summary on specific topic

        Args:
            focus: Optional topic to focus summary on
            preserve_recent: Number of recent messages to keep intact
            summary_fn: Optional function to generate summary (LLM-based)

        Returns:
            Compaction result with before/after stats
        """
        context: List[Dict[str, str]] = getattr(self, 'context', [])
        before_stats = self.estimate_tokens()

        if len(context) <= preserve_recent:
            return {
                "success": False,
                "reason": "Not enough context to compact",
                "before": before_stats,
                "after": before_stats
            }

        # Split context
        old_messages = context[:-preserve_recent]
        recent_messages = context[-preserve_recent:]

        # Generate summary
        if summary_fn:
            summary = summary_fn(old_messages, focus)
        else:
            summary = self._generate_simple_summary(old_messages, focus)

        # Create compacted context
        summary_message = {
            "role": "system",
            "content": f"[Context Summary - {len(old_messages)} messages compacted]\n{summary}"
        }

        # Update context
        setattr(self, 'context', [summary_message] + recent_messages)
        self._compaction_count += 1

        after_stats = self.estimate_tokens()

        return {
            "success": True,
            "before": before_stats,
            "after": after_stats,
            "messages_compacted": len(old_messages),
            "messages_preserved": len(recent_messages),
            "tokens_saved": before_stats["estimated_tokens"] - after_stats["estimated_tokens"],
            "focus": focus,
            "compaction_number": self._compaction_count
        }

    def _generate_simple_summary(
        self,
        messages: List[Dict[str, str]],
        focus: Optional[str] = None
    ) -> str:
        """
        Generate a simple rule-based summary of messages.

        This is a fallback when LLM summarization is not available.

        Args:
            messages: Messages to summarize
            focus: Optional topic focus

        Returns:
            Summary string
        """
        # Group by role
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        summary_parts: List[str] = []

        if user_msgs:
            user_topics: List[str] = []
            for msg in user_msgs[-5:]:  # Last 5 user messages
                content = msg.get("content", "")[:100]
                if content:
                    user_topics.append(f"- {content}...")
            if user_topics:
                summary_parts.append("User discussed:\n" + "\n".join(user_topics))

        if assistant_msgs:
            # Count tool usage patterns
            tool_mentions: Dict[str, int] = {}
            for msg in assistant_msgs:
                content = msg.get("content", "")
                for tool in ["read_file", "write_file", "edit_file", "bash_command", "search_files"]:
                    if tool in content.lower():
                        tool_mentions[tool] = tool_mentions.get(tool, 0) + 1

            if tool_mentions:
                tools_used = ", ".join(
                    f"{k}({v}x)"
                    for k, v in sorted(tool_mentions.items(), key=lambda x: -x[1])[:5]
                )
                summary_parts.append(f"Tools used: {tools_used}")

        if focus:
            summary_parts.append(f"Focus topic: {focus}")

        return "\n".join(summary_parts) if summary_parts else "Previous conversation context (details compacted)"

    def replace_with_summary(
        self,
        summary: str,
        preserve_recent: int = 5
    ) -> Dict[str, Any]:
        """
        Replace older context with a custom summary.

        Used when LLM generates a better summary externally.

        Args:
            summary: Summary text to use
            preserve_recent: Number of recent messages to keep

        Returns:
            Result dictionary
        """
        context: List[Dict[str, str]] = getattr(self, 'context', [])
        before_stats = self.estimate_tokens()

        if len(context) <= preserve_recent:
            return {
                "success": False,
                "reason": "Not enough context to compact"
            }

        recent_messages = context[-preserve_recent:]
        old_count = len(context) - preserve_recent

        summary_message = {
            "role": "system",
            "content": f"[Context Summary - {old_count} messages compacted]\n{summary}"
        }

        setattr(self, 'context', [summary_message] + recent_messages)
        self._compaction_count += 1

        after_stats = self.estimate_tokens()

        return {
            "success": True,
            "messages_compacted": old_count,
            "tokens_before": before_stats["estimated_tokens"],
            "tokens_after": after_stats["estimated_tokens"],
            "tokens_saved": before_stats["estimated_tokens"] - after_stats["estimated_tokens"]
        }

    def auto_compact_if_needed(
        self,
        preserve_recent: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically compact context if utilization exceeds threshold.

        Called after adding context to maintain healthy context window.

        Returns:
            Compaction result if compaction was performed, None otherwise
        """
        if self.needs_compaction():
            return self.compact(preserve_recent=preserve_recent)
        return None
