"""
Resource Memory - External Documents and Assets

Based on MIRIX architecture (arXiv:2507.07957).
Maintains references to external documents, images, audio,
and other resources for contextual continuity.

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


class ResourceType(str, Enum):
    """Types of resources (MIRIX spec)."""
    DOC = "doc"
    MARKDOWN = "markdown"
    PDF_TEXT = "pdf_text"
    IMAGE = "image"
    VOICE_TRANSCRIPT = "voice_transcript"
    CODE = "code"
    CONFIG = "config"
    API_RESPONSE = "api_response"


@dataclass
class Resource:
    """
    A resource memory entry.

    Attributes:
        id: Unique identifier.
        title: Resource name.
        summary: Brief overview and context.
        resource_type: Type of resource.
        content: Full or excerpted material.
        path: Optional file path or URL.
        agent_id: Agent that added this resource.
        access_count: Number of times accessed.
        metadata: Additional context.
        created_at: Creation timestamp.
        last_accessed: Last access timestamp.
    """
    id: str
    title: str
    summary: str
    resource_type: ResourceType
    content: Optional[str] = None
    path: Optional[str] = None
    agent_id: Optional[str] = None
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "resource_type": self.resource_type.value,
            "content": self.content,
            "path": self.path,
            "agent_id": self.agent_id,
            "access_count": self.access_count,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
        }


class ResourceMemory:
    """
    Resource Memory System.

    Maintains references to external documents, code files,
    configurations, and other assets. Enables agents to
    recall relevant resources for current tasks.

    Based on MIRIX (arXiv:2507.07957) resource memory component.
    """

    def __init__(self, db_path: Path, pool: ConnectionPool):
        """
        Initialize resource memory.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.pool = pool
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self.pool.get_conn(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    content TEXT,
                    path TEXT,
                    agent_id TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT,
                    last_accessed TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_res_type ON resources(resource_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_res_title ON resources(title)"
            )
            # Full-text search on summary and content
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS resources_fts
                USING fts5(id, title, summary, content)
            """)

    def store(
        self,
        title: str,
        summary: str,
        resource_type: ResourceType,
        content: Optional[str] = None,
        path: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a new resource.

        Args:
            title: Resource name.
            summary: Brief overview.
            resource_type: Type of resource.
            content: Full or excerpted content.
            path: File path or URL.
            agent_id: Agent that added this.
            metadata: Additional context.

        Returns:
            ID of the stored resource.
        """
        resource_id = str(uuid.uuid4())

        with self.pool.get_conn(self.db_path) as conn:
            conn.execute(
                """INSERT INTO resources
                   (id, title, summary, resource_type, content, path,
                    agent_id, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    resource_id,
                    title,
                    summary,
                    resource_type.value,
                    content,
                    path,
                    agent_id,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                )
            )
            # Index for FTS
            conn.execute(
                """INSERT INTO resources_fts (id, title, summary, content)
                   VALUES (?, ?, ?, ?)""",
                (resource_id, title, summary, content or "")
            )

        logger.debug(f"Stored resource {resource_id}: {title}")
        return resource_id

    def get(self, resource_id: str) -> Optional[Resource]:
        """
        Get a resource by ID and record access.

        Args:
            resource_id: ID of the resource.

        Returns:
            Resource if found, None otherwise.
        """
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM resources WHERE id = ?",
                (resource_id,)
            ).fetchone()

            if row:
                # Update access tracking
                conn.execute(
                    """UPDATE resources
                       SET access_count = access_count + 1,
                           last_accessed = ?
                       WHERE id = ?""",
                    (datetime.now().isoformat(), resource_id)
                )
                return self._row_to_resource(row)
            return None

    @timing_decorator
    async def search(
        self,
        query: str,
        resource_type: Optional[ResourceType] = None,
        limit: int = 10,
    ) -> List[Resource]:
        """
        Search resources using full-text search.

        Args:
            query: Search query.
            resource_type: Optional type filter.
            limit: Maximum results.

        Returns:
            List of matching resources.
        """
        loop = asyncio.get_event_loop()

        def db_read():
            with self.pool.get_conn(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get IDs from FTS
                # Sanitize the query for FTS5 by wrapping it in quotes
                sanitized_query = f'"{query.replace("\"", "\"\"")}"'
                fts_rows = conn.execute(
                    """SELECT id FROM resources_fts
                       WHERE resources_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (sanitized_query, limit * 2)  # Get extra for filtering
                ).fetchall()

                if not fts_rows:
                    # Fallback to LIKE search
                    return self._fallback_search(conn, query, resource_type, limit)

                ids = [row["id"] for row in fts_rows]
                placeholders = ",".join("?" * len(ids))

                sql = f"SELECT * FROM resources WHERE id IN ({placeholders})"
                params: List[Any] = list(ids)

                if resource_type:
                    sql += " AND resource_type = ?"
                    params.append(resource_type.value)

                sql += " LIMIT ?"
                params.append(limit)

                rows = conn.execute(sql, params).fetchall()
                return [self._row_to_resource(row) for row in rows]

        return await loop.run_in_executor(None, db_read)

    def _fallback_search(
        self,
        conn: sqlite3.Connection,
        query: str,
        resource_type: Optional[ResourceType],
        limit: int,
    ) -> List[Resource]:
        """Fallback to LIKE search when FTS fails."""
        conditions = ["(title LIKE ? OR summary LIKE ?)"]
        params: List[Any] = [f"%{query}%", f"%{query}%"]

        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type.value)

        where_clause = " AND ".join(conditions)

        rows = conn.execute(
            f"""SELECT * FROM resources
                WHERE {where_clause}
                ORDER BY access_count DESC
                LIMIT ?""",
            (*params, limit)
        ).fetchall()

        return [self._row_to_resource(row) for row in rows]

    def list_by_type(
        self,
        resource_type: ResourceType,
        limit: int = 50,
    ) -> List[Resource]:
        """
        List resources by type.

        Args:
            resource_type: Type to filter.
            limit: Maximum results.

        Returns:
            List of resources of given type.
        """
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM resources
                   WHERE resource_type = ?
                   ORDER BY access_count DESC, created_at DESC
                   LIMIT ?""",
                (resource_type.value, limit)
            ).fetchall()

            return [self._row_to_resource(row) for row in rows]

    def get_recent(self, limit: int = 10) -> List[Resource]:
        """
        Get recently accessed resources.

        Args:
            limit: Maximum results.

        Returns:
            List of recently accessed resources.
        """
        with self.pool.get_conn(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM resources
                   WHERE last_accessed IS NOT NULL
                   ORDER BY last_accessed DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()

            return [self._row_to_resource(row) for row in rows]

    def _row_to_resource(self, row: sqlite3.Row) -> Resource:
        """Convert database row to Resource object."""
        return Resource(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            resource_type=ResourceType(row["resource_type"]),
            content=row["content"],
            path=row["path"],
            agent_id=row["agent_id"],
            access_count=row["access_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
        )
