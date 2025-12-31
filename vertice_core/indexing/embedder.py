"""
Semantic Embedder - OpenAI text-embedding-3-large via Azure.

Generates high-quality embeddings for code chunks.

Features:
- Batch processing for efficiency
- Persistent cache (SQLite) to avoid re-computation
- Local fallback for offline development
- Rate limit handling with exponential backoff

Phase 10: Refinement Sprint 1

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

import httpx

from .chunker import CodeChunk

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    # Model settings
    model: str = "text-embedding-3-large"
    dimensions: int = 3072  # text-embedding-3-large default

    # Azure settings
    azure_endpoint: str = ""
    azure_api_key: str = ""
    azure_deployment: str = "text-embedding-3-large"
    azure_api_version: str = "2024-10-21"

    # Batching
    batch_size: int = 100  # Max items per API call
    max_concurrent_batches: int = 5

    # Caching
    cache_enabled: bool = True
    cache_dir: str = ".vertice/embeddings"

    # Rate limiting
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Fallback
    use_local_fallback: bool = True
    local_model: str = "hash"  # "hash" or "minilm" (if sentence-transformers installed)


@dataclass
class EmbeddingResult:
    """Result of embedding a chunk."""

    chunk_id: str
    embedding: List[float]
    tokens_used: int = 0
    from_cache: bool = False
    model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "embedding": self.embedding,
            "tokens_used": self.tokens_used,
            "model": self.model,
        }


class EmbeddingCache:
    """
    SQLite-based embedding cache.

    Stores embeddings persistently to avoid re-computation.
    Uses content hash as key for deduplication.
    """

    def __init__(self, cache_dir: str = ".vertice/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "embeddings.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    content_hash TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON embeddings(model)
            """)

    @contextmanager
    def _get_connection(self):
        """Get SQLite connection with context management."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _content_hash(self, content: str, model: str) -> str:
        """Generate hash for content + model combination."""
        data = f"{model}:{content}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get(self, content: str, model: str) -> Optional[List[float]]:
        """Get cached embedding if exists."""
        content_hash = self._content_hash(content, model)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT embedding FROM embeddings WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def get_batch(
        self,
        contents: List[str],
        model: str
    ) -> Dict[str, Optional[List[float]]]:
        """Get multiple cached embeddings."""
        results = {}
        with self._get_connection() as conn:
            for content in contents:
                content_hash = self._content_hash(content, model)
                cursor = conn.execute(
                    "SELECT embedding FROM embeddings WHERE content_hash = ?",
                    (content_hash,)
                )
                row = cursor.fetchone()
                results[content] = json.loads(row[0]) if row else None
        return results

    def put(
        self,
        content: str,
        embedding: List[float],
        model: str
    ) -> None:
        """Store embedding in cache."""
        content_hash = self._content_hash(content, model)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings
                (content_hash, embedding, model, dimensions, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    content_hash,
                    json.dumps(embedding),
                    model,
                    len(embedding),
                    time.time()
                )
            )

    def put_batch(
        self,
        items: List[Tuple[str, List[float]]],
        model: str
    ) -> None:
        """Store multiple embeddings."""
        with self._get_connection() as conn:
            for content, embedding in items:
                content_hash = self._content_hash(content, model)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO embeddings
                    (content_hash, embedding, model, dimensions, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        content_hash,
                        json.dumps(embedding),
                        model,
                        len(embedding),
                        time.time()
                    )
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*), model FROM embeddings GROUP BY model")
            by_model = {row[1]: row[0] for row in cursor.fetchall()}

            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            total = cursor.fetchone()[0]

            cursor = conn.execute("SELECT SUM(dimensions) FROM embeddings")
            total_dims = cursor.fetchone()[0] or 0

        return {
            "total_embeddings": total,
            "by_model": by_model,
            "approx_memory_mb": (total_dims * 4) / (1024 * 1024),  # 4 bytes per float
        }

    def clear(self, model: Optional[str] = None) -> int:
        """Clear cache, optionally for specific model."""
        with self._get_connection() as conn:
            if model:
                cursor = conn.execute(
                    "DELETE FROM embeddings WHERE model = ?",
                    (model,)
                )
            else:
                cursor = conn.execute("DELETE FROM embeddings")
            return cursor.rowcount


class SemanticEmbedder:
    """
    High-quality semantic embeddings via Azure OpenAI.

    Features:
    - Batch processing for efficiency (up to 100 texts per call)
    - Persistent SQLite cache
    - Rate limit handling with exponential backoff
    - Local fallback for offline development

    Usage:
        embedder = SemanticEmbedder()
        results = await embedder.embed_chunks(chunks)
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedder with configuration."""
        self.config = config or EmbeddingConfig()

        # Load from environment if not provided
        if not self.config.azure_endpoint:
            self.config.azure_endpoint = os.getenv(
                "AZURE_OPENAI_ENDPOINT",
                "https://eastus2.api.cognitive.microsoft.com/"
            )
        if not self.config.azure_api_key:
            self.config.azure_api_key = os.getenv("AZURE_OPENAI_KEY", "")

        # Initialize cache
        self._cache: Optional[EmbeddingCache] = None
        if self.config.cache_enabled:
            self._cache = EmbeddingCache(self.config.cache_dir)

        # HTTP client (lazy initialized)
        self._client: Optional[httpx.AsyncClient] = None

        # Stats
        self._stats = {
            "total_embedded": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "total_tokens": 0,
        }

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_connections=10),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        """Check if Azure API is available."""
        return bool(self.config.azure_api_key and self.config.azure_endpoint)

    def _build_url(self) -> str:
        """Build Azure embeddings API URL."""
        base = self.config.azure_endpoint.rstrip("/")
        deployment = self.config.azure_deployment
        version = self.config.azure_api_version
        return f"{base}/openai/deployments/{deployment}/embeddings?api-version={version}"

    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with embedding vector
        """
        results = await self.embed_texts([text])
        return results[0]

    async def embed_texts(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Embed multiple texts with batching and caching.

        Args:
            texts: List of texts to embed
            show_progress: Whether to log progress

        Returns:
            List of EmbeddingResult objects
        """
        if not texts:
            return []

        results: Dict[int, EmbeddingResult] = {}
        to_embed: List[Tuple[int, str]] = []

        # Determine which model to use for caching
        use_azure = self.is_available()
        cache_model = self.config.model if use_azure else "local-hash"

        # Check cache first
        if self._cache:
            for i, text in enumerate(texts):
                cached = self._cache.get(text, cache_model)
                if cached:
                    results[i] = EmbeddingResult(
                        chunk_id=f"text_{i}",
                        embedding=cached,
                        from_cache=True,
                        model=cache_model,
                    )
                    self._stats["cache_hits"] += 1
                else:
                    to_embed.append((i, text))
        else:
            to_embed = [(i, text) for i, text in enumerate(texts)]

        # Embed remaining texts
        if to_embed:
            if use_azure:
                await self._embed_via_azure(to_embed, results, show_progress)
            elif self.config.use_local_fallback:
                self._embed_local(to_embed, results)
            else:
                raise RuntimeError("Azure API not available and local fallback disabled")

        # Return in original order
        return [results[i] for i in range(len(texts))]

    async def _embed_via_azure(
        self,
        to_embed: List[Tuple[int, str]],
        results: Dict[int, EmbeddingResult],
        show_progress: bool
    ) -> None:
        """Embed texts via Azure OpenAI API."""
        client = await self._ensure_client()
        url = self._build_url()

        # Split into batches
        batch_size = self.config.batch_size
        batches = [
            to_embed[i:i + batch_size]
            for i in range(0, len(to_embed), batch_size)
        ]

        if show_progress:
            logger.info(f"Embedding {len(to_embed)} texts in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            indices = [item[0] for item in batch]
            texts = [item[1] for item in batch]

            # Retry with exponential backoff
            for attempt in range(self.config.max_retries):
                try:
                    response = await client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                            "api-key": self.config.azure_api_key,
                        },
                        json={
                            "input": texts,
                            "model": self.config.model,
                            "dimensions": self.config.dimensions,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        usage = data.get("usage", {})
                        total_tokens = usage.get("total_tokens", 0)

                        self._stats["api_calls"] += 1
                        self._stats["total_tokens"] += total_tokens

                        # Process embeddings
                        cache_items = []
                        for emb_data in data["data"]:
                            idx = emb_data["index"]
                            original_idx = indices[idx]
                            embedding = emb_data["embedding"]

                            results[original_idx] = EmbeddingResult(
                                chunk_id=f"text_{original_idx}",
                                embedding=embedding,
                                tokens_used=total_tokens // len(texts),
                                from_cache=False,
                                model=self.config.model,
                            )

                            cache_items.append((texts[idx], embedding))

                        # Cache results
                        if self._cache:
                            self._cache.put_batch(cache_items, self.config.model)

                        self._stats["total_embedded"] += len(texts)
                        break

                    elif response.status_code == 429:
                        # Rate limit - get retry-after header
                        retry_after = response.headers.get("Retry-After")
                        wait_time = int(retry_after) if retry_after else (
                            self.config.retry_base_delay * (2 ** attempt)
                        )
                        logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)

                    else:
                        error_text = response.text[:200]
                        raise RuntimeError(
                            f"Azure API error {response.status_code}: {error_text}"
                        )

                except httpx.TimeoutException:
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_base_delay * (2 ** attempt)
                        logger.warning(f"Timeout, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise

            if show_progress:
                logger.info(f"Batch {batch_idx + 1}/{len(batches)} complete")

    def _embed_local(
        self,
        to_embed: List[Tuple[int, str]],
        results: Dict[int, EmbeddingResult]
    ) -> None:
        """
        Local fallback embedding using hash-based pseudo-embeddings.

        For development/testing only - not semantic!
        """
        import math

        for idx, text in to_embed:
            # Hash-based pseudo-embedding
            dim = self.config.dimensions
            embedding = [0.0] * dim

            # Use multiple hash functions for better distribution
            words = text.lower().split()
            for i, word in enumerate(words):
                h1 = hash(word) % 1000000 / 1000000.0
                h2 = hash(word + str(i)) % 1000000 / 1000000.0
                pos1 = hash(word) % dim
                pos2 = (hash(word) * 31) % dim
                embedding[pos1] += h1
                embedding[(pos1 + 1) % dim] += h2 * 0.5
                embedding[pos2] -= h1 * 0.3

            # Normalize
            norm = math.sqrt(sum(x * x for x in embedding)) or 1.0
            embedding = [x / norm for x in embedding]

            results[idx] = EmbeddingResult(
                chunk_id=f"text_{idx}",
                embedding=embedding,
                from_cache=False,
                model="local-hash",
            )

            # Cache locally too
            if self._cache:
                self._cache.put(text, embedding, "local-hash")

        self._stats["total_embedded"] += len(to_embed)

    async def embed_chunks(
        self,
        chunks: List[CodeChunk],
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Embed code chunks using their embedding text.

        Args:
            chunks: List of CodeChunk objects
            show_progress: Whether to log progress

        Returns:
            List of EmbeddingResult with chunk_id set to chunk.chunk_id
        """
        # Get embedding text from chunks
        texts = [chunk.to_embedding_text() for chunk in chunks]

        # Embed
        results = await self.embed_texts(texts, show_progress)

        # Update chunk IDs
        for result, chunk in zip(results, chunks):
            result.chunk_id = chunk.chunk_id

        return results

    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        result = await self.embed_text(query)
        return result.embedding

    def get_stats(self) -> Dict[str, Any]:
        """Get embedder statistics."""
        stats = self._stats.copy()
        if self._cache:
            stats["cache"] = self._cache.get_stats()
        stats["model"] = self.config.model
        stats["dimensions"] = self.config.dimensions
        stats["is_available"] = self.is_available()
        return stats

    def clear_cache(self, model: Optional[str] = None) -> int:
        """Clear embedding cache."""
        if self._cache:
            return self._cache.clear(model)
        return 0


# Singleton instance
_embedder: Optional[SemanticEmbedder] = None


def get_embedder(config: Optional[EmbeddingConfig] = None) -> SemanticEmbedder:
    """Get or create singleton embedder instance."""
    global _embedder
    if _embedder is None or config is not None:
        _embedder = SemanticEmbedder(config)
    return _embedder


__all__ = [
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingCache",
    "SemanticEmbedder",
    "get_embedder",
]
