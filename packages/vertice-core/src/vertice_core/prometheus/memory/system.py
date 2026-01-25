"""
Unified Memory System (MIRIX-inspired).

Combines all 6 memory types into a unified interface.

Reference: arXiv:2507.07957 - MIRIX: Multi-Agent Memory System
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from .components import (
    EpisodicMemory,
    MemoryEntry,
    MemoryType,
    ProceduralMemory,
    SemanticMemory,
)


class MemorySystem:
    """
    Unified Memory System.

    Provides a single interface to all memory subsystems:
    - Core: Identity and values
    - Episodic: Past experiences
    - Semantic: Factual knowledge
    - Procedural: Learned skills
    - Resource: External resource cache
    - Knowledge Vault: Long-term consolidated knowledge
    """

    def __init__(
        self,
        agent_name: str = "Prometheus",
        max_episodic: int = 1000,
    ):
        """
        Initialize memory system.

        Args:
            agent_name: Name of the agent
            max_episodic: Maximum episodic memory entries
        """
        # Initialize all memory subsystems
        self.episodic = EpisodicMemory(max_entries=max_episodic)
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()

        # Core memory - persistent identity
        self.core: Dict[str, Any] = {
            "name": agent_name,
            "purpose": "Self-evolving agent that improves through experience",
            "values": ["accuracy", "efficiency", "learning", "helpfulness"],
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
        }

        # Resource cache - external resources
        self.resource_cache: Dict[str, Any] = {}

        # Knowledge vault - consolidated long-term knowledge
        self.knowledge_vault: List[MemoryEntry] = []

        # Stats
        self._stats = {
            "total_experiences": 0,
            "total_facts": 0,
            "total_procedures": 0,
            "consolidations": 0,
        }

        # Thread safety lock for concurrent access
        self._lock = threading.RLock()

    # === Core Memory ===

    def get_identity(self) -> Dict[str, Any]:
        """Get agent identity from core memory."""
        return self.core.copy()

    def update_core(self, key: str, value: Any) -> None:
        """Update core memory value."""
        self.core[key] = value

    # === Episodic Memory Interface ===

    def remember_experience(
        self,
        experience: str,
        outcome: str,
        context: Optional[dict] = None,
        importance: float = 0.5,
    ) -> str:
        """Store an experience. Returns entry ID."""
        with self._lock:
            entry = self.episodic.store(
                experience=experience,
                outcome=outcome,
                context=context or {},
                importance=importance,
            )
            self._stats["total_experiences"] += 1
            return entry.id

    def recall_experiences(self, situation: str, top_k: int = 5) -> List[dict]:
        """Recall relevant past experiences."""
        entries = self.episodic.recall_similar(situation, top_k)
        return [e.to_dict() for e in entries]

    def recall_successes(self, top_k: int = 5) -> List[dict]:
        """Recall successful experiences."""
        entries = self.episodic.recall_by_outcome("success")
        entries.sort(key=lambda e: e.importance, reverse=True)
        return [e.to_dict() for e in entries[:top_k]]

    def recall_failures(self, top_k: int = 5) -> List[dict]:
        """Recall failure experiences (for learning)."""
        entries = self.episodic.recall_by_outcome("failure")
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return [e.to_dict() for e in entries[:top_k]]

    # === Semantic Memory Interface ===

    def learn_fact(
        self,
        topic: str,
        fact: str,
        source: Optional[str] = None,
        confidence: float = 0.8,
    ) -> None:
        """Learn a new fact."""
        with self._lock:
            self.semantic.store_fact(topic, fact, source, confidence)
            self._stats["total_facts"] += 1

    def query_knowledge(self, topic: str) -> Optional[str]:
        """Query knowledge about a topic."""
        entry = self.semantic.query(topic)
        return entry.content if entry else None

    def search_knowledge(self, query: str, top_k: int = 5) -> List[dict]:
        """Search knowledge base."""
        results = self.semantic.search(query, top_k)
        return [{"topic": t, "content": e.content} for t, e in results]

    # === Procedural Memory Interface ===

    def learn_procedure(
        self,
        skill_name: str,
        steps: List[str],
        preconditions: Optional[List[str]] = None,
    ) -> None:
        """Learn a new procedure."""
        with self._lock:
            self.procedural.store_procedure(
                skill_name=skill_name,
                steps=steps,
                preconditions=preconditions,
            )
            self._stats["total_procedures"] += 1

    def get_procedure(self, skill_name: str) -> Optional[List[str]]:
        """Get steps for a procedure."""
        return self.procedural.get_steps(skill_name)

    def find_procedures(self, query: str, top_k: int = 5) -> List[dict]:
        """Find relevant procedures."""
        entries = self.procedural.search_procedures(query, top_k)
        return [
            {
                "skill": e.metadata["skill_name"],
                "steps": e.metadata["steps"],
                "success_rate": e.metadata.get("success_rate", 0),
            }
            for e in entries
        ]

    def record_procedure_outcome(self, skill_name: str, success: bool) -> None:
        """Record outcome of procedure execution."""
        self.procedural.update_success_rate(skill_name, success)

    # === Resource Cache ===

    def cache_resource(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Cache an external resource."""
        self.resource_cache[key] = {
            "value": value,
            "cached_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + ttl_seconds),
        }

    def get_cached_resource(self, key: str) -> Optional[Any]:
        """Get cached resource if not expired."""
        if key in self.resource_cache:
            entry = self.resource_cache[key]
            if datetime.now().timestamp() < entry["expires_at"]:
                return entry["value"]
            else:
                del self.resource_cache[key]
        return None

    # === Knowledge Vault ===

    def consolidate_to_vault(self) -> int:
        """
        Consolidate important knowledge to vault.

        Moves high-value procedural knowledge and
        frequent patterns to long-term storage.

        Returns number of consolidated entries.
        """
        consolidated = 0

        # Consolidate high-success procedures
        for name, entry in self.procedural.procedures.items():
            if entry.metadata.get("success_rate", 0) > 0.8:
                vault_entry = MemoryEntry(
                    id=f"vault_{entry.id}",
                    type=MemoryType.KNOWLEDGE_VAULT,
                    content=f"SKILL: {name}\n{entry.content}",
                    metadata={
                        **entry.metadata,
                        "consolidated_at": datetime.now().isoformat(),
                    },
                    importance=1.0,
                )

                if not any(v.id == vault_entry.id for v in self.knowledge_vault):
                    self.knowledge_vault.append(vault_entry)
                    consolidated += 1

        # Consolidate high-confidence facts
        for topic, entry in self.semantic.facts.items():
            if entry.metadata.get("confidence", 0) > 0.9:
                vault_entry = MemoryEntry(
                    id=f"vault_fact_{entry.id}",
                    type=MemoryType.KNOWLEDGE_VAULT,
                    content=f"FACT [{topic}]: {entry.content}",
                    metadata={
                        **entry.metadata,
                        "consolidated_at": datetime.now().isoformat(),
                    },
                    importance=1.0,
                )

                if not any(v.id == vault_entry.id for v in self.knowledge_vault):
                    self.knowledge_vault.append(vault_entry)
                    consolidated += 1

        self._stats["consolidations"] += 1
        return consolidated

    def query_vault(self, query: str, top_k: int = 5) -> List[dict]:
        """Query the knowledge vault."""
        query_words = set(query.lower().split())
        results = []

        for entry in self.knowledge_vault:
            entry_words = set(entry.content.lower().split())
            overlap = len(query_words & entry_words)
            if overlap > 0:
                results.append((overlap, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        return [e.to_dict() for _, e in results[:top_k]]

    # === Context Generation ===

    def get_context_for_task(self, task_description: str) -> dict:
        """Generate comprehensive context for a task."""
        return {
            "identity": self.get_identity(),
            "relevant_experiences": self.recall_experiences(task_description, top_k=3),
            "relevant_knowledge": self.search_knowledge(task_description, top_k=3),
            "relevant_procedures": self.find_procedures(task_description, top_k=3),
            "vault_knowledge": self.query_vault(task_description, top_k=2),
        }

    def get_learning_context(self) -> dict:
        """Get context focused on learning from past mistakes."""
        return {
            "recent_failures": self.recall_failures(top_k=5),
            "recent_successes": self.recall_successes(top_k=3),
            "mastered_skills": [
                skill
                for skill, entry in self.procedural.procedures.items()
                if entry.metadata.get("success_rate", 0) > 0.8
            ],
            "skills_to_improve": [
                skill
                for skill, entry in self.procedural.procedures.items()
                if 0.3 < entry.metadata.get("success_rate", 0) < 0.7
            ],
        }

    # === Persistence ===

    def export_state(self) -> dict:
        """Export complete memory state for persistence."""
        return {
            "core": self.core,
            "episodic": self.episodic.export(),
            "semantic": self.semantic.export(),
            "procedural": self.procedural.export(),
            "knowledge_vault": [e.to_dict() for e in self.knowledge_vault],
            "stats": self._stats,
        }

    def import_state(self, state: dict) -> None:
        """Import memory state from export."""
        if "core" in state:
            self.core.update(state["core"])

        if "episodic" in state:
            self.episodic.import_entries(state["episodic"])

        if "semantic" in state:
            for topic, entry_data in state["semantic"].get("facts", {}).items():
                self.semantic.store_fact(
                    topic=topic,
                    fact=entry_data["content"],
                    confidence=entry_data.get("metadata", {}).get("confidence", 0.8),
                )
            self.semantic.relations = state["semantic"].get("relations", {})

        if "procedural" in state:
            for skill, entry_data in state["procedural"].items():
                self.procedural.store_procedure(
                    skill_name=skill,
                    steps=entry_data.get("metadata", {}).get("steps", []),
                    success_rate=entry_data.get("metadata", {}).get("success_rate", 0),
                )

        if "stats" in state:
            self._stats.update(state["stats"])

    def get_stats(self) -> dict:
        """Get memory system statistics."""
        return {
            **self._stats,
            "episodic_entries": len(self.episodic.entries),
            "semantic_facts": len(self.semantic.facts),
            "procedural_skills": len(self.procedural.procedures),
            "vault_entries": len(self.knowledge_vault),
            "cache_entries": len(self.resource_cache),
        }

    def clear_all(self) -> None:
        """Clear all memories (use with caution)."""
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.resource_cache = {}
        self.knowledge_vault = []
        self._stats = {
            "total_experiences": 0,
            "total_facts": 0,
            "total_procedures": 0,
            "consolidations": 0,
        }


__all__ = ["MemorySystem"]
