"""
UnifiedContext - Shared State for Multi-Agent Orchestration.

Implements the context patterns from Big 3 (Dec 2025):
- Anthropic: Compaction + subagent isolation
- OpenAI Swarm: Explicit context_variables
- Google Gemini: Thought signatures + memory layer

Features:
- Shared state across all agents
- Automatic compaction when approaching limits
- Decision tracking for explainability
- Codebase awareness via semantic indexing
- Serializable for persistence/recovery

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from .types import (
    ContextState,
    Decision,
    DecisionType,
    ErrorContext,
    ExecutionResult,
    FileContext,
    ThoughtSignature,
)

logger = logging.getLogger(__name__)


class UnifiedContext:
    """
    Shared context for multi-agent orchestration.

    This is the single source of truth for all agents in a session.
    Follows the patterns from Anthropic, OpenAI, and Google.

    Key Features:
    1. Explicit state (like Swarm's context_variables)
    2. Compaction support (like Claude SDK)
    3. Thought signatures (like Gemini 3)
    4. Decision tracking for explainability
    5. File context management (like Claude Code /add)

    Usage:
        ctx = UnifiedContext(user_request="implement feature X")
        ctx.set("api_key", "xxx")  # Set context variable
        ctx.add_file("src/main.py", content)  # Add file to context
        ctx.record_decision(decision)  # Track decision
        prompt = ctx.to_prompt_context()  # Get context for LLM
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
        Initialize unified context.

        Args:
            user_request: Original user request
            max_tokens: Maximum tokens for context
            session_id: Optional session ID for persistence
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.created_at = time.time()
        self.max_tokens = max_tokens
        self.state = ContextState.ACTIVE

        # Core request
        self.user_request = user_request
        self.user_intent: str = ""  # Extracted intent

        # Context variables (Swarm pattern)
        self._variables: Dict[str, Any] = {}

        # Conversation history
        self._messages: List[Dict[str, str]] = []
        self._summary: str = ""  # Compacted summary

        # File context (Claude Code pattern)
        self._files: Dict[str, FileContext] = {}

        # Codebase awareness (Sprint 1 integration)
        self.codebase_summary: str = ""
        self.relevant_symbols: List[str] = []

        # Execution state
        self.current_agent: Optional[str] = None
        self.current_plan_id: Optional[str] = None
        self.completed_steps: List[ExecutionResult] = []
        self.pending_approvals: List[str] = []

        # Decision tracking
        self._decisions: List[Decision] = []
        self._errors: List[ErrorContext] = []

        # Thought signatures (Gemini pattern)
        self._thought_chain: List[ThoughtSignature] = []

        # Token tracking
        self._token_usage: int = 0

    # =========================================================================
    # Context Variables (Swarm pattern)
    # =========================================================================

    def get(self, key: str, default: Any = None) -> Any:
        """Get context variable."""
        return self._variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set context variable."""
        self._variables[key] = value

    def update(self, variables: Dict[str, Any]) -> None:
        """Update multiple context variables."""
        self._variables.update(variables)

    def delete(self, key: str) -> bool:
        """Delete context variable."""
        if key in self._variables:
            del self._variables[key]
            return True
        return False

    @property
    def variables(self) -> Dict[str, Any]:
        """Get all context variables (read-only copy)."""
        return self._variables.copy()

    # =========================================================================
    # File Context (Claude Code pattern)
    # =========================================================================

    def add_file(
        self,
        filepath: str,
        content: str,
        start_line: int = 1,
        end_line: int = 0,
        added_by: str = "user",
    ) -> bool:
        """
        Add file to context.

        Args:
            filepath: Path to file
            content: File content
            start_line: Start line (1-indexed)
            end_line: End line (0 = entire file)
            added_by: Who added the file

        Returns:
            True if added successfully
        """
        file_ctx = FileContext(
            filepath=filepath,
            content=content,
            start_line=start_line,
            end_line=end_line,
            added_by=added_by,
        )

        # Check token budget
        if self._token_usage + file_ctx.tokens > self.max_tokens:
            logger.warning(f"Cannot add {filepath}: would exceed token limit")
            return False

        self._files[filepath] = file_ctx
        self._token_usage += file_ctx.tokens
        return True

    def remove_file(self, filepath: str) -> bool:
        """Remove file from context."""
        if filepath in self._files:
            self._token_usage -= self._files[filepath].tokens
            del self._files[filepath]
            return True
        return False

    def get_file(self, filepath: str) -> Optional[FileContext]:
        """Get file context."""
        return self._files.get(filepath)

    def list_files(self) -> List[str]:
        """List files in context."""
        return list(self._files.keys())

    @property
    def files(self) -> Dict[str, FileContext]:
        """Get all file contexts."""
        return self._files.copy()

    # =========================================================================
    # Message History
    # =========================================================================

    def add_message(self, role: str, content: str) -> None:
        """Add message to history."""
        self._messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": time.time(),
            }
        )
        self._token_usage += len(content) // 4

        # Check if compaction needed
        if self._should_compact():
            self._trigger_compaction()

    def get_messages(self, limit: int = 0) -> List[Dict[str, str]]:
        """Get recent messages."""
        if limit <= 0:
            return self._messages.copy()
        return self._messages[-limit:]

    # =========================================================================
    # Decision Tracking
    # =========================================================================

    def record_decision(
        self,
        decision_type: DecisionType,
        description: str,
        agent_id: str = "",
        reasoning: str = "",
        alternatives: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> Decision:
        """
        Record a decision made during execution.

        Args:
            decision_type: Type of decision
            description: What was decided
            agent_id: Which agent made decision
            reasoning: Why this decision
            alternatives: Other options considered
            confidence: Confidence level (0-1)

        Returns:
            Created Decision object
        """
        decision = Decision(
            decision_type=decision_type,
            agent_id=agent_id or self.current_agent or "unknown",
            description=description,
            reasoning=reasoning,
            alternatives_considered=alternatives or [],
            confidence=confidence,
        )
        self._decisions.append(decision)
        return decision

    def record_error(
        self,
        error_type: str,
        error_message: str,
        agent_id: str = "",
        step_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> ErrorContext:
        """Record an error encountered during execution."""
        error = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            agent_id=agent_id or self.current_agent or "unknown",
            step_id=step_id,
            stack_trace=stack_trace,
        )
        self._errors.append(error)
        return error

    def get_decisions(
        self,
        decision_type: Optional[DecisionType] = None,
        agent_id: Optional[str] = None,
    ) -> List[Decision]:
        """Get decisions with optional filtering."""
        decisions = self._decisions
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        if agent_id:
            decisions = [d for d in decisions if d.agent_id == agent_id]
        return decisions

    def get_errors(self) -> List[ErrorContext]:
        """Get all errors."""
        return self._errors.copy()

    # =========================================================================
    # Thought Signatures (Gemini pattern)
    # =========================================================================

    def add_thought(
        self,
        agent_id: str,
        reasoning: str,
        insights: List[str],
        next_action: str,
    ) -> ThoughtSignature:
        """
        Add thought signature to maintain reasoning chain.

        This helps prevent "reasoning drift" in long sessions.
        """
        sig = ThoughtSignature.from_reasoning(
            agent_id=agent_id,
            reasoning=reasoning,
            insights=insights,
            next_action=next_action,
        )
        self._thought_chain.append(sig)

        # Keep only last 10 thoughts
        if len(self._thought_chain) > 10:
            self._thought_chain = self._thought_chain[-10:]

        return sig

    def get_thought_chain(self) -> List[ThoughtSignature]:
        """Get recent thought signatures."""
        return self._thought_chain.copy()

    # =========================================================================
    # Execution State
    # =========================================================================

    def add_step_result(self, result: ExecutionResult) -> None:
        """Add result of executing a step."""
        self.completed_steps.append(result)

    def get_step_result(self, step_id: str) -> Optional[ExecutionResult]:
        """Get result of a specific step."""
        for result in self.completed_steps:
            if result.step_id == step_id:
                return result
        return None

    def has_failures(self) -> bool:
        """Check if any steps failed."""
        return any(not r.success for r in self.completed_steps)

    # =========================================================================
    # Compaction (Claude SDK pattern)
    # =========================================================================

    def _should_compact(self) -> bool:
        """Check if compaction is needed."""
        return self._token_usage >= self.max_tokens * self.COMPACTION_THRESHOLD

    def _trigger_compaction(self) -> None:
        """Trigger automatic compaction."""
        if self.state == ContextState.COMPACTING:
            return

        self.state = ContextState.COMPACTING
        logger.info(f"Context compaction triggered at {self._token_usage} tokens")

        # Strategy 1: Keep only recent messages
        if len(self._messages) > 10:
            old_messages = self._messages[:-10]
            summary_parts = [self._summary] if self._summary else []

            for msg in old_messages:
                # Summarize role and key content
                content = (
                    msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                )
                summary_parts.append(f"[{msg['role']}]: {content}")

            self._summary = "\n".join(summary_parts[-20:])  # Keep last 20 summary entries
            self._messages = self._messages[-10:]

        # Strategy 2: Reduce file content
        for filepath, file_ctx in list(self._files.items()):
            if file_ctx.relevance_score < 0.5:
                self.remove_file(filepath)

        # Recalculate token usage
        self._recalculate_tokens()
        self.state = ContextState.ACTIVE
        logger.info(f"Context compacted to {self._token_usage} tokens")

    def _recalculate_tokens(self) -> None:
        """Recalculate total token usage."""
        tokens = 0

        # Messages
        for msg in self._messages:
            tokens += len(msg.get("content", "")) // 4

        # Summary
        tokens += len(self._summary) // 4

        # Files
        for file_ctx in self._files.values():
            tokens += file_ctx.tokens

        # Request and intent
        tokens += len(self.user_request) // 4
        tokens += len(self.user_intent) // 4

        self._token_usage = tokens

    def compact(self, summarizer: Optional[Callable[[str], str]] = None) -> str:
        """
        Manually trigger compaction with optional LLM summarizer.

        Args:
            summarizer: Optional function to summarize content

        Returns:
            Summary of compacted content
        """
        if summarizer:
            # Use LLM to create intelligent summary
            full_content = self.to_prompt_context()
            self._summary = summarizer(full_content)
            self._messages = []  # Clear after summarization
        else:
            self._trigger_compaction()

        return self._summary

    # =========================================================================
    # Serialization (delegated to serialization module)
    # =========================================================================

    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompt."""
        from .serialization import generate_prompt_context

        return generate_prompt_context(self)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire context to dictionary."""
        from .serialization import context_to_dict

        return context_to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedContext":
        """Deserialize from dictionary."""
        from .serialization import context_from_dict

        return context_from_dict(cls, data)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_token_usage(self) -> Tuple[int, int]:
        """Get (used, max) token counts."""
        return self._token_usage, self.max_tokens

    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "token_usage": f"{self._token_usage}/{self.max_tokens}",
            "usage_percent": f"{(self._token_usage / self.max_tokens * 100):.1f}%",
            "files": len(self._files),
            "messages": len(self._messages),
            "decisions": len(self._decisions),
            "errors": len(self._errors),
            "thoughts": len(self._thought_chain),
            "completed_steps": len(self.completed_steps),
        }

    def clear(self) -> None:
        """Clear all context (fresh start)."""
        self._variables.clear()
        self._messages.clear()
        self._files.clear()
        self._decisions.clear()
        self._errors.clear()
        self._thought_chain.clear()
        self.completed_steps.clear()
        self._summary = ""
        self._token_usage = 0
        self.state = ContextState.ACTIVE


__all__ = ["UnifiedContext"]
