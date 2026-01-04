"""
Compaction - Intelligent Context Compression.

Implements context compression strategies from 2025 research:
- Observation Masking: Remove verbose tool outputs (best for agentic loops)
- Hierarchical Summarization: Recent verbatim, older summarized
- LLM Summarization: Emergency mode with intelligent compression

Key insight: Observation masking > LLM summarization for agent loops
because it preserves critical details while removing noise.

References:
- JetBrains Research: Smarter Context Management (Dec 2025)
- KVzip: 3-4x compression maintaining accuracy
- mem0: Memory formation patterns

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
)

from .context import UnifiedContext

logger = logging.getLogger(__name__)


class CompactionStrategy(str, Enum):
    """Available compaction strategies."""

    OBSERVATION_MASKING = "observation_masking"  # Default, best for agents
    HIERARCHICAL = "hierarchical"  # Multi-level summarization
    LLM_SUMMARY = "llm_summary"  # LLM-based (expensive)
    HYBRID = "hybrid"  # Combination of above
    NONE = "none"  # No compaction


class CompactionTrigger(str, Enum):
    """When to trigger compaction."""

    THRESHOLD = "threshold"  # At X% capacity
    PERIODIC = "periodic"  # Every N messages
    MANUAL = "manual"  # Explicit call only
    ADAPTIVE = "adaptive"  # Based on context importance


@dataclass
class CompactionConfig:
    """Configuration for compaction behavior."""

    # Thresholds
    trigger_threshold: float = 0.85  # Trigger at 85% capacity
    target_threshold: float = 0.60  # Compact down to 60%
    emergency_threshold: float = 0.95  # Force aggressive compaction

    # Message retention
    keep_recent_messages: int = 10  # Always keep last N messages
    keep_recent_tool_calls: int = 5  # Keep last N tool results
    keep_decisions: int = 10  # Keep last N decisions

    # Strategy
    default_strategy: CompactionStrategy = CompactionStrategy.OBSERVATION_MASKING
    fallback_strategy: CompactionStrategy = CompactionStrategy.HIERARCHICAL

    # LLM settings
    llm_model: str = "gpt-4o-mini"  # Fast, cheap for summarization
    max_summary_tokens: int = 500

    # Observation masking
    max_tool_output_chars: int = 500  # Truncate tool output
    mask_patterns: List[str] = field(
        default_factory=lambda: [
            r"^\s+",  # Leading whitespace
            r"\n{3,}",  # Multiple newlines
            r"```[\s\S]*?```",  # Code blocks (keep summary)
        ]
    )


@dataclass
class CompactionResult:
    """Result of a compaction operation."""

    success: bool
    strategy_used: CompactionStrategy
    tokens_before: int
    tokens_after: int
    compression_ratio: float
    duration_ms: float
    messages_removed: int
    summary_generated: str = ""
    error: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        return self.tokens_before - self.tokens_after


@dataclass
class MaskedObservation:
    """An observation (tool output) with masking applied."""

    original_hash: str  # For verification
    tool_name: str
    summary: str
    key_values: Dict[str, Any]
    success: bool
    timestamp: float


class CompactionStrategy_ABC(ABC):
    """Base class for compaction strategies."""

    @abstractmethod
    def compact(
        self,
        context: UnifiedContext,
        config: CompactionConfig,
    ) -> CompactionResult:
        """Compact the context."""
        pass


class ObservationMaskingStrategy(CompactionStrategy_ABC):
    """
    Observation masking strategy.

    Removes verbose tool outputs while preserving:
    - Command/tool name
    - Success/failure status
    - Key output values
    - Error messages

    This is the BEST strategy for agentic loops (Dec 2025 research).
    """

    # Tool output patterns to extract key info
    EXTRACT_PATTERNS = {
        "error": r"(?:error|exception|failed):\s*(.+?)(?:\n|$)",
        "success": r"(?:success|completed|done)(?::\s*(.+?))?(?:\n|$)",
        "count": r"(\d+)\s+(?:files?|items?|matches?|results?)",
        "path": r"(?:file|path|location):\s*(.+?)(?:\n|$)",
    }

    def compact(
        self,
        context: UnifiedContext,
        config: CompactionConfig,
    ) -> CompactionResult:
        """Apply observation masking to context."""
        start_time = time.time()
        tokens_before = context._token_usage
        messages_removed = 0

        messages = context._messages.copy()
        masked_messages = []

        # Keep recent messages verbatim
        recent_count = config.keep_recent_messages

        for i, msg in enumerate(messages):
            is_recent = i >= len(messages) - recent_count

            if is_recent:
                # Keep verbatim
                masked_messages.append(msg)
            else:
                # Apply masking
                content = msg.get("content", "")
                role = msg.get("role", "")

                if role == "tool" or self._is_tool_output(content):
                    # Mask tool output
                    masked = self._mask_tool_output(content, config)
                    if masked:
                        masked_messages.append(
                            {
                                **msg,
                                "content": masked,
                                "_masked": True,
                            }
                        )
                    else:
                        messages_removed += 1
                elif len(content) > config.max_tool_output_chars * 2:
                    # Truncate very long messages
                    truncated = content[: config.max_tool_output_chars] + "\n[...truncated...]"
                    masked_messages.append(
                        {
                            **msg,
                            "content": truncated,
                            "_truncated": True,
                        }
                    )
                else:
                    masked_messages.append(msg)

        # Update context
        context._messages = masked_messages
        context._recalculate_tokens()

        tokens_after = context._token_usage
        duration_ms = (time.time() - start_time) * 1000

        return CompactionResult(
            success=True,
            strategy_used=CompactionStrategy.OBSERVATION_MASKING,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=tokens_after / max(tokens_before, 1),
            duration_ms=duration_ms,
            messages_removed=messages_removed,
        )

    def _is_tool_output(self, content: str) -> bool:
        """Check if content looks like tool output."""
        indicators = [
            content.startswith("```"),
            "error:" in content.lower(),
            "output:" in content.lower(),
            len(content.split("\n")) > 10,
            re.search(r"^\s{4,}", content, re.MULTILINE),
        ]
        return sum(bool(i) for i in indicators) >= 2

    def _mask_tool_output(
        self,
        content: str,
        config: CompactionConfig,
    ) -> Optional[str]:
        """
        Mask tool output, extracting key information.

        Returns masked content or None if should be removed.
        """
        # Extract key values
        extracted = {}
        for key, pattern in self.EXTRACT_PATTERNS.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                extracted[key] = match.group(1) if match.lastindex else True

        # Determine success/failure
        if "error" in extracted:
            status = f"❌ Error: {extracted['error'][:100]}"
        elif "success" in extracted:
            status = f"✓ Success"
            if extracted["success"] and extracted["success"] is not True:
                status += f": {extracted['success'][:50]}"
        else:
            status = "→ Executed"

        # Add counts if found
        if "count" in extracted:
            status += f" ({extracted['count']})"

        # Add path if found
        if "path" in extracted:
            status += f"\n  Path: {extracted['path'][:100]}"

        return f"[Tool Output]\n{status}"


class HierarchicalStrategy(CompactionStrategy_ABC):
    """
    Hierarchical summarization strategy.

    Three levels:
    1. Recent messages: Verbatim (last N)
    2. Medium-age messages: Topic-based summary
    3. Old messages: Compact summary
    """

    def compact(
        self,
        context: UnifiedContext,
        config: CompactionConfig,
    ) -> CompactionResult:
        """Apply hierarchical summarization."""
        start_time = time.time()
        tokens_before = context._token_usage

        messages = context._messages.copy()
        total = len(messages)

        if total <= config.keep_recent_messages:
            # Nothing to compact
            return CompactionResult(
                success=True,
                strategy_used=CompactionStrategy.HIERARCHICAL,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                compression_ratio=1.0,
                duration_ms=0,
                messages_removed=0,
            )

        # Split into tiers
        recent_start = max(0, total - config.keep_recent_messages)
        medium_start = max(0, recent_start - config.keep_recent_messages)

        old_messages = messages[:medium_start]
        medium_messages = messages[medium_start:recent_start]
        recent_messages = messages[recent_start:]

        # Summarize old messages
        old_summary = self._summarize_messages(old_messages, "compact")

        # Summarize medium messages
        medium_summary = self._summarize_messages(medium_messages, "detailed")

        # Build new summary
        summary_parts = []
        if context._summary:
            summary_parts.append(context._summary)
        if old_summary:
            summary_parts.append(f"[Earlier]: {old_summary}")
        if medium_summary:
            summary_parts.append(f"[Recent context]: {medium_summary}")

        context._summary = "\n".join(summary_parts)

        # Keep only recent messages
        context._messages = recent_messages

        # Recalculate
        context._recalculate_tokens()

        tokens_after = context._token_usage
        duration_ms = (time.time() - start_time) * 1000
        messages_removed = len(old_messages) + len(medium_messages)

        return CompactionResult(
            success=True,
            strategy_used=CompactionStrategy.HIERARCHICAL,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=tokens_after / max(tokens_before, 1),
            duration_ms=duration_ms,
            messages_removed=messages_removed,
            summary_generated=context._summary,
        )

    def _summarize_messages(
        self,
        messages: List[Dict[str, Any]],
        level: str,
    ) -> str:
        """
        Summarize messages at given level.

        For now, uses extractive summarization.
        Full implementation would use LLM.
        """
        if not messages:
            return ""

        # Extract key content
        summaries = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if level == "compact":
                # Very brief
                if role == "user":
                    first_line = content.split("\n")[0][:50]
                    summaries.append(f"User: {first_line}")
                elif role == "assistant":
                    # Extract first action/statement
                    first_line = content.split("\n")[0][:30]
                    summaries.append(f"→ {first_line}")
            else:
                # More detailed
                if role == "user":
                    summaries.append(f"User asked: {content[:100]}")
                elif role == "assistant":
                    summaries.append(f"Assistant: {content[:150]}")

        return " | ".join(summaries[:10])


class LLMSummaryStrategy(CompactionStrategy_ABC):
    """
    LLM-based summarization strategy.

    Most expensive but most intelligent.
    Use only for emergency compaction.
    """

    SUMMARY_PROMPT = """Summarize this conversation context concisely.
