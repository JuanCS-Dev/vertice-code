"""
Semantic Memory - "What I know"

Stores factual knowledge and concepts.
Organized by topics and relations.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Tuple

from .types import MemoryEntry, MemoryType


class SemanticMemory:
    """
    Semantic Memory subsystem.

    Stores factual knowledge organized by:
    - Topics
    - Relations between concepts
    - Keyword index for search
    """

    def __init__(self):
        """Initialize semantic memory."""
        self.facts: Dict[str, MemoryEntry] = {}
        self.relations: Dict[str, List[str]] = {}
        self._topic_index: Dict[str, List[str]] = {}

    def store_fact(
        self,
        topic: str,
        fact: str,
        source: Optional[str] = None,
        confidence: float = 0.8,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """
        Store a factual knowledge entry.

        Args:
            topic: Topic/subject of the fact
            fact: The factual content
            source: Where this fact came from
            confidence: Confidence level (0-1)
            tags: Optional tags

        Returns:
            Created memory entry
        """
        entry = MemoryEntry(
            id=hashlib.md5(topic.encode()).hexdigest()[:12],
            type=MemoryType.SEMANTIC,
            content=fact,
            metadata={
                "topic": topic,
                "source": source,
                "confidence": confidence,
            },
            importance=confidence,
            tags=tags or [],
        )

        self.facts[topic] = entry
        self._update_topic_index(topic, fact)

        return entry

    def query(self, topic: str) -> Optional[MemoryEntry]:
        """Query knowledge by exact topic."""
        entry = self.facts.get(topic)
        if entry:
            entry.update_access()
        return entry

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, MemoryEntry]]:
        """
        Search knowledge by keywords.

        Returns list of (topic, entry) tuples.
        """
        query_words = set(query.lower().split())
        results = []

        for keyword in query_words:
            if keyword in self._topic_index:
                for topic in self._topic_index[keyword]:
                    if topic in self.facts:
                        entry = self.facts[topic]
                        results.append((topic, entry))
                        entry.update_access()

        # Deduplicate and limit
        seen = set()
        unique_results = []
        for topic, entry in results:
            if topic not in seen:
                seen.add(topic)
                unique_results.append((topic, entry))

        return unique_results[:top_k]

    def add_relation(
        self, concept_a: str, concept_b: str, relation_type: str = "related"
    ) -> None:
        """Add a relation between concepts."""
        if concept_a not in self.relations:
            self.relations[concept_a] = []

        relation_entry = f"{relation_type}:{concept_b}"
        if relation_entry not in self.relations[concept_a]:
            self.relations[concept_a].append(relation_entry)

        # Bidirectional for "related"
        if relation_type == "related":
            if concept_b not in self.relations:
                self.relations[concept_b] = []
            reverse_entry = f"{relation_type}:{concept_a}"
            if reverse_entry not in self.relations[concept_b]:
                self.relations[concept_b].append(reverse_entry)

    def get_related(self, concept: str) -> List[str]:
        """Get concepts related to a given concept."""
        if concept not in self.relations:
            return []
        return [r.split(":", 1)[1] for r in self.relations[concept]]

    def update_confidence(self, topic: str, delta: float) -> None:
        """Update confidence for a fact."""
        if topic in self.facts:
            entry = self.facts[topic]
            new_confidence = max(0, min(1, entry.metadata["confidence"] + delta))
            entry.metadata["confidence"] = new_confidence
            entry.importance = new_confidence

    def _update_topic_index(self, topic: str, content: str) -> None:
        """Update keyword index."""
        words = set(topic.lower().split() + content.lower().split())
        for word in words:
            if len(word) > 2:
                if word not in self._topic_index:
                    self._topic_index[word] = []
                if topic not in self._topic_index[word]:
                    self._topic_index[word].append(topic)

    def export(self) -> dict:
        """Export semantic memory."""
        return {
            "facts": {t: e.to_dict() for t, e in self.facts.items()},
            "relations": self.relations,
        }


__all__ = ["SemanticMemory"]
