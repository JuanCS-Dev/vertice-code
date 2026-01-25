"""
Vector Store - Semantic Search for Code Chunks.

Provides similarity search over embedded code chunks.

Features:
- ChromaDB backend (if available)
- In-memory fallback with SQLite persistence
- Cosine similarity search
- Metadata filtering (filepath, language, chunk_type)
- Incremental updates

Phase 10: Refinement Sprint 1

Soli Deo Gloria
"""

from __future__ import annotations

import json
import logging
import math
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .chunker import CodeChunk, ChunkType

logger = logging.getLogger(__name__)


# Check if ChromaDB is available
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.debug("ChromaDB not installed, using in-memory fallback")


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""

    # Storage
    persist_dir: str = ".vertice/index"
    collection_name: str = "codebase"

    # Search settings
    default_top_k: int = 10
    similarity_threshold: float = 0.5
    distance_metric: str = "cosine"  # cosine, l2, inner_product

    # ChromaDB settings
    use_chromadb: bool = True
    chroma_anonymized_telemetry: bool = False

    # In-memory fallback
    max_memory_items: int = 100_000


@dataclass
class SearchResult:
    """Result of a similarity search."""

    chunk_id: str
    filepath: str
    content: str
    score: float
    chunk_type: ChunkType
    start_line: int
    end_line: int
    name: str
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "filepath": self.filepath,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "score": round(self.score, 4),
            "chunk_type": self.chunk_type.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "name": self.name,
        }


