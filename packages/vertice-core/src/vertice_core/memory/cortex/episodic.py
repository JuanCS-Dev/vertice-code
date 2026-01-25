"""
Episodic Memory - Session transcripts and history.

Permanent storage for agent interactions, decisions, and outcomes.
Default backend: AlloyDB (source of truth), with local failover to SQLite when no DSN is configured.
"""

from __future__ import annotations

import dataclasses
import asyncio
import concurrent.futures
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from .timing import timing_decorator
from .connection_pool import ConnectionPool
from ..alloydb_connector import AlloyDBConfig, AlloyDBConnector

from sqlalchemy import text


_ASYNC_BRIDGE_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=1)


@dataclasses.dataclass(frozen=True, slots=True)
class EpisodicBackendConfig:
    """
    Backend selection for EpisodicMemory.

    Policy:
    - Default is "alloydb" to make AlloyDB the system of record.
    - If `backend="alloydb"` but `alloydb_dsn` is missing, the implementation fails over to SQLite
      (local/dev without DSN).
    """

    backend: Literal["sqlite", "alloydb"] = "alloydb"
    alloydb_dsn: Optional[str] = None
    alloydb_pool_size: int = 5


class EpisodicMemory:
    """
    Session transcripts and history - permanent storage.

    Records agent interactions, decisions, and outcomes
    for later retrieval and learning.
    """

    def __init__(
        self,
        db_path: Path,
        pool: ConnectionPool,
        config: Optional[EpisodicBackendConfig] = None,
        alloydb: Optional[AlloyDBConnector] = None,
    ) -> None:
        self.db_path = db_path
        self.pool = pool
        self._config = config or EpisodicBackendConfig()
        self._alloydb = alloydb
        self._backend_effective: Literal["sqlite", "alloydb"] = "sqlite"

        if (
            self._config.backend == "alloydb"
            and not self._config.alloydb_dsn
            and self._alloydb is None
        ):
            # Local/dev failover (no DSN configured).
            self._backend_effective = "sqlite"
            self._init_sqlite_db()
            return

        if self._config.backend == "alloydb":
            self._backend_effective = "alloydb"
            if self._alloydb is None:
                if not self._config.alloydb_dsn:
                    raise ValueError(
                        "EpisodicBackendConfig.alloydb_dsn is required for alloydb backend."
                    )
                self._alloydb = AlloyDBConnector(
                    AlloyDBConfig(
                        dsn=self._config.alloydb_dsn, pool_size=self._config.alloydb_pool_size
                    )
                )
            self._run_async_blocking(self._init_alloydb())
        else:
            self._backend_effective = "sqlite"
            self._init_sqlite_db()

    def _init_sqlite_db(self) -> None:
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
            conn.commit()

    async def _init_alloydb(self) -> None:
        assert self._alloydb is not None
        await self._alloydb.start()

        create_table = text(
            """
            CREATE TABLE IF NOT EXISTS episodes (
              id UUID PRIMARY KEY,
              session_id TEXT NOT NULL,
              agent_id TEXT NULL,
              event_type TEXT NOT NULL,
              content TEXT NOT NULL,
              metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        create_idx_session = text(
            "CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id)"
        )
        create_idx_agent = text(
            "CREATE INDEX IF NOT EXISTS idx_episodes_agent ON episodes(agent_id)"
        )
        create_idx_created_at = text(
            "CREATE INDEX IF NOT EXISTS idx_episodes_created_at ON episodes(created_at DESC)"
        )

        async with self._alloydb.engine.begin() as conn:
            await conn.execute(create_table)
            await conn.execute(create_idx_session)
            await conn.execute(create_idx_agent)
            await conn.execute(create_idx_created_at)

    @staticmethod
    def _run_async_blocking(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        return _ASYNC_BRIDGE_POOL.submit(lambda: asyncio.run(coro)).result()

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

        if self._backend_effective == "alloydb":
            self._run_async_blocking(
                self._exec_alloydb(
                    text(
                        """
                        INSERT INTO episodes (id, session_id, agent_id, event_type, content, metadata, created_at)
                        VALUES (:id::uuid, :session_id, :agent_id, :event_type, :content, :metadata::jsonb, :created_at)
                        """
                    ),
                    episode_id=episode_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    event_type=event_type,
                    content=content,
                    metadata=metadata or {},
                )
            )
            return episode_id

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
            conn.commit()

        return episode_id

    async def _exec_alloydb(self, stmt, **params: Any) -> Any:
        assert self._alloydb is not None
        await self._alloydb.start()
        if "metadata" in params and not isinstance(params["metadata"], str):
            params["metadata"] = json.dumps(params["metadata"])
        if "created_at" not in params:
            params["created_at"] = datetime.now()
        async with self._alloydb.engine.begin() as conn:
            return await conn.execute(stmt, params)

    async def _fetch_alloydb(self, stmt, **params: Any) -> List[Dict[str, Any]]:
        assert self._alloydb is not None
        await self._alloydb.start()
        async with self._alloydb.connect() as conn:
            res = await conn.execute(stmt, params)
            return [dict(row._mapping) for row in res.fetchall()]

    def get_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all episodes from a session."""
        if self._backend_effective == "alloydb":
            stmt = text(
                """
                SELECT id::text AS id, session_id, agent_id, event_type, content, metadata::text AS metadata,
                       created_at::text AS timestamp
                FROM episodes
                WHERE session_id = :session_id
                ORDER BY created_at
                """
            )
            return self._run_async_blocking(self._fetch_alloydb(stmt, session_id=session_id))  # type: ignore[return-value]

        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent episodes."""
        if self._backend_effective == "alloydb":
            stmt = text(
                """
                SELECT id::text AS id, session_id, agent_id, event_type, content, metadata::text AS metadata,
                       created_at::text AS timestamp
                FROM episodes
                ORDER BY created_at DESC
                LIMIT :limit
                """
            )
            return self._run_async_blocking(self._fetch_alloydb(stmt, limit=limit))  # type: ignore[return-value]

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
        if self._backend_effective == "alloydb":
            conditions = []
            params: Dict[str, Any] = {"limit": limit}

            if query:
                conditions.append("content ILIKE :query")
                params["query"] = f"%{query}%"
            if agent_id:
                conditions.append("agent_id = :agent_id")
                params["agent_id"] = agent_id
            if event_type:
                conditions.append("event_type = :event_type")
                params["event_type"] = event_type

            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            stmt = text(
                f"""
                SELECT id::text AS id, session_id, agent_id, event_type, content, metadata::text AS metadata,
                       created_at::text AS timestamp
                FROM episodes
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            )
            return await self._fetch_alloydb(stmt, **params)

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
        if self._config.backend == "alloydb":
            stmt = text("DELETE FROM episodes WHERE session_id = :session_id")
            res = self._run_async_blocking(self._exec_alloydb(stmt, session_id=session_id))
            return int(getattr(res, "rowcount", 0) or 0)

        with self.pool.get_conn(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM episodes WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
            return cursor.rowcount

    def count(self) -> int:
        """Get total episode count."""
        if self._config.backend == "alloydb":
            stmt = text("SELECT COUNT(*) AS count FROM episodes")
            rows = self._run_async_blocking(self._fetch_alloydb(stmt))  # type: ignore[arg-type]
            if not rows:
                return 0
            return int(rows[0]["count"])

        with self.pool.get_conn(self.db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
            return result[0] if result else 0
