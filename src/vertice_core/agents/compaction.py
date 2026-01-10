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

# Re-export everything from the modular structure for backward compatibility
from vertice_core.agents.compaction import (
    CompactionConfig,
    CompactionResult,
    CompactionStrategy,
    CompactionTrigger,
    ContextCompactor,
    HierarchicalStrategy,
    LLMSummaryStrategy,
    MaskedObservation,
    ObservationMaskingStrategy,
    auto_compact,
    compact_with_strategy,
)

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
