"""
Caching Types - Configuration and data structures for LLM caching.

References:
- GPTCache patterns
- MeanCache: arXiv:2403.02694
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum


class CacheStrategy(Enum):
    """Caching strategy selection."""

    EXACT = "exact"  # Exact string match
    SEMANTIC = "semantic"  # Vector similarity match
    HYBRID = "hybrid"  # Exact first, then semantic


@dataclass
class CacheConfig:
    """Configuration for cache behavior.

    Attributes:
        strategy: Caching strategy to use
        max_size: Maximum entries in cache
        ttl_seconds: Time-to-live for entries
        similarity_threshold: Min similarity for semantic match (0.0-1.0)
        embedding_model: Model for semantic embeddings
        persist_path: Path for cache persistence (None for in-memory)
    """

    strategy: CacheStrategy = CacheStrategy.EXACT
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour default
    similarity_threshold: float = 0.85
    embedding_model: str = "text-embedding-3-small"
    persist_path: Optional[str] = None


@dataclass
class CacheEntry:
    """Single cache entry.

    Attributes:
        key: Cache key (query text or hash)
        value: Cached response
        embedding: Vector embedding for semantic search
        created_at: When entry was created
        last_accessed: When entry was last accessed
        access_count: Number of times accessed
        metadata: Additional context (model, tokens, etc.)
    """

    key: str
    value: Any
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if entry has expired.

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if entry is expired
        """
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > ttl_seconds

    def touch(self) -> None:
        """Update access time and count."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


@dataclass
class CacheStats:
    """Statistics for cache performance.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        size: Current number of entries
        evictions: Number of entries evicted
        total_requests: Total lookup requests
        bytes_saved: Estimated bytes saved by caching
    """

    hits: int = 0
    misses: int = 0
    size: int = 0
    evictions: int = 0
    total_requests: int = 0
    bytes_saved: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as percentage (0.0-1.0)
        """
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests


@dataclass
class CacheHit:
    """Result when cache hit occurs.

    Attributes:
        value: Cached response
        entry: Full cache entry
        similarity: Similarity score for semantic hits (1.0 for exact)
    """

    value: Any
    entry: CacheEntry
    similarity: float = 1.0


@dataclass
class CacheMiss:
    """Result when cache miss occurs.

    Attributes:
        key: Query key that missed
        reason: Why cache missed (not_found, expired, low_similarity)
    """

    key: str
    reason: str = "not_found"
