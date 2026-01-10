"""
Context Compaction Module - Intelligent context compression for agents.

Provides multiple strategies for compressing conversation context while preserving
critical information. Based on 2025 research showing observation masking is most
effective for agentic loops.
"""

from typing import Optional

from .compactor import ContextCompactor
from .types import CompactionResult, CompactionStrategy
from .strategies import (
    CompactionStrategy_ABC,
    HierarchicalStrategy,
    LLMSummaryStrategy,
    ObservationMaskingStrategy,
)
from .types import (
    CompactionConfig,
    CompactionResult,
    CompactionStrategy,
    CompactionTrigger,
    MaskedObservation,
)


# Convenience functions
def auto_compact(context) -> Optional[CompactionResult]:
    """Auto-compact context if needed."""
    compactor = ContextCompactor(context)
    return compactor.auto_compact()


def compact_with_strategy(context, strategy: CompactionStrategy) -> CompactionResult:
    """Compact with specific strategy."""
    compactor = ContextCompactor(context)
    return compactor.compact(strategy=strategy, force=True)


__all__ = [
    # Main classes
    "ContextCompactor",
    # Strategies
    "CompactionStrategy_ABC",
    "ObservationMaskingStrategy",
    "HierarchicalStrategy",
    "LLMSummaryStrategy",
    # Types
    "CompactionStrategy",
    "CompactionTrigger",
    "CompactionConfig",
    "CompactionResult",
    "MaskedObservation",
    # Functions
    "auto_compact",
    "compact_with_strategy",
]
