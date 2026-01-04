"""
Context Awareness Module - Smart context management.

Research-Driven Features (Nov 2025):
1. Intelligent file relevance scoring (Cursor/Cody inspiration)
2. Auto-context optimization (token efficiency)
3. Workspace intelligence (semantic understanding)
4. Smart suggestions based on context

Submodules:
    - types: Domain models (ContentType, ContextItem, etc.)
    - scoring: RelevanceScorer for file relevance
    - rendering: Panel rendering functions
    - engine: ContextAwarenessEngine
"""

from .types import (
    ContentType,
    ContextItem,
    OptimizationMetrics,
    FileRelevance,
    TokenUsageSnapshot,
    ContextWindow,
)
from .scoring import RelevanceScorer
from .rendering import render_context_panel, render_token_usage_realtime
from .engine import ContextAwarenessEngine

__all__ = [
    # Types
    "ContentType",
    "ContextItem",
    "OptimizationMetrics",
    "FileRelevance",
    "TokenUsageSnapshot",
    "ContextWindow",
    # Scoring
    "RelevanceScorer",
    # Rendering
    "render_context_panel",
    "render_token_usage_realtime",
    # Engine
    "ContextAwarenessEngine",
]
