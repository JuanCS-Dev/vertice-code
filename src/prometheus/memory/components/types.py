"""
Memory Types - Domain models for the MIRIX memory system.

Reference: arXiv:2507.07957 - MIRIX: Multi-Agent Memory System for LLM-Based Agents
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Types of memory in the MIRIX system."""

    CORE = "core"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    RESOURCE = "resource"
    KNOWLEDGE_VAULT = "knowledge_vault"


@dataclass
class MemoryEntry:
    """
    A single memory entry.

    Attributes:
        id: Unique identifier
        type: Type of memory
        content: Main content
        embedding: Optional vector embedding
        metadata: Additional metadata
        created_at: Creation timestamp
        accessed_at: Last access timestamp
        access_count: Number of accesses
        importance: Importance score (0-1)
        tags: Categorization tags
    """

    id: str
    type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "importance": self.importance,
            "tags": self.tags,
        }

    def update_access(self) -> None:
        """Update access time and count."""
        self.accessed_at = datetime.now()
        self.access_count += 1

    def compute_relevance(self, recency_weight: float = 0.3) -> float:
        """
        Compute relevance score based on importance and recency.

        Uses exponential decay for recency.
        """
        days_since_access = (datetime.now() - self.accessed_at).days
        recency_score = math.exp(-0.1 * days_since_access)
        return (1 - recency_weight) * self.importance + recency_weight * recency_score


__all__ = ["MemoryType", "MemoryEntry"]
