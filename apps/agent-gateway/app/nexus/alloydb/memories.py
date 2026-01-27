"""
AlloyDB Memory Operations.

Store and search memories with vector embeddings.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

from nexus.types import MemoryBlock, MemoryLevel

logger = logging.getLogger(__name__)


class MemoryOperations:
    """Mixin for memory operations on AlloyDB."""

    async def store_memory(self, block: MemoryBlock) -> bool:
        """Store a memory block with embedding."""
        if not self._initialized:
            return False

        try:
            embedding = None
            if self._embeddings and block.content:
                embedding = await self._embeddings.aembed_query(block.content)

            query = """
                INSERT INTO nexus_memories (id, level, content, embedding, token_count, importance, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    last_accessed = NOW(),
                    access_count = nexus_memories.access_count + 1
            """

            await self.execute(
                query,
                block.id,
                block.level.value,
                block.content,
                embedding,
                block.token_count,
                block.importance,
                json.dumps(block.metadata),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    async def search_memories(
        self,
        query: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Tuple[MemoryBlock, float]]:
        """Semantic search across memories using vector similarity."""
        if not self._initialized:
            return []

        try:
            if self._embeddings:
                query_embedding = await self._embeddings.aembed_query(query)
                return await self._search_memories_vector(
                    query_embedding, level, limit, min_similarity
                )
            else:
                return await self._search_memories_keyword(query, level, limit)

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def _search_memories_vector(
        self,
        embedding: List[float],
        level: Optional[MemoryLevel],
        limit: int,
        min_similarity: float,
    ) -> List[Tuple[MemoryBlock, float]]:
        """Vector similarity search."""
        level_filter = f"AND level = '{level.value}'" if level else ""

        sql = f"""
            SELECT id, level, content, token_count, importance, created_at, metadata,
                   1 - (embedding <=> $1::vector) as similarity
            FROM nexus_memories
            WHERE embedding IS NOT NULL {level_filter}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """

        rows = await self.fetch(sql, str(embedding), limit)

        results = []
        for row in rows:
            similarity = float(row["similarity"])
            if similarity >= min_similarity:
                block = MemoryBlock(
                    id=row["id"],
                    level=MemoryLevel(row["level"]),
                    content=row["content"],
                    token_count=row["token_count"],
                    importance=row["importance"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                results.append((block, similarity))

        return results

    async def _search_memories_keyword(
        self,
        query: str,
        level: Optional[MemoryLevel],
        limit: int,
    ) -> List[Tuple[MemoryBlock, float]]:
        """Keyword-based search fallback."""
        level_filter = f"AND level = '{level.value}'" if level else ""

        sql = f"""
            SELECT id, level, content, token_count, importance, created_at, metadata
            FROM nexus_memories
            WHERE content ILIKE $1 {level_filter}
            ORDER BY importance DESC
            LIMIT $2
        """

        rows = await self.fetch(sql, f"%{query}%", limit)

        return [
            (
                MemoryBlock(
                    id=row["id"],
                    level=MemoryLevel(row["level"]),
                    content=row["content"],
                    token_count=row["token_count"],
                    importance=row["importance"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                ),
                0.5,  # Fixed similarity for keyword search
            )
            for row in rows
        ]

    async def get_memories_by_level(
        self,
        level: MemoryLevel,
        limit: int = 50,
    ) -> List[MemoryBlock]:
        """Get memories by level."""
        if not self._initialized:
            return []

        try:
            sql = """
                SELECT id, level, content, token_count, importance, created_at, metadata
                FROM nexus_memories
                WHERE level = $1
                ORDER BY importance DESC, created_at DESC
                LIMIT $2
            """

            rows = await self.fetch(sql, level.value, limit)

            return [
                MemoryBlock(
                    id=row["id"],
                    level=MemoryLevel(row["level"]),
                    content=row["content"],
                    token_count=row["token_count"],
                    importance=row["importance"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []
