"""
Vertice Memory System

6-type memory architecture:
- Working: Active task context
- Episodic: Session history
- Semantic: Knowledge graph (LanceDB)
- Procedural: Learned patterns
- Meta: Self-reflection logs
- Social: Agent interaction patterns

Usage:
    from memory.cortex import get_cortex
    cortex = get_cortex()
    cortex.remember("important fact", memory_type="semantic")
"""

from .cortex import MemoryCortex, get_cortex

__all__ = [
    "MemoryCortex",
    "get_cortex",
]
