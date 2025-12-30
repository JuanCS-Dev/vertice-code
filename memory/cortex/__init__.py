"""
Memory Cortex - MIRIX 6-Type Architecture

Implements the MIRIX memory system (arXiv:2507.07957):
1. Core Memory - Agent identity (persona + human blocks)
2. Episodic Memory - Time-stamped events
3. Semantic Memory - Knowledge graph (LanceDB vectors)
4. Procedural Memory - Learned workflows
5. Resource Memory - External documents
6. Knowledge Vault - Secure sensitive data

Plus:
- Working Memory - Ephemeral task context
- Active Retrieval - Automatic context injection

Stack:
- SQLite: Structured data (zero setup, file-based)
- LanceDB: Vector embeddings (optional, embedded)

Reference: https://arxiv.org/abs/2507.07957
"""

from .memory import (
    MemoryCortex,
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    Memory,
    Contribution,
    get_cortex,
    LANCEDB_AVAILABLE,
)
from .core import CoreMemory, CoreBlockType, CoreBlock
from .procedural import ProceduralMemory, ProcedureType, Procedure
from .resource import ResourceMemory, ResourceType, Resource
from .vault import KnowledgeVault, VaultEntryType, SensitivityLevel, VaultEntry

__all__ = [
    # Main cortex
    "MemoryCortex",
    "get_cortex",
    "LANCEDB_AVAILABLE",
    # Data classes
    "Memory",
    "Contribution",
    # Core memory
    "CoreMemory",
    "CoreBlockType",
    "CoreBlock",
    # Working memory
    "WorkingMemory",
    # Episodic memory
    "EpisodicMemory",
    # Semantic memory
    "SemanticMemory",
    # Procedural memory
    "ProceduralMemory",
    "ProcedureType",
    "Procedure",
    # Resource memory
    "ResourceMemory",
    "ResourceType",
    "Resource",
    # Knowledge vault
    "KnowledgeVault",
    "VaultEntryType",
    "SensitivityLevel",
    "VaultEntry",
]
