"""
Semantic Memory - Knowledge graph and facts.

Vector-based retrieval using LanceDB with SQLite FTS fallback.
Stores facts, knowledge, and contextual information.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from .timing import timing_decorator
from async_lru import alru_cache

logger = logging.getLogger(__name__)

# Try to import LanceDB (optional)
try:
    import lancedb

    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logger.debug("LanceDB not installed. Vector search disabled.")


class SemanticMemory:
    """
    Knowledge graph and facts - vector-based retrieval.

    Uses LanceDB for embedding storage and similarity search.
    Falls back to SQLite FTS if LanceDB not available.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lance_db: Any = None
        self._fallback_db: Optional[Path] = None

        if LANCEDB_AVAILABLE:
            self._init_lancedb()
        else:
            self._init_sqlite_fallback()

    def _init_lancedb(self) -> None:
        """Initialize LanceDB for vector storage."""
        try:
            self._lance_db = lancedb.connect(str(self.db_path))
            logger.info(f"LanceDB initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            self._init_sqlite_fallback()

    def _init_sqlite_fallback(self) -> None:
        """Initialize SQLite FTS as fallback."""
        fallback_path = self.db_path.parent / "semantic_fallback.db"
        with sqlite3.connect(fallback_path) as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS semantic_fts
                USING fts5(id, content, category, metadata)
            """
            )
        self._fallback_db = fallback_path
        logger.info("Using SQLite FTS fallback for semantic memory")

    def store(
        self,
        content: str,
        category: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a fact or knowledge entry."""
        entry_id = str(uuid.uuid4())

        if self._lance_db and embedding:
            # Store in LanceDB with embedding
            data = [
                {
                    "id": entry_id,
                    "content": content,
                    "category": category,
                    "metadata": json.dumps(metadata or {}),
                    "vector": embedding,
                }
            ]

            table_name = "knowledge"
            if table_name in self._lance_db.table_names():
                table = self._lance_db.open_table(table_name)
                table.add(data)
            else:
                self._lance_db.create_table(table_name, data)
        elif self._fallback_db:
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
        loop = asyncio.get_event_loop()

        def db_read():
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
            if self._fallback_db:
                with sqlite3.connect(self._fallback_db) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        "SELECT * FROM semantic_fts WHERE content MATCH ? LIMIT ?",
                        (query, limit),
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
        if self._fallback_db:
            with sqlite3.connect(self._fallback_db) as conn:
                result = conn.execute("SELECT COUNT(*) FROM semantic_fts").fetchone()
                return result[0] if result else 0
        return 0

    @property
    def is_vector_enabled(self) -> bool:
        """Check if vector search is available."""
        return self._lance_db is not None
