"""
UnifiedContext - Modular Shared State for Multi-Agent Orchestration.

Refactored into focused mixins for better maintainability and scalability.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from .mixins import (
    ContextVariablesMixin,
    DecisionTrackingMixin,
    ErrorTrackingMixin,
    ExecutionResultsMixin,
    FileContextMixin,
    MessageMixin,
    ThoughtSignaturesMixin,
)
from .types import ContextState, ExecutionResult, ThoughtSignature

logger = logging.getLogger(__name__)


class UnifiedContext(
    ContextVariablesMixin,
    FileContextMixin,
    MessageMixin,
    DecisionTrackingMixin,
    ErrorTrackingMixin,
    ThoughtSignaturesMixin,
    ExecutionResultsMixin,
):
    """
    UnifiedContext - Modular Shared State for Multi-Agent Orchestration.

    Refactored into focused mixins for better maintainability and scalability.
    """

    # Token limits
    DEFAULT_MAX_TOKENS = 32_000
    COMPACTION_THRESHOLD = 0.90  # Trigger compaction at 90%

    def __init__(
        self,
        user_request: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        session_id: Optional[str] = None,
    ):
        """
        Initialize unified context with all mixins.

        Args:
            user_request: Original user request
            max_tokens: Maximum tokens for context
            session_id: Optional session ID for persistence
        """
        # Initialize all mixins
        ContextVariablesMixin.__init__(self)
        FileContextMixin.__init__(self)
        MessageMixin.__init__(self)
        DecisionTrackingMixin.__init__(self)
        ErrorTrackingMixin.__init__(self)
        ThoughtSignaturesMixin.__init__(self)
        ExecutionResultsMixin.__init__(self)

        # Core attributes
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.created_at = time.time()
        self.max_tokens = max_tokens
        self.state = ContextState.ACTIVE

        # Core request
        self.user_request = user_request
        self.user_intent: str = ""  # Extracted intent

        # Codebase awareness
        self.codebase_summary: str = ""

        # Current execution state
        self.current_agent: Optional[str] = None
        self.current_plan_id: Optional[str] = None
        self.completed_steps: List[ExecutionResult] = []

        # Summary for compaction
        self._summary: str = ""  # Compacted summary

        # Token usage tracking
        self._token_usage: int = 0

        # Thought chain (legacy compatibility)
        self._thought_chain: List[ThoughtSignature] = []

    def _should_compact(self) -> bool:
        """Check if context should be compacted based on thresholds."""
        usage_ratio = self._token_usage / self.max_tokens
        return usage_ratio >= self.COMPACTION_THRESHOLD

    def _trigger_compaction(self) -> None:
        """Trigger automatic compaction."""
        logger.info(f"Context compaction triggered at {self._token_usage} tokens")

        if len(self._messages) > 10:
            old_messages = self._messages[:-10]

            for msg in old_messages:
                # Simple compaction - keep recent, summarize old
                pass

            self._messages = self._messages[-10:]

        self._recalculate_tokens()
        logger.info(f"Context compacted to {self._token_usage} tokens")

    def _recalculate_tokens(self) -> None:
        """Recalculate token usage."""
        total_tokens = 0

        # Messages
        for msg in self._messages:
            total_tokens += len(msg.get("content", "")) // 4

        # Files
        for file_ctx in self._files.values():
            total_tokens += file_ctx.tokens

        self._token_usage = total_tokens

    def compact(self, summarizer: Optional[Callable[[str], str]] = None) -> str:
        """Compact context using external summarizer."""
        if not summarizer:
            return ""

        # Create summary of current context
        context_text = self.to_prompt_context()
        self._summary = summarizer(context_text)

        # Clear detailed messages, keep summary
        self._messages = [
            {
                "role": "system",
                "content": f"CONTEXT SUMMARY: {self._summary}",
                "timestamp": str(time.time()),
            }
        ]

        self._recalculate_tokens()
        return self._summary

    def to_prompt_context(self) -> str:
        """Convert context to prompt-ready format."""
        parts = []

        # User request
        parts.append(f"User Request: {self.user_request}")

        # Variables
        if self._variables:
            vars_str = ", ".join(f"{k}={v}" for k, v in self._variables.items())
            parts.append(f"Context Variables: {vars_str}")

        # Files
        if self._files:
            files_str = ", ".join(self._files.keys())
            parts.append(f"Relevant Files: {files_str}")

        # Recent messages
        if self._messages:
            msg_count = min(5, len(self._messages))
            recent_msgs = self._messages[-msg_count:]
            parts.append(f"Recent Conversation ({msg_count} messages):")
            for msg in recent_msgs:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]
                parts.append(f"  {role.title()}: {content}...")

        # Decisions
        if self._decisions:
            recent_decisions = self._decisions[-3:]
            parts.append("Recent Decisions:")
            for decision in recent_decisions:
                parts.append(f"  - {decision.description}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "max_tokens": self.max_tokens,
            "state": self.state.value,
            "user_request": self.user_request,
            "user_intent": self.user_intent,
            "variables": self._variables,
            "messages": self._messages,
            "files": {k: v.__dict__ for k, v in self._files.items()},
            "decisions": [d.__dict__ for d in self._decisions],
            "errors": [e.__dict__ for e in self._errors],
            "thoughts": [t.__dict__ for t in self._thoughts],
            "execution_results": {k: v.__dict__ for k, v in self._execution_results.items()},
            "summary": self._summary,
            "token_usage": self._token_usage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedContext":
        """Deserialize from dictionary."""
        # Create instance
        ctx = cls(
            user_request=data.get("user_request", ""),
            max_tokens=data.get("max_tokens", cls.DEFAULT_MAX_TOKENS),
            session_id=data.get("session_id"),
        )

        # Restore state
        ctx.created_at = data.get("created_at", time.time())
        ctx.state = ContextState(data.get("state", "active"))
        ctx.user_intent = data.get("user_intent", "")
        ctx._summary = data.get("summary", "")
        ctx._token_usage = data.get("token_usage", 0)

        # Restore collections
        ctx._variables = data.get("variables", {})
        ctx._messages = data.get("messages", [])

        # Restore files
        files_data = data.get("files", {})
        for filepath, file_dict in files_data.items():
            # Create FileContext from dict
            from .types import FileContext

            file_ctx = FileContext(**file_dict)
            ctx._files[filepath] = file_ctx

        # Restore decisions
        decisions_data = data.get("decisions", [])
        for decision_dict in decisions_data:
            from .types import Decision

            decision = Decision(**decision_dict)
            ctx._decisions.append(decision)

        # Restore errors
        errors_data = data.get("errors", [])
        for error_dict in errors_data:
            from .types import ErrorContext

            error = ErrorContext(**error_dict)
            ctx._errors.append(error)

        # Restore thoughts
        thoughts_data = data.get("thoughts", [])
        for thought_dict in thoughts_data:
            from .types import ThoughtSignature

            thought = ThoughtSignature(**thought_dict)
            ctx._thoughts.append(thought)

        # Restore execution results
        exec_data = data.get("execution_results", {})
        for step_id, result_dict in exec_data.items():
            from .types import ExecutionResult

            result = ExecutionResult(**result_dict)
            ctx._execution_results[step_id] = result

        return ctx

    def get_token_usage(self) -> Tuple[int, int]:
        """Get current token usage and limit."""
        return self._token_usage, self.max_tokens

    def get_thought_chain(self) -> List[ThoughtSignature]:
        """Get the complete thought signature chain (legacy compatibility)."""
        return self._thoughts.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive context statistics."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "state": self.state.value,
            "variables_count": len(self._variables),
            "messages_count": len(self._messages),
            "files_count": len(self._files),
            "decisions_count": len(self._decisions),
            "errors_count": len(self._errors),
            "thoughts_count": len(self._thoughts),
            "execution_steps": len(self._execution_results),
            "failures": self.has_failures(),
            "token_usage": f"{self._token_usage}/{self.max_tokens}",
            "usage_percent": f"{(self._token_usage / self.max_tokens * 100):.1f}%",
        }

    def clear(self) -> None:
        """Clear all context data."""
        self._variables.clear()
        self._messages.clear()
        self._files.clear()
        self._decisions.clear()
        self._errors.clear()
        self._thoughts.clear()
        self._execution_results.clear()
        self._summary = ""
        self._token_usage = 0
