"""
Compaction Types - Data structures for context compaction.

Contains all enums, dataclasses, and type definitions for the compaction system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
        """Calculate tokens saved."""
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


__all__ = [
    "CompactionStrategy",
    "CompactionTrigger",
    "CompactionConfig",
    "CompactionResult",
    "MaskedObservation",
]
