"""
Memory Cortex - Unified Memory System Facade.

Implements MIRIX 6-type architecture (arXiv:2507.07957):
- Core memory for agent identity
- Episodic memory for session history
- Semantic memory for knowledge retrieval
- Procedural memory for learned workflows
- Resource memory for external documents
- Knowledge vault for sensitive data

Plus:
- Working memory for active task context
- Active Retrieval for context injection
- Contribution tracking for economy system

Reference: https://arxiv.org/abs/2507.07957
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import CoreMemory
from .economy import ContributionLedger
from .episodic import EpisodicMemory
from .procedural import ProceduralMemory, Procedure, ProcedureType
from .resource import ResourceMemory
from .retrieval import ActiveRetrieval
from .semantic import SemanticMemory
from .vault import KnowledgeVault
from .working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryCortex:
    """
    Unified Memory System for Vertice Agency.

    Lightweight facade that composes MIRIX 6-type memory subsystems
    and provides convenience methods for common operations.

    All agents share this brain for coordination.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        agent_id: str = "default",
    ) -> None:
        if base_path is None:
            base_path = Path.home() / ".vertice" / "cortex"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.agent_id = agent_id

        # Initialize MIRIX 6-type memory subsystems
        self.working = WorkingMemory()
        self.core = CoreMemory(self.base_path / "core.db", agent_id)
        self.episodic = EpisodicMemory(self.base_path / "episodic.db")
        self.semantic = SemanticMemory(self.base_path / "semantic")
        self.procedural = ProceduralMemory(self.base_path / "procedural.db")
        self.resource = ResourceMemory(self.base_path / "resource.db")
        self.vault = KnowledgeVault(self.base_path / "vault.db")

        # Composed managers
        self._economy = ContributionLedger(self.base_path / "ledger.db")
        self._retrieval = ActiveRetrieval(
            core=self.core,
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
            resource=self.resource,
        )

        logger.info(f"Memory Cortex (MIRIX 6-type) initialized at {self.base_path}")

    # === Economy delegation ===

    def record_contribution(
        self,
        agent_id: str,
        contribution_type: str,
        value: float,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record an agent contribution."""
        return self._economy.record_contribution(
            agent_id, contribution_type, value, task_id, metadata
        )

    def get_agent_reputation(self, agent_id: str) -> Dict[str, Any]:
        """Get an agent's reputation score."""
        return self._economy.get_agent_reputation(agent_id)

    # === Active Retrieval delegation ===

    def active_retrieve(
        self,
        query: str,
        limit_per_type: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """MIRIX Active Retrieval - Automatic context injection."""
        return self._retrieval.retrieve(query, limit_per_type)

    def to_context_prompt(self, query: str) -> str:
        """Generate context string for LLM prompt injection."""
        return self._retrieval.to_context_prompt(query)

    # === Convenience methods ===

    def remember(
        self,
        content: str,
        memory_type: str = "episodic",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Store a memory (convenience method)."""
        if memory_type == "working":
            self.working.set_context(kwargs.get("key", "memory"), content)
            return "working"
        elif memory_type == "episodic":
            return self.episodic.record(
                event_type=kwargs.get("event_type", "memory"),
                content=content,
                session_id=session_id or "default",
                agent_id=agent_id,
                metadata=kwargs.get("metadata"),
            )
        elif memory_type == "semantic":
            return self.semantic.store(
                content=content,
                category=kwargs.get("category", "general"),
                embedding=kwargs.get("embedding"),
                metadata=kwargs.get("metadata"),
            )
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

    def recall(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Recall memories matching query."""
        results: List[Dict[str, Any]] = []
        memory_types = memory_types or ["episodic", "semantic"]

        if "episodic" in memory_types:
            episodic_results = self.episodic.search(query=query, limit=limit)
            for r in episodic_results:
                r["source"] = "episodic"
                results.append(r)

        if "semantic" in memory_types:
            semantic_results = self.semantic.search(
                query=query,
                embedding=kwargs.get("embedding"),
                limit=limit,
            )
            for r in semantic_results:
                r["source"] = "semantic"
                results.append(r)

        return results[:limit]

    def learn_procedure(
        self,
        description: str,
        steps: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
    ) -> str:
        """Learn a new procedure from successful task execution."""
        return self.procedural.store(
            description=description,
            steps=steps,
            entry_type=ProcedureType.WORKFLOW,
            agent_id=agent_id or self.agent_id,
        )

    def get_best_procedure(self, task: str) -> Optional[Procedure]:
        """Get the best procedure for a task."""
        return self.procedural.get_best_for_task(task)

    def get_status(self) -> Dict[str, Any]:
        """Get memory cortex status."""
        return {
            "base_path": str(self.base_path),
            "agent_id": self.agent_id,
            "architecture": "MIRIX 6-type",
            "working_memory": self.working.to_dict(),
            "core_memory": self.core.check_capacity(),
            "lancedb_available": self.semantic.is_vector_enabled,
            "databases": {
                "core": str(self.base_path / "core.db"),
                "episodic": str(self.base_path / "episodic.db"),
                "procedural": str(self.base_path / "procedural.db"),
                "resource": str(self.base_path / "resource.db"),
                "vault": str(self.base_path / "vault.db"),
                "ledger": str(self.base_path / "ledger.db"),
            },
        }


# Global cortex instance
_cortex: Optional[MemoryCortex] = None


def get_cortex() -> MemoryCortex:
    """Get the global Memory Cortex instance."""
    global _cortex
    if _cortex is None:
        _cortex = MemoryCortex()
    return _cortex
