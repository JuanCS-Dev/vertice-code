"""
Exact Cache - Traditional exact-match caching for LLM responses.

Features:
- O(1) lookup with hash-based keys
- LRU eviction policy
- TTL expiration
- Thread-safe operations

References:
- Standard caching patterns
- GPTCache exact matching
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional, Any, Dict
from collections import OrderedDict
import asyncio

from .types import CacheConfig, CacheEntry, CacheStats, CacheHit, CacheMiss

logger = logging.getLogger(__name__)


class ExactCache:
    """Exact-match cache with LRU eviction.

    Features:
    - Hash-based key generation
    - LRU eviction when max size exceeded
    - TTL-based expiration
    - Async-safe operations

    Example:
        cache = ExactCache(config=CacheConfig(max_size=1000, ttl_seconds=3600))

        # Store
        await cache.set("What is Python?", "Python is a programming language...")

        # Retrieve
        result = await cache.get("What is Python?")
        if isinstance(result, CacheHit):
            print(result.value)
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        """Initialize exact cache.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = asyncio.Lock()

    def _hash_key(self, query: str) -> str:
        """Generate hash key for query.

        Args:
            query: Query text

        Returns:
            Hash string for cache key
        """
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def _evict_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries evicted
        """
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired(self.config.ttl_seconds)
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1

        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict least recently used entry if over capacity."""
        while len(self._cache) >= self.config.max_size:
            self._cache.popitem(last=False)
            self._stats.evictions += 1

    async def get(self, query: str) -> CacheHit | CacheMiss:
        """Get cached response for query.

        Args:
            query: Query text

        Returns:
            CacheHit if found, CacheMiss otherwise
        """
        async with self._lock:
            self._stats.total_requests += 1
            key = self._hash_key(query)

            if key not in self._cache:
                self._stats.misses += 1
                return CacheMiss(key=key, reason="not_found")

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired(self.config.ttl_seconds):
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return CacheMiss(key=key, reason="expired")

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()

            self._stats.hits += 1
            self._stats.bytes_saved += len(str(entry.value).encode())

            return CacheHit(value=entry.value, entry=entry, similarity=1.0)

    async def set(
        self,
        query: str,
        response: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CacheEntry:
        """Store response in cache.

        Args:
            query: Query text
            response: Response to cache
            metadata: Additional metadata

        Returns:
            Created cache entry
        """
        async with self._lock:
            key = self._hash_key(query)

            # Evict if necessary
            self._evict_expired()
            self._evict_lru()

            entry = CacheEntry(
                key=key,
                value=response,
                metadata=metadata or {},
            )

            self._cache[key] = entry
            self._stats.size = len(self._cache)

            logger.debug(f"Cached response for key {key[:8]}...")
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
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False

    async def clear(self) -> int:
        """Clear all entries from cache.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.size = 0
            logger.info(f"Cleared {count} cache entries")
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
        }

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics.

        Returns:
            Prometheus metrics string
        """
        lines = [
            f'cache_hits_total{{type="exact"}} {self._stats.hits}',
            f'cache_misses_total{{type="exact"}} {self._stats.misses}',
            f'cache_size{{type="exact"}} {self._stats.size}',
            f'cache_evictions_total{{type="exact"}} {self._stats.evictions}',
            f'cache_hit_rate{{type="exact"}} {self._stats.hit_rate}',
        ]
        return "\n".join(lines)
