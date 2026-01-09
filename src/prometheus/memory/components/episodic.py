"""
Episodic Memory - "What happened"

Stores past experiences with temporal context.
Enables learning from previous successes and failures.

Reference: +47% adaptation to new situations (arXiv:2502.06975)
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional

from .types import MemoryEntry, MemoryType


class EpisodicMemory:
    """
    Episodic Memory subsystem.

    Stores experiences and enables recall based on:
    - Similarity to current situation
    - Outcome type (success/failure)
    - Recency
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize episodic memory.

        Args:
            max_entries: Maximum number of entries to retain
        """
        self.entries: List[MemoryEntry] = []
        self.max_entries = max_entries
        self._index: Dict[str, int] = {}

    def store(
        self,
        experience: str,
        outcome: str,
        context: dict,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """
        Store an experience.

        Args:
            experience: What happened
            outcome: Result of the experience
            context: Additional context
            importance: How important (0-1)
            tags: Optional tags for retrieval

        Returns:
            Created memory entry
        """
        entry_id = self._generate_id(experience)

        entry = MemoryEntry(
            id=entry_id,
            type=MemoryType.EPISODIC,
            content=f"Experience: {experience}\nOutcome: {outcome}",
            metadata={
                "context": context,
                "outcome_type": self._classify_outcome(outcome),
                "experience_raw": experience,
                "outcome_raw": outcome,
            },
            importance=importance,
            tags=tags or [],
        )

        self.entries.append(entry)
        self._index[entry_id] = len(self.entries) - 1
        self._prune_if_needed()

        return entry

    def recall_similar(
        self,
        query: str,
        top_k: int = 5,
        min_relevance: float = 0.0,
    ) -> List[MemoryEntry]:
        """
        Retrieve similar experiences.

        Uses keyword matching (can be upgraded to embeddings).
        """
        query_words = set(self._tokenize(query))
        scored_entries = []

        for entry in self.entries:
            entry_words = set(self._tokenize(entry.content))
            overlap = len(query_words & entry_words)

            if overlap > 0:
                similarity = overlap / len(query_words | entry_words)
                relevance = entry.compute_relevance()
                combined_score = 0.6 * similarity + 0.4 * relevance

                if combined_score >= min_relevance:
                    scored_entries.append((combined_score, entry))
                    entry.update_access()

        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:top_k]]

    def recall_by_outcome(self, outcome_type: str) -> List[MemoryEntry]:
        """Retrieve experiences by outcome type (success/failure)."""
        return [
            e for e in self.entries if e.metadata.get("outcome_type") == outcome_type
        ]

    def recall_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Retrieve most recent experiences."""
        sorted_entries = sorted(self.entries, key=lambda e: e.created_at, reverse=True)
        return sorted_entries[:n]

    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get entry by ID."""
        idx = self._index.get(entry_id)
        if idx is not None and idx < len(self.entries):
            return self.entries[idx]
        return None

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for entry."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:12]

    def _classify_outcome(self, outcome: str) -> str:
        """Classify outcome as success, failure, or neutral."""
        outcome_lower = outcome.lower()
        success_keywords = [
            "success",
            "completed",
            "achieved",
            "solved",
            "correct",
            "passed",
        ]
        failure_keywords = [
            "fail",
            "error",
            "wrong",
            "incorrect",
            "crashed",
            "timeout",
        ]

        if any(kw in outcome_lower for kw in success_keywords):
            return "success"
        elif any(kw in outcome_lower for kw in failure_keywords):
            return "failure"
        return "neutral"

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return re.findall(r"\b\w+\b", text.lower())

    def _prune_if_needed(self) -> None:
        """Remove low-relevance entries if exceeding limit."""
        if len(self.entries) > self.max_entries:
            self.entries.sort(key=lambda e: e.compute_relevance(), reverse=True)
            self.entries = self.entries[: self.max_entries]
            self._index = {e.id: i for i, e in enumerate(self.entries)}

    def export(self) -> List[dict]:
        """Export all entries."""
        return [e.to_dict() for e in self.entries]

    def import_entries(self, data: List[dict]) -> None:
        """Import entries from export."""
        for item in data:
            entry = MemoryEntry(
                id=item["id"],
                type=MemoryType(item["type"]),
                content=item["content"],
                metadata=item.get("metadata", {}),
                created_at=datetime.fromisoformat(item["created_at"]),
                importance=item.get("importance", 0.5),
                tags=item.get("tags", []),
            )
            self.entries.append(entry)
            self._index[entry.id] = len(self.entries) - 1


__all__ = ["EpisodicMemory"]
