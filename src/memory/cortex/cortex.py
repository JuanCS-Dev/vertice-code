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

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import CoreMemory
from .economy import ContributionLedger
from .episodic import EpisodicMemory
from .procedural import ProceduralMemory, Procedure, ProcedureType
from .resource import ResourceMemory
from .retrieval import ActiveRetrieval
from .connection_pool import get_connection_pool
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
        self._pool = get_connection_pool()

        # Lazy-loaded properties
        self._working: Optional[WorkingMemory] = None
        self._core: Optional[CoreMemory] = None
        self._episodic: Optional[EpisodicMemory] = None
        self._semantic: Optional[SemanticMemory] = None
        self._procedural: Optional[ProceduralMemory] = None
        self._resource: Optional[ResourceMemory] = None
        self._vault: Optional[KnowledgeVault] = None
        self._economy: Optional[ContributionLedger] = None
        self._retrieval: Optional[ActiveRetrieval] = None

        logger.info(f"Memory Cortex (MIRIX 6-type) lazy-initialized at {self.base_path}")

    @property
    def working(self) -> WorkingMemory:
        if self._working is None:
            self._working = WorkingMemory()
        return self._working

    @property
    def core(self) -> CoreMemory:
        if self._core is None:
            self._core = CoreMemory(self.base_path / "core.db", self.agent_id)
        return self._core

    @property
    def episodic(self) -> EpisodicMemory:
        if self._episodic is None:
            self._episodic = EpisodicMemory(self.base_path / "episodic.db", self._pool)
        return self._episodic

    @property
    def semantic(self) -> SemanticMemory:
        if self._semantic is None:
            self._semantic = SemanticMemory(self.base_path / "semantic")
        return self._semantic

    @property
    def procedural(self) -> ProceduralMemory:
        if self._procedural is None:
            self._procedural = ProceduralMemory(self.base_path / "procedural.db", self._pool)
        return self._procedural

    @property
    def resource(self) -> ResourceMemory:
        if self._resource is None:
            self._resource = ResourceMemory(self.base_path / "resource.db", self._pool)
        return self._resource

    @property
    def vault(self) -> KnowledgeVault:
        if self._vault is None:
            self._vault = KnowledgeVault(self.base_path / "vault.db")
        return self._vault

    @property
    def economy(self) -> ContributionLedger:
        if self._economy is None:
            self._economy = ContributionLedger(self.base_path / "ledger.db")
        return self._economy

    @property
    def retrieval(self) -> ActiveRetrieval:
        if self._retrieval is None:
            self._retrieval = ActiveRetrieval(
                core=self.core,
                episodic=self.episodic,
                semantic=self.semantic,
                procedural=self.procedural,
                resource=self.resource,
            )
        return self._retrieval

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
        return self.economy.record_contribution(
            agent_id, contribution_type, value, task_id, metadata
        )

    def get_agent_reputation(self, agent_id: str) -> Dict[str, Any]:
        """Get an agent's reputation score."""
        return self.economy.get_agent_reputation(agent_id)

    # === Active Retrieval delegation ===

    async def active_retrieve(
        self,
        query: str,
        limit_per_type: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """MIRIX Active Retrieval - Automatic context injection."""
        return await self.retrieval.retrieve(query, limit_per_type)

    async def to_context_prompt(self, query: str) -> str:
        """Generate context string for LLM prompt injection."""
        return await self.retrieval.to_context_prompt(query)

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

    async def recall(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Recall memories matching query."""
        results: List[Dict[str, Any]] = []
        memory_types = memory_types or ["episodic", "semantic"]

        tasks = []
        sources = []

        if "episodic" in memory_types:
            tasks.append(self.episodic.search(query=query, limit=limit))
            sources.append("episodic")

        if "semantic" in memory_types:
            tasks.append(self.semantic.search(
                query=query,
                embedding=kwargs.get("embedding"),
                limit=limit,
            ))
            sources.append("semantic")

        search_results = await asyncio.gather(*tasks)

        for source, search_result in zip(sources, search_results):
            for r in search_result:
                r["source"] = source
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

    async def get_best_procedure(self, task: str) -> Optional[Procedure]:
        """Get the best procedure for a task."""
        return await self.procedural.get_best_for_task(task)

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
