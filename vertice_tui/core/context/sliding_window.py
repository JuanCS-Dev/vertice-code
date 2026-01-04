"""
SlidingWindowCompressor - Gemini-Style Context Compression.

Implements progressive truncation and sliding window patterns from Gemini 3:
- Automatic context length management
- Progressive truncation of older content
- Maintains logical thread of recent exchanges
- Configurable window sizes and overlap

Key Features:
- Prevents abrupt terminations due to context limits
- Smooth degradation as context grows
- Priority-based retention (recent > important > old)

References:
- Google Gemini 3 context compression (Dec 2025)
- "Longer Sessions via Context Compression" - Gemini API docs

Phase 10: Sprint 4 - Context Optimization

Soli Deo Gloria
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Token estimation
CHARS_PER_TOKEN = 4


class WindowStrategy(str, Enum):
    """Sliding window strategies."""

    FIFO = "fifo"  # First In First Out (simple)
    PRIORITY = "priority"  # Based on message priority
    HIERARCHICAL = "hierarchical"  # Tiered compression
    ADAPTIVE = "adaptive"  # Adjusts based on content


class RetentionPolicy(str, Enum):
    """What to retain during compression."""

    RECENT_ONLY = "recent_only"  # Keep only recent messages
    BOOKENDS = "bookends"  # Keep first + last messages
    IMPORTANT = "important"  # Keep high-priority messages
    SUMMARIZE = "summarize"  # Summarize removed content


@dataclass
class WindowConfig:
    """Configuration for sliding window compression."""

    # Window sizes (in tokens)
    max_tokens: int = 32_000
    target_tokens: int = 24_000  # Target after compression
    min_tokens: int = 4_000  # Minimum to keep

    # Trigger thresholds
    trigger_percent: float = 0.85  # Trigger at 85% capacity
    emergency_percent: float = 0.95  # Emergency at 95%

    # Retention settings
    keep_recent_messages: int = 10  # Always keep last N
    keep_first_messages: int = 2  # Keep first N (system context)
    overlap_tokens: int = 500  # Overlap between windows

    # Strategy
    strategy: WindowStrategy = WindowStrategy.PRIORITY
    retention: RetentionPolicy = RetentionPolicy.BOOKENDS

    # Progressive truncation
    truncation_steps: int = 3  # Number of progressive steps
    truncation_ratio: float = 0.7  # Keep 70% at each step


@dataclass
class WindowSlice:
    """A slice of the context window."""

    start_index: int
    end_index: int
    tokens: int
    priority: float
    content_hash: str
    is_summary: bool = False


@dataclass
class CompressionResult:
    """Result of window compression."""

    success: bool
    tokens_before: int
    tokens_after: int
    messages_before: int
    messages_after: int
    strategy_used: WindowStrategy
    compression_ratio: float
    duration_ms: float
    summary_generated: str = ""
    removed_hashes: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        return self.tokens_before - self.tokens_after


@dataclass
class Message:
    """A message in the context window."""

    role: str
    content: str
    priority: float = 1.0
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.tokens == 0:
            self.tokens = len(self.content) // CHARS_PER_TOKEN

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "priority": self.priority,
            "tokens": self.tokens,
        }


class SlidingWindowCompressor:
    """
    Gemini-style sliding window context compressor.

    Implements progressive truncation pattern:
    1. Monitor token usage continuously
    2. When approaching limit, compress oldest content
    3. Maintain overlap for continuity
    4. Preserve system context and recent messages

    Usage:
        compressor = SlidingWindowCompressor(config)

        # Add messages
        compressor.add_message("user", "Hello")
        compressor.add_message("assistant", "Hi there!")

        # Check if compression needed
        if compressor.needs_compression():
            result = compressor.compress()

        # Get context for LLM
        context = compressor.get_context_string()
    """

    def __init__(
        self,
        config: Optional[WindowConfig] = None,
        summarizer: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize sliding window compressor.

        Args:
            config: Window configuration
            summarizer: Optional LLM function for summarization
        """
        self.config = config or WindowConfig()
        self._summarizer = summarizer
        self._messages: List[Message] = []
        self._summary: str = ""
        self._compression_history: List[CompressionResult] = []

    @property
    def total_tokens(self) -> int:
        """Total tokens in window."""
        msg_tokens = sum(m.tokens for m in self._messages)
        summary_tokens = len(self._summary) // CHARS_PER_TOKEN
        return msg_tokens + summary_tokens

    @property
    def utilization(self) -> float:
        """Current utilization (0.0 to 1.0)."""
        return self.total_tokens / max(self.config.max_tokens, 1)

    @property
    def message_count(self) -> int:
        """Number of messages in window."""
        return len(self._messages)

    def add_message(
        self,
        role: str,
        content: str,
        priority: float = 1.0,
        **metadata: Any,
    ) -> bool:
        """
        Add a message to the window.

        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            priority: Importance (1.0 = high, 0.0 = low)
            **metadata: Additional metadata

        Returns:
            True if added, False if compression needed first
        """
        msg = Message(
            role=role,
            content=content,
            priority=priority,
            metadata=metadata,
        )

        # Check if would exceed limit
        if self.total_tokens + msg.tokens > self.config.max_tokens:
            # Try auto-compression
            if self.needs_compression():
                self.compress()

            # Check again
            if self.total_tokens + msg.tokens > self.config.max_tokens:
                return False

        self._messages.append(msg)
        return True

    def needs_compression(self) -> bool:
        """Check if compression is needed."""
        return self.utilization >= self.config.trigger_percent

    def needs_emergency_compression(self) -> bool:
        """Check if emergency compression is needed."""
        return self.utilization >= self.config.emergency_percent

    def compress(
        self,
        strategy: Optional[WindowStrategy] = None,
        force: bool = False,
    ) -> CompressionResult:
        """
        Compress the context window.

        Args:
            strategy: Compression strategy (uses config default if None)
            force: Force compression even if not needed

        Returns:
            CompressionResult with details
        """
        start_time = time.time()
        strategy = strategy or self.config.strategy

        if not force and not self.needs_compression():
            return CompressionResult(
                success=True,
                tokens_before=self.total_tokens,
                tokens_after=self.total_tokens,
                messages_before=self.message_count,
                messages_after=self.message_count,
                strategy_used=strategy,
                compression_ratio=1.0,
                duration_ms=0,
            )

        tokens_before = self.total_tokens
        messages_before = self.message_count

        try:
            if strategy == WindowStrategy.FIFO:
                result = self._compress_fifo()
            elif strategy == WindowStrategy.PRIORITY:
                result = self._compress_priority()
            elif strategy == WindowStrategy.HIERARCHICAL:
                result = self._compress_hierarchical()
            elif strategy == WindowStrategy.ADAPTIVE:
                result = self._compress_adaptive()
            else:
                result = self._compress_fifo()

            duration_ms = (time.time() - start_time) * 1000

            compression_result = CompressionResult(
                success=True,
                tokens_before=tokens_before,
                tokens_after=self.total_tokens,
                messages_before=messages_before,
                messages_after=self.message_count,
                strategy_used=strategy,
                compression_ratio=self.total_tokens / max(tokens_before, 1),
                duration_ms=duration_ms,
                summary_generated=result.get("summary", ""),
                removed_hashes=result.get("removed", []),
            )

            self._compression_history.append(compression_result)
            return compression_result

        except Exception as e:
            return CompressionResult(
                success=False,
                tokens_before=tokens_before,
                tokens_after=self.total_tokens,
                messages_before=messages_before,
                messages_after=self.message_count,
                strategy_used=strategy,
                compression_ratio=1.0,
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

    def _compress_fifo(self) -> Dict[str, Any]:
        """Simple FIFO compression - remove oldest messages."""
        removed = []
        config = self.config

        # Calculate how many tokens to remove
        target = config.target_tokens
        to_remove = self.total_tokens - target

        if to_remove <= 0:
            return {"removed": [], "summary": ""}

        # Keep first N messages (system context)
        first_messages = self._messages[: config.keep_first_messages]

        # Keep last N messages (recent)
        last_messages = self._messages[-config.keep_recent_messages :]

        # Middle messages are candidates for removal
        start_idx = config.keep_first_messages
        end_idx = len(self._messages) - config.keep_recent_messages

        if start_idx >= end_idx:
            # Not enough messages to remove
            return {"removed": [], "summary": ""}

        middle_messages = self._messages[start_idx:end_idx]

        # Remove oldest until we hit target
        tokens_removed = 0
        kept_middle = []

        for msg in reversed(middle_messages):
            if tokens_removed < to_remove:
                tokens_removed += msg.tokens
                removed.append(msg.content_hash)
            else:
                kept_middle.insert(0, msg)

        # Rebuild messages
        self._messages = first_messages + kept_middle + last_messages

        return {"removed": removed, "summary": ""}

    def _compress_priority(self) -> Dict[str, Any]:
        """Priority-based compression - remove low-priority first."""
        removed = []
        config = self.config

        target = config.target_tokens
        to_remove = self.total_tokens - target

        if to_remove <= 0:
            return {"removed": [], "summary": ""}

        # Separate protected messages
        first_messages = self._messages[: config.keep_first_messages]
        last_messages = self._messages[-config.keep_recent_messages :]

        start_idx = config.keep_first_messages
        end_idx = len(self._messages) - config.keep_recent_messages

        if start_idx >= end_idx:
            return {"removed": [], "summary": ""}

        middle_messages = self._messages[start_idx:end_idx]

        # Sort by priority (ascending - lowest priority first)
        sorted_middle = sorted(middle_messages, key=lambda m: m.priority)

        # Remove lowest priority until target reached
        tokens_removed = 0
        to_keep = []

        for msg in sorted_middle:
            if tokens_removed < to_remove:
                tokens_removed += msg.tokens
                removed.append(msg.content_hash)
            else:
                to_keep.append(msg)

        # Restore original order for kept messages
        kept_middle = [m for m in middle_messages if m in to_keep]

        # Rebuild messages
        self._messages = first_messages + kept_middle + last_messages

        return {"removed": removed, "summary": ""}

    def _compress_hierarchical(self) -> Dict[str, Any]:
        """
        Hierarchical compression with tiered summarization.

        Levels:
        1. Recent (verbatim)
        2. Medium-age (truncated)
        3. Old (summarized into context)
        """
        removed = []
        config = self.config

        # Three tiers
        recent_count = config.keep_recent_messages
        medium_count = config.keep_recent_messages
        first_count = config.keep_first_messages

        total = len(self._messages)

        if total <= recent_count + first_count:
            return {"removed": [], "summary": ""}

        # Split into tiers
        first_msgs = self._messages[:first_count]
        recent_start = max(first_count, total - recent_count)
        medium_start = max(first_count, recent_start - medium_count)

        old_msgs = self._messages[first_count:medium_start]
        medium_msgs = self._messages[medium_start:recent_start]
        recent_msgs = self._messages[recent_start:]

        # Summarize old messages
        if old_msgs:
            old_summary = self._summarize_messages(old_msgs)
            for msg in old_msgs:
                removed.append(msg.content_hash)

            # Add to global summary
            if self._summary:
                self._summary = f"{self._summary}\n\n{old_summary}"
            else:
                self._summary = old_summary

        # Truncate medium messages
        truncated_medium = []
        for msg in medium_msgs:
            if msg.tokens > 100:
                # Truncate to ~50% keeping start and end
                content = msg.content
                keep_chars = (msg.tokens * CHARS_PER_TOKEN) // 2
                half = keep_chars // 2
                truncated_content = f"{content[:half]}\n[...truncated...]\n{content[-half:]}"
                truncated_medium.append(
                    Message(
                        role=msg.role,
                        content=truncated_content,
                        priority=msg.priority,
                        timestamp=msg.timestamp,
                        metadata={**msg.metadata, "_truncated": True},
                    )
                )
            else:
                truncated_medium.append(msg)

        # Rebuild
        self._messages = first_msgs + truncated_medium + recent_msgs

        return {"removed": removed, "summary": self._summary}

    def _compress_adaptive(self) -> Dict[str, Any]:
        """
        Adaptive compression based on content analysis.

        Analyzes content type and importance to decide compression.
        """
        # For now, use hierarchical as base
        # Future: analyze content types and adapt strategy
        return self._compress_hierarchical()

    def _summarize_messages(self, messages: List[Message]) -> str:
        """Summarize a list of messages."""
        if not messages:
            return ""

        if self._summarizer:
            # Use LLM summarizer
            full_content = "\n".join(f"[{m.role}]: {m.content[:200]}" for m in messages)
            return self._summarizer(full_content)

        # Simple extractive summary
        summaries = []
        for msg in messages:
            role = msg.role
            content = msg.content[:100]
            first_line = content.split("\n")[0]
            summaries.append(f"[{role}] {first_line}")

        return "Previous context:\n" + "\n".join(summaries[:10])

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages as dicts."""
        return [m.to_dict() for m in self._messages]

    def get_context_string(self) -> str:
        """Get full context as string for LLM."""
        parts = []

        if self._summary:
            parts.append(f"## Context Summary\n{self._summary}")

        if self._messages:
            msg_parts = []
            for msg in self._messages:
                msg_parts.append(f"**{msg.role}**: {msg.content}")
            parts.append("\n\n".join(msg_parts))

        return "\n\n".join(parts)

    def clear(self) -> None:
        """Clear all messages and summary."""
        self._messages.clear()
        self._summary = ""

    def get_stats(self) -> Dict[str, Any]:
        """Get window statistics."""
        return {
            "total_tokens": self.total_tokens,
            "max_tokens": self.config.max_tokens,
            "utilization": f"{self.utilization * 100:.1f}%",
            "message_count": self.message_count,
            "summary_tokens": len(self._summary) // CHARS_PER_TOKEN,
            "compressions": len(self._compression_history),
            "needs_compression": self.needs_compression(),
        }

    def get_compression_history(self) -> List[Dict[str, Any]]:
        """Get compression history."""
        return [
            {
                "tokens_before": r.tokens_before,
                "tokens_after": r.tokens_after,
                "saved": r.tokens_saved,
                "ratio": f"{r.compression_ratio:.2%}",
                "strategy": r.strategy_used.value,
                "duration_ms": r.duration_ms,
            }
            for r in self._compression_history
        ]


# Singleton instance
_compressor: Optional[SlidingWindowCompressor] = None


def get_sliding_window() -> SlidingWindowCompressor:
    """Get or create singleton sliding window compressor."""
    global _compressor
    if _compressor is None:
        _compressor = SlidingWindowCompressor()
    return _compressor


__all__ = [
    "WindowStrategy",
    "RetentionPolicy",
    "WindowConfig",
    "WindowSlice",
    "CompressionResult",
    "Message",
    "SlidingWindowCompressor",
    "get_sliding_window",
]