Focus on:
1. User's original goal/request
2. Key decisions made
3. Current state/progress
4. Important files/code mentioned

Context to summarize:
{context}

Provide a concise summary (max 500 tokens):"""

    def __init__(
        self,
        llm_func: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize with LLM function.

        Args:
            llm_func: Function that takes prompt, returns completion
        """
        self._llm_func = llm_func

    def compact(
        self,
        context: UnifiedContext,
        config: CompactionConfig,
    ) -> CompactionResult:
        """Apply LLM summarization."""
        start_time = time.time()
        tokens_before = context._token_usage

        if not self._llm_func:
            # Fall back to hierarchical
            fallback = HierarchicalStrategy()
            return fallback.compact(context, config)

        try:
            # Generate full context
            full_context = context.to_prompt_context()

            # Call LLM for summary
            prompt = self.SUMMARY_PROMPT.format(context=full_context)
            summary = self._llm_func(prompt)

            # Replace context with summary
            old_summary = context._summary
            context._summary = summary
            context._messages = context._messages[-config.keep_recent_messages :]

            # Recalculate
            context._recalculate_tokens()

            tokens_after = context._token_usage
            duration_ms = (time.time() - start_time) * 1000

            return CompactionResult(
                success=True,
                strategy_used=CompactionStrategy.LLM_SUMMARY,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                compression_ratio=tokens_after / max(tokens_before, 1),
                duration_ms=duration_ms,
                messages_removed=len(context._messages),
                summary_generated=summary,
            )

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return CompactionResult(
                success=False,
                strategy_used=CompactionStrategy.LLM_SUMMARY,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                compression_ratio=1.0,
                duration_ms=(time.time() - start_time) * 1000,
                messages_removed=0,
                error=str(e),
            )


