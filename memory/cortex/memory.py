"""
Memory Cortex Implementation - MIRIX 6-Type Architecture

The shared brain for all Vertice agents. Implements the MIRIX
memory architecture (arXiv:2507.07957) with 6 distinct memory types:

1. Core Memory - Agent identity and user information
2. Episodic Memory - Time-stamped events and interactions
3. Semantic Memory - Knowledge graph and facts
4. Procedural Memory - Learned workflows and patterns
5. Resource Memory - External documents and assets
6. Knowledge Vault - Secure sensitive data storage

Also provides:
- Working Memory (ephemeral task context)
- Active Retrieval (topic-based context injection)
- Contribution tracking for economy system

Reference: https://arxiv.org/abs/2507.07957
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

# Import MIRIX memory components
from .core import CoreMemory
from .procedural import ProceduralMemory, ProcedureType, Procedure
from .resource import ResourceMemory
from .vault import KnowledgeVault

logger = logging.getLogger(__name__)

# Try to import LanceDB (optional for now)
try:
    import lancedb
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logger.warning("LanceDB not installed. Vector search disabled. Install with: pip install lancedb")


@dataclass
class Memory:
    """A single memory entry."""
    id: str
    content: str
    memory_type: str  # working, episodic, semantic, procedural, meta, social
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    embedding: Optional[List[float]] = None


@dataclass
class Contribution:
    """Track agent contributions for economy system."""
    id: str
    agent_id: str
    contribution_type: str  # code_commit, code_review, task_completion, etc.
    value: float
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class WorkingMemory:
    """
    Active task context - ephemeral, session-scoped.

    Stores current task state, active context, and
    intermediate results during task execution.
    """

    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._active_task: Optional[str] = None
        self._stack: List[Dict] = []

    def set_context(self, key: str, value: Any):
        """Set a context value."""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self._context.get(key, default)

    def set_active_task(self, task_id: str, task_data: Dict):
        """Set the currently active task."""
        self._active_task = task_id
        self._context["current_task"] = task_data

    def push(self, frame: Dict):
        """Push a context frame onto the stack."""
        self._stack.append(frame)

    def pop(self) -> Optional[Dict]:
        """Pop a context frame from the stack."""
        return self._stack.pop() if self._stack else None

    def clear(self):
        """Clear working memory."""
        self._context.clear()
        self._active_task = None
        self._stack.clear()

    def to_dict(self) -> Dict:
        """Export working memory state."""
        return {
            "context": self._context,
            "active_task": self._active_task,
            "stack_depth": len(self._stack),
        }


class EpisodicMemory:
    """
    Session transcripts and history - permanent storage.

    Records agent interactions, decisions, and outcomes
    for later retrieval and learning.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    agent_id TEXT,
                    event_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON episodes(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON episodes(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON episodes(timestamp)")

    def record(
        self,
        event_type: str,
        content: str,
        session_id: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Record an episode."""
        import uuid
        episode_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO episodes
                   (id, session_id, agent_id, event_type, content, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    episode_id,
                    session_id,
                    agent_id,
                    event_type,
                    content,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                )
            )

        return episode_id

    def get_session(self, session_id: str) -> List[Dict]:
        """Get all episodes from a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ).fetchall()

            return [dict(row) for row in rows]

    def search(
        self,
        query: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Search episodes with filters."""
        conditions = []
        params = []

        if query:
            conditions.append("content LIKE ?")
            params.append(f"%{query}%")
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM episodes WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                (*params, limit)
            ).fetchall()

            return [dict(row) for row in rows]


class SemanticMemory:
    """
    Knowledge graph and facts - vector-based retrieval.

    Uses LanceDB for embedding storage and similarity search.
    Falls back to SQLite FTS if LanceDB not available.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lance_db = None
        self._table = None

        if LANCEDB_AVAILABLE:
            self._init_lancedb()
        else:
            self._init_sqlite_fallback()

    def _init_lancedb(self):
        """Initialize LanceDB for vector storage."""
        try:
            self._lance_db = lancedb.connect(str(self.db_path))
            logger.info(f"LanceDB initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            self._init_sqlite_fallback()

    def _init_sqlite_fallback(self):
        """Initialize SQLite FTS as fallback."""
        fallback_path = self.db_path.parent / "semantic_fallback.db"
        with sqlite3.connect(fallback_path) as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS semantic_fts
                USING fts5(id, content, category, metadata)
            """)
        self._fallback_db = fallback_path
        logger.info("Using SQLite FTS fallback for semantic memory")

    def store(
        self,
        content: str,
        category: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store a fact or knowledge entry."""
        import uuid
        entry_id = str(uuid.uuid4())

        if self._lance_db and embedding:
            # Store in LanceDB with embedding
            data = [{
                "id": entry_id,
                "content": content,
                "category": category,
                "metadata": json.dumps(metadata or {}),
                "vector": embedding,
            }]

            table_name = "knowledge"
            if table_name in self._lance_db.table_names():
                table = self._lance_db.open_table(table_name)
                table.add(data)
            else:
                self._lance_db.create_table(table_name, data)
        else:
            # Fallback to SQLite FTS
            with sqlite3.connect(self._fallback_db) as conn:
                conn.execute(
                    "INSERT INTO semantic_fts VALUES (?, ?, ?, ?)",
                    (entry_id, content, category, json.dumps(metadata or {}))
                )

        return entry_id

    def search(
        self,
        query: str,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search semantic memory."""
        if self._lance_db and embedding:
            # Vector similarity search
            try:
                table = self._lance_db.open_table("knowledge")
                results = table.search(embedding).limit(limit).to_list()
                return [
                    {
                        "id": r["id"],
                        "content": r["content"],
                        "category": r["category"],
                        "metadata": json.loads(r["metadata"]),
                        "score": r.get("_distance", 0),
                    }
                    for r in results
                ]
            except Exception as e:
                logger.warning(f"LanceDB search failed: {e}")

        # Fallback to FTS
        with sqlite3.connect(self._fallback_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM semantic_fts WHERE content MATCH ? LIMIT ?",
                (query, limit)
            ).fetchall()

            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "category": row["category"],
                    "metadata": json.loads(row["metadata"]),
                }
                for row in rows
            ]


class MemoryCortex:
    """
    Unified Memory System for Vertice Agency.

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

    All agents share this brain for coordination.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        agent_id: str = "default",
    ):
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

        # Initialize ledger for economy system
        self._init_ledger()

        logger.info(f"Memory Cortex (MIRIX 6-type) initialized at {self.base_path}")

    def _init_ledger(self):
        """Initialize contribution ledger."""
        with sqlite3.connect(self.base_path / "ledger.db") as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contributions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    contribution_type TEXT,
                    value REAL,
                    task_id TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reputation (
                    agent_id TEXT PRIMARY KEY,
                    total_contributions REAL DEFAULT 0,
                    successful_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.5,
                    last_updated TEXT
                )
            """)

    def record_contribution(
        self,
        agent_id: str,
        contribution_type: str,
        value: float,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Record an agent contribution."""
        import uuid

        with sqlite3.connect(self.base_path / "ledger.db") as conn:
            # Record contribution
            conn.execute(
                """INSERT INTO contributions
                   (id, agent_id, contribution_type, value, task_id, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    agent_id,
                    contribution_type,
                    value,
                    task_id,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                )
            )

            # Update reputation
            conn.execute(
                """INSERT INTO reputation (agent_id, total_contributions, last_updated)
                   VALUES (?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                   total_contributions = total_contributions + ?,
                   last_updated = ?""",
                (
                    agent_id,
                    value,
                    datetime.now().isoformat(),
                    value,
                    datetime.now().isoformat(),
                )
            )

    def get_agent_reputation(self, agent_id: str) -> Dict:
        """Get an agent's reputation score."""
        with sqlite3.connect(self.base_path / "ledger.db") as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM reputation WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()

            if row:
                return dict(row)
            return {
                "agent_id": agent_id,
                "total_contributions": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "quality_score": 0.5,
            }

    def remember(
        self,
        content: str,
        memory_type: str = "episodic",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs,
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
        **kwargs,
    ) -> List[Dict]:
        """Recall memories matching query."""
        results = []
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

    def get_status(self) -> Dict:
        """Get memory cortex status."""
        return {
            "base_path": str(self.base_path),
            "agent_id": self.agent_id,
            "architecture": "MIRIX 6-type",
            "working_memory": self.working.to_dict(),
            "core_memory": self.core.check_capacity(),
            "lancedb_available": LANCEDB_AVAILABLE,
            "databases": {
                "core": str(self.base_path / "core.db"),
                "episodic": str(self.base_path / "episodic.db"),
                "procedural": str(self.base_path / "procedural.db"),
                "resource": str(self.base_path / "resource.db"),
                "vault": str(self.base_path / "vault.db"),
                "ledger": str(self.base_path / "ledger.db"),
            },
        }

    def active_retrieve(
        self,
        query: str,
        limit_per_type: int = 5,
    ) -> Dict[str, List[Dict]]:
        """
        MIRIX Active Retrieval - Automatic context injection.

        Retrieves relevant entries from ALL memory types based on
        the current query/topic. Results are tagged by source for
        injection into LLM system prompt.

        Args:
            query: Current topic or user input.
            limit_per_type: Max entries per memory type.

        Returns:
            Dictionary with tagged results from each memory type.
        """
        results: Dict[str, List[Dict]] = {}

        # Core memory (always include)
        results["core"] = [self.core.get_persona()]

        # Episodic memory
        episodic_results = self.episodic.search(query=query, limit=limit_per_type)
        if episodic_results:
            results["episodic"] = episodic_results

        # Semantic memory
        semantic_results = self.semantic.search(query=query, limit=limit_per_type)
        if semantic_results:
            results["semantic"] = semantic_results

        # Procedural memory
        proc_results = self.procedural.search(query=query, limit=limit_per_type)
        if proc_results:
            results["procedural"] = [p.to_dict() for p in proc_results]

        # Resource memory
        resource_results = self.resource.search(query=query, limit=limit_per_type)
        if resource_results:
            results["resource"] = [r.to_dict() for r in resource_results]

        return results

    def to_context_prompt(self, query: str) -> str:
        """
        Generate context string for LLM prompt injection.

        Uses Active Retrieval to gather relevant context and
        formats it for system prompt inclusion.

        Args:
            query: Current topic or user input.

        Returns:
            Formatted context string with XML tags.
        """
        retrieved = self.active_retrieve(query)
        parts = ["<memory_context>"]

        # Core memory
        if "core" in retrieved:
            parts.append(self.core.to_context_string())

        # Episodic memories
        if "episodic" in retrieved and retrieved["episodic"]:
            parts.append("<episodic_memory>")
            for ep in retrieved["episodic"][:3]:
                parts.append(f"  [{ep.get('timestamp', 'unknown')}] {ep.get('content', '')[:200]}")
            parts.append("</episodic_memory>")

        # Procedural memories
        if "procedural" in retrieved and retrieved["procedural"]:
            parts.append("<procedural_memory>")
            for proc in retrieved["procedural"][:2]:
                parts.append(f"  Workflow: {proc.get('description', '')}")
            parts.append("</procedural_memory>")

        # Resource memories
        if "resource" in retrieved and retrieved["resource"]:
            parts.append("<resource_memory>")
            for res in retrieved["resource"][:3]:
                parts.append(f"  [{res.get('resource_type', 'unknown')}] {res.get('title', '')}: {res.get('summary', '')[:100]}")
            parts.append("</resource_memory>")

        parts.append("</memory_context>")

        return "\n".join(parts)

    def learn_procedure(
        self,
        description: str,
        steps: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Learn a new procedure from successful task execution.

        Args:
            description: What this procedure accomplishes.
            steps: List of steps that worked.
            agent_id: Agent that learned this.

        Returns:
            ID of the stored procedure.
        """
        return self.procedural.store(
            description=description,
            steps=steps,
            entry_type=ProcedureType.WORKFLOW,
            agent_id=agent_id or self.agent_id,
        )

    def get_best_procedure(self, task: str) -> Optional[Procedure]:
        """
        Get the best procedure for a task.

        Args:
            task: Task description.

        Returns:
            Best matching procedure or None.
        """
        return self.procedural.get_best_for_task(task)


# Global cortex instance
_cortex: Optional[MemoryCortex] = None


def get_cortex() -> MemoryCortex:
    """Get the global Memory Cortex instance."""
    global _cortex
    if _cortex is None:
        _cortex = MemoryCortex()
    return _cortex
