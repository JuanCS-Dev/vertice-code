"""
Intelligent Caching System for Vertice-Code Performance Optimization.

Provides LRU caching with TTL, cache warming, and intelligent cache
invalidation for frequently accessed data and expensive operations.
"""

import time
import hashlib
import asyncio
import logging
from typing import Any, Dict, Optional, Callable, TypeVar, Generic, Awaitable
from dataclasses import dataclass, field
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""

    value: T
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update access metadata."""
        self.accessed_at = time.time()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""

    max_size: int = 1000  # Maximum number of entries
    default_ttl: Optional[float] = 300  # 5 minutes default TTL
    max_memory_mb: int = 100  # Maximum memory usage in MB
    cleanup_interval: float = 60  # Cleanup interval in seconds
    enable_compression: bool = False  # Compress large entries


class IntelligentCache(Generic[T]):
    """
    Intelligent LRU cache with TTL and memory management.

    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Memory usage limits
    - Automatic cleanup
    - Cache warming support
    - Compression for large entries
    """

    def __init__(self, config: Optional[CacheConfig] = None, name: str = "cache"):
        self.config = config or CacheConfig()
        self.name = name
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._total_memory = 0
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "sets": 0,
            "deletes": 0,
        }

        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background cleanup task."""

        def cleanup_worker():
            while True:
                time.sleep(self.config.cleanup_interval)
                self._cleanup_expired()

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode("utf-8") if isinstance(value, str) else value)
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(len(str(k)) + self._estimate_size(v) for k, v in value.items())
            else:
                return len(str(value).encode("utf-8"))
        except Exception:
            return 1024  # Default estimate

    def _cleanup_expired(self):
        """Remove expired entries."""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
                    self._total_memory -= entry.size_bytes
                    self._stats["expirations"] += 1

            for key in expired_keys:
                del self._cache[key]

    def _evict_lru(self):
        """Evict least recently used entries to free memory."""
        with self._lock:
            while (
                len(self._cache) >= self.config.max_size
                or self._total_memory >= self.config.max_memory_mb * 1024 * 1024
            ):
                if not self._cache:
                    break

                # Remove oldest accessed entry
                oldest_key, oldest_entry = next(iter(self._cache.items()))
                for key, entry in self._cache.items():
                    if entry.accessed_at < oldest_entry.accessed_at:
                        oldest_key = key
                        oldest_entry = entry

                del self._cache[oldest_key]
                self._total_memory -= oldest_entry.size_bytes
                self._stats["evictions"] += 1

    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    del self._cache[key]
                    self._total_memory -= entry.size_bytes
                    self._stats["expirations"] += 1
                    self._stats["misses"] += 1
                    return None

                entry.touch()
                self._cache.move_to_end(key)  # Mark as recently used
                self._stats["hits"] += 1
                return entry.value

            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            size_bytes = self._estimate_size(value)
            ttl = ttl or self.config.default_ttl

            # Check if we need to evict
            if key not in self._cache:
                self._evict_lru()

            # Remove old entry if exists
            if key in self._cache:
                old_entry = self._cache[key]
                self._total_memory -= old_entry.size_bytes
            else:
                self._stats["sets"] += 1

            # Add new entry
            entry = CacheEntry(value=value, ttl=ttl, size_bytes=size_bytes)

            self._cache[key] = entry
            self._total_memory += size_bytes
            self._cache.move_to_end(key)

            return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self._total_memory -= entry.size_bytes
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._total_memory = 0
            self._stats = {k: 0 for k in self._stats}

    def get_or_set(self, key: str, factory: Callable[[], T], ttl: Optional[float] = None) -> T:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    async def get_or_set_async(
        self, key: str, factory: Callable[[], Awaitable[T]], ttl: Optional[float] = None
    ) -> T:
        """Async version of get_or_set."""
        value = self.get(key)
        if value is not None:
            return value

        value = await factory()
        self.set(key, value, ttl)
        return value

    def warm_cache(
        self, key_factory_pairs: Dict[str, Callable[[], T]], ttl: Optional[float] = None
    ):
        """Warm cache with pre-computed values."""
        logger.info(f"Warming cache with {len(key_factory_pairs)} entries")

        for key, factory in key_factory_pairs.items():
            try:
                value = factory()
                self.set(key, value, ttl)
            except Exception as e:
                logger.warning(f"Failed to warm cache for key {key}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = (
                self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"])
            ) * 100

            return {
                "name": self.name,
                "entries": len(self._cache),
                "memory_usage_mb": round(self._total_memory / (1024 * 1024), 2),
                "max_memory_mb": self.config.max_memory_mb,
                "memory_usage_percent": round(
                    (self._total_memory / (self.config.max_memory_mb * 1024 * 1024)) * 100, 2
                ),
                "hit_rate": round(hit_rate, 2),
                "total_requests": self._stats["hits"] + self._stats["misses"],
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
                "sets": self._stats["sets"],
                "deletes": self._stats["deletes"],
                "oldest_entry_age": min(
                    (time.time() - e.created_at for e in self._cache.values()), default=0
                ),
                "newest_entry_age": max(
                    (time.time() - e.created_at for e in self._cache.values()), default=0
                ),
            }

    def get_entries_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all cache entries."""
        with self._lock:
            return {
                key: {
                    "created_at": entry.created_at,
                    "accessed_at": entry.accessed_at,
                    "access_count": entry.access_count,
                    "ttl": entry.ttl,
                    "size_bytes": entry.size_bytes,
                    "is_expired": entry.is_expired(),
                    "age_seconds": time.time() - entry.created_at,
                }
                for key, entry in self._cache.items()
            }


# Global cache instances
_llm_cache = IntelligentCache(
    name="llm_responses", config=CacheConfig(max_size=500, default_ttl=600)
)  # 10 min
_api_cache = IntelligentCache(
    name="api_responses", config=CacheConfig(max_size=200, default_ttl=300)
)  # 5 min
_file_cache = IntelligentCache(
    name="file_operations", config=CacheConfig(max_size=100, default_ttl=1800)
)  # 30 min


def get_llm_cache() -> IntelligentCache:
    """Get LLM response cache."""
    return _llm_cache


def get_api_cache() -> IntelligentCache:
    """Get API response cache."""
    return _api_cache


def get_file_cache() -> IntelligentCache:
    """Get file operation cache."""
    return _file_cache


def cached(ttl: Optional[float] = None, cache_name: str = "default"):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        cache_name: Name of cache to use ('llm', 'api', 'file')
    """

    def decorator(func: Callable) -> Callable:
        cache_map = {
            "llm": _llm_cache,
            "api": _api_cache,
            "file": _file_cache,
            "default": _llm_cache,
        }

        cache = cache_map.get(cache_name, _llm_cache)

        def wrapper(*args, **kwargs):
            key = cache._generate_key(func.__name__, *args, **kwargs)
            return cache.get_or_set(key, lambda: func(*args, **kwargs), ttl)

        async def async_wrapper(*args, **kwargs):
            key = cache._generate_key(func.__name__, *args, **kwargs)
            return await cache.get_or_set_async(key, lambda: func(*args, **kwargs), ttl)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator
