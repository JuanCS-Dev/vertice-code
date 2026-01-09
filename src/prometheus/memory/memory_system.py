"""
MIRIX-inspired 6-Type Memory System - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- components/types.py: MemoryType, MemoryEntry
- components/episodic.py: EpisodicMemory
- components/semantic.py: SemanticMemory
- components/procedural.py: ProceduralMemory
- system.py: MemorySystem

All symbols are re-exported here for backward compatibility.
Import from submodules for new code.

Reference: arXiv:2507.07957 - MIRIX: Multi-Agent Memory System for LLM-Based Agents
Additional: arXiv:2502.06975 - +47% adaptation with episodic memory
"""

# Re-export all public symbols for backward compatibility
from .components import (
    MemoryType,
    MemoryEntry,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
)
from .system import MemorySystem

__all__ = [
    "MemoryType",
    "MemoryEntry",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "MemorySystem",
]
