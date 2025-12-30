"""
Semantic Cache - Vector similarity-based caching for LLM responses.

Uses embeddings to find semantically similar queries:
- "What is Python?" and "Tell me about Python" may hit same cache entry
- Configurable similarity threshold
- Efficient nearest neighbor search

References:
- GPTCache: github.com/zilliztech/GPTCache
- MeanCache: arXiv:2403.02694
- GenerativeCache: arXiv:2503.17603
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Optional, Any, Dict, List, Tuple, Callable, Awaitable
from datetime import datetime
import asyncio

from .types import CacheConfig, CacheEntry, CacheStats, CacheHit, CacheMiss

logger = logging.getLogger(__name__)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Similarity score (0.0-1.0)
    """
    if len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class SemanticCache:
    """Semantic similarity-based cache for LLM responses.

    Features:
    - Vector embedding-based similarity matching
    - Configurable similarity threshold
    - Hybrid exact + semantic lookup
    - Pluggable embedding function

    Example:
        cache = SemanticCache(
            config=CacheConfig(similarity_threshold=0.85),
            embed_func=openai_embed,  # async function returning List[float]
        )

        # Store with embedding
        await cache.set("What is Python?", "Python is...")

        # Semantic lookup - may match similar queries
        result = await cache.get("Tell me about Python programming")
        if isinstance(result, CacheHit):
            print(f"Hit with similarity {result.similarity}")
    """

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        embed_func: Optional[Callable[[str], Awaitable[List[float]]]] = None,
    ) -> None:
        """Initialize semantic cache.

        Args:
            config: Cache configuration
            embed_func: Async function to generate embeddings
        """
        self.config = config or CacheConfig()
        self._embed_func = embed_func or self._default_embed
        self._entries: Dict[str, CacheEntry] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()

    async def _default_embed(self, text: str) -> List[float]:
        """Default embedding function (simple hash-based).

        This is a placeholder - real usage should provide proper embedding function.

        Args:
            text: Text to embed

        Returns:
            Pseudo-embedding vector
        """
        # Simple deterministic pseudo-embedding for testing
        # In production, use actual embedding model
        h = hashlib.sha256(text.lower().encode()).digest()
        return [float(b) / 255.0 for b in h]

    def _hash_key(self, query: str) -> str:
        """Generate hash key for exact matching.

        Args:
            query: Query text

        Returns:
            Hash string
        """
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def _find_similar(
        self, embedding: List[float]
    ) -> Optional[Tuple[str, float]]:
        """Find most similar cached embedding.

        Args:
            embedding: Query embedding

        Returns:
            Tuple of (key, similarity) or None if no match above threshold
        """
        best_key: Optional[str] = None
        best_similarity = 0.0

        for key, cached_emb in self._embeddings.items():
            similarity = cosine_similarity(embedding, cached_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_key = key

        if best_key and best_similarity >= self.config.similarity_threshold:
            return best_key, best_similarity

        return None

    def _evict_oldest(self) -> None:
        """Evict oldest entry if over capacity."""
        if len(self._entries) < self.config.max_size:
            return

        # Find oldest entry
        oldest_key: Optional[str] = None
        oldest_time: Optional[datetime] = None

        for key, entry in self._entries.items():
            if oldest_time is None or entry.last_accessed < oldest_time:
                oldest_time = entry.last_accessed
                oldest_key = key

        if oldest_key:
            del self._entries[oldest_key]
            if oldest_key in self._embeddings:
                del self._embeddings[oldest_key]
            self._stats.evictions += 1

    def _evict_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries evicted
        """
        expired_keys = [
            key
            for key, entry in self._entries.items()
            if entry.is_expired(self.config.ttl_seconds)
        ]

        for key in expired_keys:
            del self._entries[key]
            if key in self._embeddings:
                del self._embeddings[key]
            self._stats.evictions += 1

        return len(expired_keys)

    async def get(self, query: str) -> CacheHit | CacheMiss:
        """Get cached response for query using semantic similarity.

        Args:
            query: Query text

        Returns:
            CacheHit if found (exact or semantic), CacheMiss otherwise
        """
        async with self._lock:
            self._stats.total_requests += 1
            self._evict_expired()

            # Try exact match first
            key = self._hash_key(query)
            if key in self._entries:
                entry = self._entries[key]
                if not entry.is_expired(self.config.ttl_seconds):
                    entry.touch()
                    self._stats.hits += 1
                    self._stats.bytes_saved += len(str(entry.value).encode())
                    return CacheHit(value=entry.value, entry=entry, similarity=1.0)

            # Try semantic match
            query_embedding = await self._embed_func(query)
            similar = self._find_similar(query_embedding)

            if similar:
                similar_key, similarity = similar
                entry = self._entries[similar_key]

                if not entry.is_expired(self.config.ttl_seconds):
                    entry.touch()
                    self._stats.hits += 1
                    self._stats.bytes_saved += len(str(entry.value).encode())

                    logger.debug(
                        f"Semantic cache hit: similarity={similarity:.3f}"
                    )
                    return CacheHit(
                        value=entry.value, entry=entry, similarity=similarity
                    )

            self._stats.misses += 1
            return CacheMiss(key=key, reason="low_similarity")

    async def set(
        self,
        query: str,
        response: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CacheEntry:
        """Store response in cache with embedding.

        Args:
            query: Query text
            response: Response to cache
            metadata: Additional metadata

        Returns:
            Created cache entry
        """
        async with self._lock:
            self._evict_expired()
            self._evict_oldest()

            key = self._hash_key(query)
            embedding = await self._embed_func(query)

            entry = CacheEntry(
                key=key,
                value=response,
                embedding=embedding,
                metadata=metadata or {},
            )

            self._entries[key] = entry
            self._embeddings[key] = embedding
            self._stats.size = len(self._entries)

            logger.debug(f"Cached response with embedding for key {key[:8]}...")
            return entry

    async def delete(self, query: str) -> bool:
        """Delete entry from cache.

        Args:
            query: Query text

        Returns:
            True if entry was deleted
        """
        async with self._lock:
            key = self._hash_key(query)
            if key in self._entries:
                del self._entries[key]
                if key in self._embeddings:
                    del self._embeddings[key]
                self._stats.size = len(self._entries)
                return True
            return False

    async def clear(self) -> int:
        """Clear all entries from cache.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._entries)
            self._entries.clear()
            self._embeddings.clear()
            self._stats.size = 0
            logger.info(f"Cleared {count} semantic cache entries")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "size": self._stats.size,
            "evictions": self._stats.evictions,
            "hit_rate": self._stats.hit_rate,
            "bytes_saved": self._stats.bytes_saved,
            "total_requests": self._stats.total_requests,
            "similarity_threshold": self.config.similarity_threshold,
        }

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics.

        Returns:
            Prometheus metrics string
        """
        lines = [
            f'cache_hits_total{{type="semantic"}} {self._stats.hits}',
            f'cache_misses_total{{type="semantic"}} {self._stats.misses}',
            f'cache_size{{type="semantic"}} {self._stats.size}',
            f'cache_evictions_total{{type="semantic"}} {self._stats.evictions}',
            f'cache_hit_rate{{type="semantic"}} {self._stats.hit_rate}',
        ]
        return "\n".join(lines)