class InMemoryVectorStore:
    """
    In-memory vector store with SQLite persistence.

    Fallback when ChromaDB is not available.
    Uses brute-force cosine similarity search.
    """

    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self._vectors: Dict[str, List[float]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

        # SQLite for persistence
        persist_path = Path(config.persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)
        self.db_path = persist_path / "vectors.db"
        self._init_db()
        self._load_from_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    chunk_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    metadata TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_filepath
                ON vectors(json_extract(metadata, '$.filepath'))
            """
            )

    @contextmanager
    def _get_connection(self):
        """Get SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _load_from_db(self) -> None:
        """Load vectors from SQLite into memory."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT chunk_id, embedding, metadata FROM vectors")
            for row in cursor:
                chunk_id, embedding_blob, metadata_json = row
                self._vectors[chunk_id] = json.loads(embedding_blob)
                self._metadata[chunk_id] = json.loads(metadata_json)

        logger.info(f"Loaded {len(self._vectors)} vectors from disk")

    def add(
        self, chunk_ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add vectors to store."""
        with self._get_connection() as conn:
            for chunk_id, embedding, metadata in zip(chunk_ids, embeddings, metadatas):
                self._vectors[chunk_id] = embedding
                self._metadata[chunk_id] = metadata

                conn.execute(
                    """
                    INSERT OR REPLACE INTO vectors (chunk_id, embedding, metadata, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (chunk_id, json.dumps(embedding), json.dumps(metadata), time.time()),
                )

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors."""
        if not self._vectors:
            return []

        # Filter candidates
        candidates = []
        for chunk_id, embedding in self._vectors.items():
            metadata = self._metadata.get(chunk_id, {})

            # Apply filters
            if filters:
                skip = False
                for key, value in filters.items():
                    if key == "filepath" and metadata.get("filepath") != value:
                        skip = True
                        break
                    if key == "language" and metadata.get("language") != value:
                        skip = True
                        break
                    if key == "chunk_type" and metadata.get("chunk_type") != value:
                        skip = True
                        break
                if skip:
                    continue

            # Compute similarity
            score = self._cosine_similarity(query_embedding, embedding)
            candidates.append((chunk_id, score, metadata))

        # Sort and return top k
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def delete(self, chunk_ids: List[str]) -> int:
        """Delete vectors by ID."""
        deleted = 0
        with self._get_connection() as conn:
            for chunk_id in chunk_ids:
                if chunk_id in self._vectors:
                    del self._vectors[chunk_id]
                    self._metadata.pop(chunk_id, None)
                    conn.execute("DELETE FROM vectors WHERE chunk_id = ?", (chunk_id,))
                    deleted += 1
        return deleted

    def delete_by_filepath(self, filepath: str) -> int:
        """Delete all vectors for a filepath."""
        to_delete = [
            chunk_id
            for chunk_id, meta in self._metadata.items()
            if meta.get("filepath") == filepath
        ]
        return self.delete(to_delete)

    def count(self) -> int:
        """Get number of vectors."""
        return len(self._vectors)

    def clear(self) -> None:
        """Clear all vectors."""
        self._vectors.clear()
        self._metadata.clear()
        with self._get_connection() as conn:
            conn.execute("DELETE FROM vectors")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)


class ChromaVectorStore:
    """
    ChromaDB-based vector store.

    High-performance vector search with metadata filtering.
    """

    def __init__(self, config: VectorStoreConfig):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed: pip install chromadb")

        self.config = config

        # Initialize ChromaDB
        persist_path = Path(config.persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        settings = ChromaSettings(
            anonymized_telemetry=config.chroma_anonymized_telemetry,
            allow_reset=True,
            is_persistent=True,
        )

        self._client = chromadb.PersistentClient(path=str(persist_path), settings=settings)

        # Get or create collection
        distance_fn = {"cosine": "cosine", "l2": "l2", "inner_product": "ip"}.get(
            config.distance_metric, "cosine"
        )

        self._collection = self._client.get_or_create_collection(
            name=config.collection_name, metadata={"hnsw:space": distance_fn}
        )

        logger.info(f"ChromaDB collection '{config.collection_name}' ready")

    def add(
        self, chunk_ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add vectors to ChromaDB."""
        # Convert ChunkType enum to string for metadata
        safe_metadatas = []
        for meta in metadatas:
            safe_meta = meta.copy()
            if "chunk_type" in safe_meta and hasattr(safe_meta["chunk_type"], "value"):
                safe_meta["chunk_type"] = safe_meta["chunk_type"].value
            safe_metadatas.append(safe_meta)

        self._collection.upsert(ids=chunk_ids, embeddings=embeddings, metadatas=safe_metadatas)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search ChromaDB for similar vectors."""
        # Build where clause
        where = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append({key: {"$eq": value}})
            if len(conditions) == 1:
                where = conditions[0]
            elif len(conditions) > 1:
                where = {"$and": conditions}

        # Query
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances"],
        )

        # Convert to standard format
        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns distance, convert to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                # Cosine distance to similarity: similarity = 1 - distance
                score = 1 - distance
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                output.append((chunk_id, score, metadata))

        return output

    def delete(self, chunk_ids: List[str]) -> int:
        """Delete vectors by ID."""
        try:
            self._collection.delete(ids=chunk_ids)
            return len(chunk_ids)
        except Exception as e:
            logger.warning(f"Delete failed: {e}")
            return 0

    def delete_by_filepath(self, filepath: str) -> int:
        """Delete all vectors for a filepath."""
        # Query to find IDs with this filepath
        results = self._collection.get(where={"filepath": filepath}, include=[])

        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0

    def count(self) -> int:
        """Get number of vectors."""
        return self._collection.count()

    def clear(self) -> None:
        """Clear all vectors."""
        # Delete and recreate collection
        self._client.delete_collection(self.config.collection_name)
        self._collection = self._client.create_collection(
            name=self.config.collection_name, metadata={"hnsw:space": "cosine"}
        )


class VectorStore:
    """
    Unified vector store interface.

    Automatically selects ChromaDB or in-memory backend.

    Usage:
        store = VectorStore()
        store.add_chunks(chunks, embeddings)
        results = store.search("find error handling code")
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig()

        # Select backend
        if self.config.use_chromadb and CHROMADB_AVAILABLE:
            self._backend = ChromaVectorStore(self.config)
            self._backend_type = "chromadb"
        else:
            self._backend = InMemoryVectorStore(self.config)
            self._backend_type = "memory"
            if self.config.use_chromadb:
                logger.warning("ChromaDB requested but not available, using in-memory store")

        logger.info(f"VectorStore initialized with {self._backend_type} backend")

    @property
    def backend_type(self) -> str:
        """Get current backend type."""
        return self._backend_type

    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> int:
        """
        Add code chunks with their embeddings to the store.

        Args:
            chunks: List of CodeChunk objects
            embeddings: Corresponding embedding vectors

        Returns:
            Number of chunks added
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings")

        chunk_ids = []
        metadatas = []

        for chunk in chunks:
            chunk_ids.append(chunk.chunk_id)
            metadatas.append(
                {
                    "filepath": chunk.filepath,
                    "name": chunk.name,
                    "chunk_type": chunk.chunk_type.value,
                    "language": chunk.language,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "tokens": chunk.tokens,
                    "content": chunk.content,  # Store content for retrieval
                    "docstring": chunk.docstring or "",
                    "parent": chunk.parent or "",
                }
            )

        self._backend.add(chunk_ids, embeddings, metadatas)
        return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filepath_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        chunk_type_filter: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Search for similar code chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results (default from config)
            filepath_filter: Filter by filepath
            language_filter: Filter by language
            chunk_type_filter: Filter by chunk type
            min_score: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        top_k = top_k or self.config.default_top_k
        min_score = min_score if min_score is not None else self.config.similarity_threshold

        # Build filters
        filters = {}
        if filepath_filter:
            filters["filepath"] = filepath_filter
        if language_filter:
            filters["language"] = language_filter
        if chunk_type_filter:
            filters["chunk_type"] = chunk_type_filter

        # Search backend
        raw_results = self._backend.search(
            query_embedding,
            top_k=top_k * 2,  # Get more to filter by score
            filters=filters if filters else None,
        )

        # Convert to SearchResult and filter by score
        results = []
        for chunk_id, score, metadata in raw_results:
            if score < min_score:
                continue

            # Parse chunk_type
            try:
                chunk_type = ChunkType(metadata.get("chunk_type", "unknown"))
            except ValueError:
                chunk_type = ChunkType.UNKNOWN

            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    filepath=metadata.get("filepath", ""),
                    content=metadata.get("content", ""),
                    score=score,
                    chunk_type=chunk_type,
                    start_line=metadata.get("start_line", 0),
                    end_line=metadata.get("end_line", 0),
                    name=metadata.get("name", ""),
                    language=metadata.get("language", ""),
                    metadata=metadata,
                )
            )

        return results[:top_k]

    def delete_chunks(self, chunk_ids: List[str]) -> int:
        """Delete chunks by ID."""
        return self._backend.delete(chunk_ids)

    def delete_file(self, filepath: str) -> int:
        """Delete all chunks for a file."""
        return self._backend.delete_by_filepath(filepath)

    def count(self) -> int:
        """Get number of indexed chunks."""
        return self._backend.count()

    def clear(self) -> None:
        """Clear all indexed chunks."""
        self._backend.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "backend": self._backend_type,
            "collection": self.config.collection_name,
            "total_chunks": self.count(),
            "persist_dir": self.config.persist_dir,
        }


# Singleton instance
_store: Optional[VectorStore] = None


def get_vector_store(config: Optional[VectorStoreConfig] = None) -> VectorStore:
    """Get or create singleton vector store instance."""
    global _store
    if _store is None or config is not None:
        _store = VectorStore(config)
    return _store


__all__ = [
    "VectorStoreConfig",
    "SearchResult",
    "VectorStore",
    "get_vector_store",
    "CHROMADB_AVAILABLE",
]
