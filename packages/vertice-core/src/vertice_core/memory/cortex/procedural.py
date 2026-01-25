"""
Procedural Memory - Workflows and Learned Patterns

Based on MIRIX architecture (arXiv:2507.07957).
Stores structured workflows, guides, and scripts that agents
learn and reuse across tasks.

Reference: https://arxiv.org/abs/2507.07957
"""

from __future__ import annotations

import json
import sqlite3
import asyncio
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from .timing import timing_decorator
from .connection_pool import ConnectionPool

logger = logging.getLogger(__name__)


class ProcedureType(str, Enum):
    """Types of procedural entries (MIRIX spec)."""

    WORKFLOW = "workflow"
    GUIDE = "guide"
    SCRIPT = "script"


@dataclass
class Procedure:
    """
    A procedural memory entry.

    Attributes:
        id: Unique identifier.
        entry_type: workflow, guide, or script.
        description: Goal or function of this procedure.
        steps: List of instructions (JSON-serializable).
        agent_id: Agent that created/learned this procedure.
        success_count: Times this procedure succeeded.
        failure_count: Times this procedure failed.
        metadata: Additional context.
        created_at: Creation timestamp.
        last_used: Last usage timestamp.
    """

    id: str
    entry_type: ProcedureType
    description: str
    steps: List[Dict[str, Any]]
    agent_id: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this procedure."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # Unknown, neutral
        return self.success_count / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "entry_type": self.entry_type.value,
            "description": self.description,
            "steps": self.steps,
            "agent_id": self.agent_id,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }


class ProceduralMemory:
    """
    Procedural Memory System.

    Stores learned workflows, guides, and scripts that agents
    can retrieve and execute. Tracks success/failure for
    reinforcement learning of effective patterns.

    Based on MIRIX (arXiv:2507.07957) procedural memory component.
    """

    def __init__(self, db_path: Path, pool: ConnectionPool):
        """
        Initialize procedural memory.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.pool = pool
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self.pool.get_conn(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    entry_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    agent_id TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT,
                    last_used TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proc_type ON procedures(entry_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proc_agent ON procedures(agent_id)")

    def store(
        self,
        description: str,
        steps: List[Dict[str, Any]],
        entry_type: ProcedureType = ProcedureType.WORKFLOW,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a new procedure.

        Args:
            description: Goal or function of this procedure.
            steps: List of instruction steps.
            entry_type: Type of procedure (workflow, guide, script).
            agent_id: Agent that created this procedure.
            metadata: Additional context.

        Returns:
            ID of the stored procedure.
        """
        procedure_id = str(uuid.uuid4())

        with self.pool.get_conn(self.db_path) as conn:
            conn.execute(
                """INSERT INTO procedures
                   (id, entry_type, description, steps, agent_id, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    procedure_id,
                    entry_type.value,
                    description,
                    json.dumps(steps),
                    agent_id,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                ),
            )

        logger.debug(f"Stored procedure {procedure_id}: {description[:50]}...")
        return procedure_id

    def get(self, procedure_id: str) -> Optional[Procedure]:
        """
        Get a procedure by ID.

        Args:
            procedure_id: ID of the procedure.

        Returns:
            Procedure if found, None otherwise.
        """
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM procedures WHERE id = ?", (procedure_id,)).fetchone()

            if row:
                return self._row_to_procedure(row)
            return None

    @timing_decorator
    async def search(
        self,
        query: str,
        entry_type: Optional[ProcedureType] = None,
        agent_id: Optional[str] = None,
        min_success_rate: float = 0.0,
        limit: int = 10,
    ) -> List[Procedure]:
        """
        Search procedures by description.

        Args:
            query: Search query for description.
            entry_type: Filter by type.
            agent_id: Filter by agent.
            min_success_rate: Minimum success rate threshold.
            limit: Maximum results.

        Returns:
            List of matching procedures.
        """
        conditions = ["description LIKE ?"]
        params: List[Any] = [f"%{query}%"]

        if entry_type:
            conditions.append("entry_type = ?")
            params.append(entry_type.value)

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        where_clause = " AND ".join(conditions)

        loop = asyncio.get_event_loop()

        def db_read():
            with self.pool.get_conn(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"""SELECT * FROM procedures
                        WHERE {where_clause}
                        ORDER BY (success_count * 1.0 /
                                 NULLIF(success_count + failure_count, 0)) DESC,
                                 created_at DESC
                        LIMIT ?""",
                    (*params, limit),
                ).fetchall()

                procedures = [self._row_to_procedure(row) for row in rows]
                return [p for p in procedures if p.success_rate >= min_success_rate]

        return await loop.run_in_executor(None, db_read)

    def record_outcome(
        self,
        procedure_id: str,
        success: bool,
    ) -> None:
        """
        Record the outcome of using a procedure.

        Args:
            procedure_id: ID of the procedure used.
            success: Whether the procedure succeeded.
        """
        column = "success_count" if success else "failure_count"

        with self.pool.get_conn(self.db_path) as conn:
            conn.execute(
                f"""UPDATE procedures
                    SET {column} = {column} + 1,
                        last_used = ?
                    WHERE id = ?""",
                (datetime.now().isoformat(), procedure_id),
            )

        logger.debug(f"Recorded {'success' if success else 'failure'} for {procedure_id}")

    async def get_best_for_task(
        self,
        task_description: str,
        entry_type: Optional[ProcedureType] = None,
    ) -> Optional[Procedure]:
        """
        Get the best procedure for a given task.

        Uses keyword matching and success rate to find optimal procedure.

        Args:
            task_description: Description of the task.
            entry_type: Optional type filter.

        Returns:
            Best matching procedure or None.
        """
        # Extract key terms for matching
        terms = task_description.lower().split()

        # Search with each term
        all_matches: Dict[str, Procedure] = {}
        for term in terms[:5]:  # Limit to first 5 terms
            if len(term) > 3:  # Skip short words
                matches = await self.search(term, entry_type=entry_type, limit=5)
                for proc in matches:
                    if proc.id not in all_matches:
                        all_matches[proc.id] = proc

        if not all_matches:
            return None

        # Return highest success rate
        return max(all_matches.values(), key=lambda p: p.success_rate)

    def _row_to_procedure(self, row: sqlite3.Row) -> Procedure:
        """Convert database row to Procedure object."""
        return Procedure(
            id=row["id"],
            entry_type=ProcedureType(row["entry_type"]),
            description=row["description"],
            steps=json.loads(row["steps"]),
            agent_id=row["agent_id"],
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            last_used=row["last_used"],
        )
