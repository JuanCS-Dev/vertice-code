"""
Context Awareness Types - Domain models for context management.

Enums and dataclasses for context tracking.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class ContentType(Enum):
    """Type of content in context."""

    FILE_CONTENT = "file_content"
    TOOL_RESULT = "tool_result"
    CONVERSATION = "conversation"
    CODE_SNIPPET = "code_snippet"
    ERROR_MESSAGE = "error_message"


@dataclass
class ContextItem:
    """Item in the context window with LRU tracking."""

    id: str
    content: str
    content_type: ContentType
    token_count: int
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    relevance_score: float = 1.0
    pinned: bool = False


@dataclass
class OptimizationMetrics:
    """Metrics from optimization operation."""

    items_before: int
    items_after: int
    tokens_before: int
    tokens_after: int
    items_removed: int
    tokens_freed: int
    duration_ms: float


@dataclass
class FileRelevance:
    """File relevance scoring for context optimization."""

    path: str
    score: float  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    last_accessed: Optional[datetime] = None
    token_count: int = 0
    dependencies: Set[str] = field(default_factory=set)

    @property
    def is_relevant(self) -> bool:
        """Check if file meets relevance threshold."""
        return self.score >= 0.5

    @property
    def priority(self) -> str:
        """Get priority level."""
        if self.score >= 0.8:
            return "HIGH"
        elif self.score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"


@dataclass
class TokenUsageSnapshot:
    """Snapshot of token usage at a point in time."""

    timestamp: datetime
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cost_estimate_usd: float = 0.0


@dataclass
class ContextWindow:
    """Represents current context window state (Enhanced DAY 8 Phase 4)."""

    total_tokens: int
    max_tokens: int
    files: Dict[str, FileRelevance] = field(default_factory=dict)
    auto_added: Set[str] = field(default_factory=set)
    user_pinned: Set[str] = field(default_factory=set)

    # Real-time token tracking
    current_input_tokens: int = 0
    current_output_tokens: int = 0
    streaming_tokens: int = 0  # Tokens being streamed right now
    usage_history: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def utilization(self) -> float:
        """Context window utilization (0.0 to 1.0)."""
        return self.total_tokens / self.max_tokens if self.max_tokens > 0 else 0.0

    @property
    def available_tokens(self) -> int:
        """Tokens available for new context."""
        return max(0, self.max_tokens - self.total_tokens)

    @property
    def is_critical(self) -> bool:
        """Check if context is critically full (>90%)."""
        return self.utilization > 0.9

    @property
    def is_warning(self) -> bool:
        """Check if context is in warning zone (>80%)."""
        return self.utilization > 0.8

    def add_token_snapshot(
        self, input_tokens: int, output_tokens: int, cost_estimate: float = 0.0
    ) -> None:
        """Add token usage snapshot."""
        snapshot = TokenUsageSnapshot(
            timestamp=datetime.now(),
            total_tokens=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_estimate_usd=cost_estimate,
        )
        self.usage_history.append(snapshot)
        self.current_input_tokens = input_tokens
        self.current_output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens

    def update_tokens(self, input_tokens: int, output_tokens: int, cost: float = 0.0) -> None:
        """Alias for add_token_snapshot for easier testing."""
        self.add_token_snapshot(input_tokens, output_tokens, cost)


__all__ = [
    "ContentType",
    "ContextItem",
    "OptimizationMetrics",
    "FileRelevance",
    "TokenUsageSnapshot",
    "ContextWindow",
]