class ContextCompactor:
    """
    Main compaction manager.

    Automatically selects and applies compaction strategies
    based on context state and configuration.

    Usage:
        compactor = ContextCompactor(context)
        result = compactor.compact()  # Auto-select strategy

        # Or specific strategy
        result = compactor.compact(strategy=CompactionStrategy.HIERARCHICAL)
    """

    def __init__(
        self,
        context: UnifiedContext,
        config: Optional[CompactionConfig] = None,
        llm_func: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize compactor.

        Args:
            context: Context to manage
            config: Compaction configuration
            llm_func: Optional LLM function for summarization
        """
        self.context = context
        self.config = config or CompactionConfig()
        self._llm_func = llm_func

        # Strategy instances
        self._strategies = {
            CompactionStrategy.OBSERVATION_MASKING: ObservationMaskingStrategy(),
            CompactionStrategy.HIERARCHICAL: HierarchicalStrategy(),
            CompactionStrategy.LLM_SUMMARY: LLMSummaryStrategy(llm_func),
        }

        # History
        self._compaction_history: List[CompactionResult] = []

    def should_compact(self) -> bool:
        """Check if compaction is needed."""
        usage = self.context._token_usage / self.context.max_tokens
        return usage >= self.config.trigger_threshold

    def needs_emergency_compact(self) -> bool:
        """Check if emergency compaction is needed."""
        usage = self.context._token_usage / self.context.max_tokens
        return usage >= self.config.emergency_threshold

    def get_recommended_strategy(self) -> CompactionStrategy:
        """Get recommended strategy based on current state."""
        if self.needs_emergency_compact():
            # Emergency: use LLM if available
            if self._llm_func:
                return CompactionStrategy.LLM_SUMMARY
            return CompactionStrategy.HIERARCHICAL

        # Normal: use observation masking (best for agents)
        return self.config.default_strategy

    def compact(
        self,
        strategy: Optional[CompactionStrategy] = None,
        force: bool = False,
    ) -> CompactionResult:
        """
        Compact the context.

        Args:
            strategy: Strategy to use (None = auto-select)
            force: Force compaction even if not needed

        Returns:
            CompactionResult with details
        """
        if not force and not self.should_compact():
            return CompactionResult(
                success=True,
                strategy_used=CompactionStrategy.NONE,
                tokens_before=self.context._token_usage,
                tokens_after=self.context._token_usage,
                compression_ratio=1.0,
                duration_ms=0,
                messages_removed=0,
            )

        # Select strategy
        if strategy is None:
            strategy = self.get_recommended_strategy()

        if strategy == CompactionStrategy.NONE:
            return CompactionResult(
                success=True,
                strategy_used=CompactionStrategy.NONE,
                tokens_before=self.context._token_usage,
                tokens_after=self.context._token_usage,
                compression_ratio=1.0,
                duration_ms=0,
                messages_removed=0,
            )

        # Get strategy instance
        strategy_impl = self._strategies.get(strategy)
        if not strategy_impl:
            logger.warning(f"Unknown strategy: {strategy}, using default")
            strategy_impl = self._strategies[self.config.default_strategy]

        # Execute
        logger.info(f"Compacting with strategy: {strategy.value}")
        result = strategy_impl.compact(self.context, self.config)

        # Record history
        self._compaction_history.append(result)

        logger.info(
            f"Compaction complete: {result.tokens_before} → {result.tokens_after} "
            f"({result.compression_ratio:.2%})"
        )

        return result

    def auto_compact(self) -> Optional[CompactionResult]:
        """
        Automatically compact if needed.

        Returns result if compaction occurred, None otherwise.
        """
        if self.should_compact():
            return self.compact()
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get compaction statistics."""
        total_compactions = len(self._compaction_history)
        total_saved = sum(r.tokens_saved for r in self._compaction_history)

        return {
            "total_compactions": total_compactions,
            "total_tokens_saved": total_saved,
            "average_compression": (
                sum(r.compression_ratio for r in self._compaction_history)
                / max(total_compactions, 1)
            ),
            "current_usage": f"{self.context._token_usage}/{self.context.max_tokens}",
            "current_percent": f"{self.context._token_usage / self.context.max_tokens * 100:.1f}%",
            "should_compact": self.should_compact(),
            "needs_emergency": self.needs_emergency_compact(),
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get compaction history."""
        return [
            {
                "strategy": r.strategy_used.value,
                "tokens_before": r.tokens_before,
                "tokens_after": r.tokens_after,
                "saved": r.tokens_saved,
                "ratio": f"{r.compression_ratio:.2%}",
                "messages_removed": r.messages_removed,
                "duration_ms": r.duration_ms,
            }
            for r in self._compaction_history
        ]


# Convenience functions
def auto_compact(context: UnifiedContext) -> Optional[CompactionResult]:
    """Auto-compact context if needed."""
    compactor = ContextCompactor(context)
    return compactor.auto_compact()


def compact_with_strategy(
    context: UnifiedContext,
    strategy: CompactionStrategy,
) -> CompactionResult:
    """Compact with specific strategy."""
    compactor = ContextCompactor(context)
    return compactor.compact(strategy=strategy, force=True)


__all__ = [
    "CompactionStrategy",
    "CompactionTrigger",
    "CompactionConfig",
    "CompactionResult",
    "MaskedObservation",
    "ObservationMaskingStrategy",
    "HierarchicalStrategy",
    "LLMSummaryStrategy",
    "ContextCompactor",
    "auto_compact",
    "compact_with_strategy",
]
