"""
Semantic Memory - Knowledge graph and facts.

Phase 4 cutover policy:
- Default backend is AlloyDB AI (source of truth).
- Embeddings are generated inside the database via `google_ml_integration` (SQL: `embedding(model, text)`).
- Local/dev without a DSN fails over to SQLite FTS (no external infra).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import dataclasses
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from async_lru import alru_cache
from sqlalchemy import text

from ..alloydb_connector import AlloyDBConfig, AlloyDBConnector
from .timing import timing_decorator

logger = logging.getLogger(__name__)

LANCEDB_AVAILABLE = False

_ASYNC_BRIDGE_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=1)


@dataclasses.dataclass(frozen=True, slots=True)
class SemanticBackendConfig:
    """Backend selection for SemanticMemory."""

    backend: Literal["sqlite", "alloydb"] = "alloydb"
    alloydb_dsn: Optional[str] = None
    alloydb_pool_size: int = 5
    embedding_model: str = "text-embedding-005"
    embedding_dim: int = 768


class SemanticMemory:
    """
    Knowledge graph and facts - vector-based retrieval.

    Production: AlloyDB AI with pgvector + google_ml_integration.
    Local/dev without DSN: SQLite FTS fallback.
    """

    def __init__(
        self,
        db_path: Path,
        *,
        config: Optional[SemanticBackendConfig] = None,
        alloydb: Optional[AlloyDBConnector] = None,
    ) -> None:
        self.db_path = db_path
        self._config = config or SemanticBackendConfig()
        self._alloydb = alloydb
        self._backend_effective: Literal["sqlite", "alloydb"] = "sqlite"
        self._fallback_db: Optional[Path] = None

        if (
            self._config.backend == "alloydb"
            and not self._config.alloydb_dsn
            and self._alloydb is None
        ):
            # Local/dev failover (no DSN configured).
            self._backend_effective = "sqlite"
            self._init_sqlite_fallback()
            return

        if self._config.backend == "alloydb":
            self._backend_effective = "alloydb"
            if self._alloydb is None:
                if not self._config.alloydb_dsn:
                    raise ValueError(
                        "SemanticBackendConfig.alloydb_dsn is required for alloydb backend."
                    )
                self._alloydb = AlloyDBConnector(
                    AlloyDBConfig(
                        dsn=self._config.alloydb_dsn, pool_size=self._config.alloydb_pool_size
                    )
                )
            self._run_async_blocking(self._init_alloydb())
        else:
            self._backend_effective = "sqlite"
            self._init_sqlite_fallback()

    def _init_sqlite_fallback(self) -> None:
        """Initialize SQLite FTS as fallback."""
        if self.db_path.suffix == ".db":
            fallback_path = self.db_path
        else:
            self.db_path.mkdir(parents=True, exist_ok=True)
            fallback_path = self.db_path / "semantic_fallback.db"
        with sqlite3.connect(fallback_path) as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS semantic_fts
                USING fts5(id, content, category, metadata)
            """
            )
        self._fallback_db = fallback_path
        logger.info("Using SQLite FTS fallback for semantic memory")

    async def _init_alloydb(self) -> None:
        assert self._alloydb is not None
        await self._alloydb.start()

        dim = self._config.embedding_dim
        stmts = [
            text("CREATE EXTENSION IF NOT EXISTS vector"),
            text("CREATE EXTENSION IF NOT EXISTS google_ml_integration"),
            text(
                f"""
                CREATE TABLE IF NOT EXISTS semantic_memories (
                  id UUID PRIMARY KEY,
                  category TEXT NOT NULL,
                  content TEXT NOT NULL,
                  metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                  embedding vector({dim}) NOT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            ),
            text(
                "CREATE INDEX IF NOT EXISTS idx_semantic_memories_category ON semantic_memories(category)"
            ),
            text(
                "CREATE INDEX IF NOT EXISTS idx_semantic_memories_created_at "
                "ON semantic_memories(created_at DESC)"
            ),
        ]

        async with self._alloydb.engine.begin() as conn:
            for stmt in stmts:
                await conn.execute(stmt)

    def store(
        self,
        content: str,
        category: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a knowledge entry.

        Note: `embedding` is accepted for backward-compat, but ignored on AlloyDB (computed in SQL).
        """
        entry_id = str(uuid.uuid4())

        if self._backend_effective == "alloydb":
            self._run_async_blocking(
                self._exec_alloydb(
                    text(
                        """
                        INSERT INTO semantic_memories (id, category, content, metadata, embedding, created_at)
                        VALUES (
                          :entry_id::uuid,
                          :category,
                          :content,
                          :metadata::jsonb,
                          embedding(:model, :content),
                          NOW()
                        )
                        ON CONFLICT (id) DO NOTHING
                        """
                    ),
                    entry_id=entry_id,
                    category=category,
                    content=content,
                    metadata=metadata or {},
                    model=self._config.embedding_model,
                )
            )
            return entry_id

        if self._fallback_db:
            # Fallback to SQLite FTS
            with sqlite3.connect(self._fallback_db) as conn:
                conn.execute(
                    "INSERT INTO semantic_fts VALUES (?, ?, ?, ?)",
                    (entry_id, content, category, json.dumps(metadata or {})),
                )

        return entry_id

    @alru_cache(maxsize=128)
    @timing_decorator
    async def search(
        self,
        query: str,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search semantic memory."""
        if self._backend_effective == "alloydb":
            stmt = text(
                """
                SELECT
                  id::text AS id,
                  content,
                  category,
                  metadata::text AS metadata,
                  (embedding <=> embedding(:model, :query)) AS distance
                FROM semantic_memories
                ORDER BY embedding <=> embedding(:model, :query)
                LIMIT :limit
                """
            )
            rows = await self._fetch_alloydb(
                stmt, query=query, limit=limit, model=self._config.embedding_model
            )
            out: List[Dict[str, Any]] = []
            for r in rows:
                md = r.get("metadata")
                out.append(
                    {
                        "id": r.get("id"),
                        "content": r.get("content"),
                        "category": r.get("category"),
                        "metadata": json.loads(md) if isinstance(md, str) and md else {},
                        "score": r.get("distance"),
                    }
                )
            return out

        loop = asyncio.get_event_loop()

        def db_read():
            # Fallback to FTS
            if self._fallback_db:
                with sqlite3.connect(self._fallback_db) as conn:
                    conn.row_factory = sqlite3.Row
                    # Sanitize the query for FTS5
                    escaped = query.replace('"', '""')
                    sanitized_query = f'"{escaped}"'
                    rows = conn.execute(
                        "SELECT * FROM semantic_fts WHERE content MATCH ? LIMIT ?",
                        (sanitized_query, limit),
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
            return []

        return await loop.run_in_executor(None, db_read)

    def get_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get entries by category."""
        if self._backend_effective == "alloydb":
            stmt = text(
                """
                SELECT id::text AS id, content, category, metadata::text AS metadata
                FROM semantic_memories
                WHERE category = :category
                ORDER BY created_at DESC
                LIMIT :limit
                """
            )
            rows = self._run_async_blocking(
                self._fetch_alloydb(stmt, category=category, limit=limit)
            )  # type: ignore[return-value]
            return [
                {
                    "id": r.get("id"),
                    "content": r.get("content"),
                    "category": r.get("category"),
                    "metadata": json.loads(r.get("metadata") or "{}"),
                }
                for r in rows
            ]

        if self._fallback_db:
            with sqlite3.connect(self._fallback_db) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM semantic_fts WHERE category = ? LIMIT ?",
                    (category, limit),
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

        return []

    def count(self) -> int:
        """Get total entry count."""
        if self._backend_effective == "alloydb":
            stmt = text("SELECT COUNT(*) AS c FROM semantic_memories")
            rows = self._run_async_blocking(self._fetch_alloydb(stmt))  # type: ignore[return-value]
            if rows:
                return int(rows[0].get("c") or 0)
            return 0

        if self._fallback_db:
            with sqlite3.connect(self._fallback_db) as conn:
                result = conn.execute("SELECT COUNT(*) FROM semantic_fts").fetchone()
                return result[0] if result else 0
        return 0

    @property
    def is_vector_enabled(self) -> bool:
        """Check if vector search is available."""
        return self._backend_effective == "alloydb"

    @staticmethod
    def _run_async_blocking(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        return _ASYNC_BRIDGE_POOL.submit(lambda: asyncio.run(coro)).result()

    async def _exec_alloydb(self, stmt, **params: Any) -> Any:
        assert self._alloydb is not None
        await self._alloydb.start()
        if "metadata" in params and not isinstance(params["metadata"], str):
            params["metadata"] = json.dumps(params["metadata"])
        async with self._alloydb.engine.begin() as conn:
            return await conn.execute(stmt, params)

    async def _fetch_alloydb(self, stmt, **params: Any) -> List[Dict[str, Any]]:
        assert self._alloydb is not None
        await self._alloydb.start()
        async with self._alloydb.connect() as conn:
            res = await conn.execute(stmt, params)
            return [dict(row._mapping) for row in res.fetchall()]
