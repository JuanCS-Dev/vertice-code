"""
Context Awareness System - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- context_awareness/types.py: ContentType, ContextItem, FileRelevance, etc.
- context_awareness/scoring.py: RelevanceScorer
- context_awareness/rendering.py: Panel rendering functions
- context_awareness/engine.py: ContextAwarenessEngine

All symbols are re-exported here for backward compatibility.
Import from 'context_awareness' subpackage for new code.

Research-Driven Features (Nov 2025):
1. Intelligent file relevance scoring (Cursor/Cody inspiration)
2. Auto-context optimization (token efficiency)
3. Workspace intelligence (semantic understanding)
4. Smart suggestions based on context

Constitutional Compliance:
- P1 (Completude): Full context state tracking
- P2 (Validacao): Validates context relevance
- P3 (Ceticismo): Questions unnecessary context
- P6 (Eficiencia): Minimizes token usage (<10% overhead)
"""

# Re-export all public symbols for backward compatibility
from .context_awareness import (
    # Types
    ContentType,
    ContextItem,
    OptimizationMetrics,
    FileRelevance,
    TokenUsageSnapshot,
    ContextWindow,
    # Engine
    ContextAwarenessEngine,
)

__all__ = [
    "ContentType",
    "ContextItem",
    "OptimizationMetrics",
    "FileRelevance",
    "TokenUsageSnapshot",
    "ContextWindow",
    "ContextAwarenessEngine",
]
