"""
Episodic Memory - Session transcripts and history.

Permanent storage for agent interactions, decisions, and outcomes.
Uses SQLite with indexes for efficient retrieval.
"""

from __future__ import annotations

import json
import asyncio
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from .timing import timing_decorator
from .connection_pool import ConnectionPool


class EpisodicMemory:
    """
    Session transcripts and history - permanent storage.

    Records agent interactions, decisions, and outcomes
    for later retrieval and learning.
    """

    def __init__(self, db_path: Path, pool: ConnectionPool) -> None:
        self.db_path = db_path
        self.pool = pool
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with self.pool.get_conn(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    agent_id TEXT,
                    event_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON episodes(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON episodes(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON episodes(timestamp)")

    def record(
        self,
        event_type: str,
        content: str,
        session_id: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record an episode."""
        episode_id = str(uuid.uuid4())

        with self.pool.get_conn(self.db_path) as conn:
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
                ),
            )

        return episode_id

    def get_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all episodes from a session."""
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent episodes."""
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()

            return [dict(row) for row in rows]

    @timing_decorator
    async def search(
        self,
        query: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search episodes with filters."""
        conditions = []
        params: List[Any] = []

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

        loop = asyncio.get_event_loop()

        def db_read():
            with self.pool.get_conn(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT * FROM episodes WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                    (*params, limit),
                ).fetchall()
                return [dict(row) for row in rows]

        return await loop.run_in_executor(None, db_read)

    def delete_session(self, session_id: str) -> int:
        """Delete all episodes from a session. Returns count deleted."""
        with self.pool.get_conn(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM episodes WHERE session_id = ?",
                (session_id,),
            )
            return cursor.rowcount

    def count(self) -> int:
        """Get total episode count."""
        with self.pool.get_conn(self.db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
            return result[0] if result else 0
