"""
Memory Cortex - Unified Brain for Vertice Agency

Implements the 6-type memory system:
- Working: Active task context
- Episodic: Session history
- Semantic: Knowledge graph (LanceDB vectors)
- Procedural: Learned patterns
- Meta: Self-reflection logs
- Social: Agent interaction patterns

Stack:
- SQLite: Structured data (zero setup, file-based)
- LanceDB: Vector embeddings (embedded, file-based)
"""

from .memory import (
    MemoryCortex,
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    get_cortex,
)

__all__ = [
    "MemoryCortex",
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "get_cortex",
]
