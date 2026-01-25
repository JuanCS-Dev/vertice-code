"""
Router Cache Mixin - Caching for routing decisions.
"""

import time
from typing import Dict, Optional

from .types import RoutingDecision


class RouterCacheMixin:
    """Mixin for caching routing decisions."""

    def __init__(self) -> None:
        self._cache: Dict[str, RoutingDecision] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 300.0  # 5 minutes default

    def get_cached_decision(self, query: str) -> Optional[RoutingDecision]:
        """
        Get cached routing decision for a query.

        Args:
            query: Query string

        Returns:
            Cached decision if valid, None otherwise
        """
        if query not in self._cache:
            return None

        # Check TTL
        cached_time = self._cache_timestamps.get(query, 0)
        if time.time() - cached_time > self._cache_ttl:
            # Expired, remove from cache
            self._remove_from_cache(query)
            return None

        return self._cache[query]

    def cache_decision(self, query: str, decision: RoutingDecision) -> None:
        """
        Cache a routing decision.

        Args:
            query: Query string
            decision: Routing decision to cache
        """
        self._cache[query] = decision
        self._cache_timestamps[query] = time.time()

    def _remove_from_cache(self, query: str) -> None:
        """Remove a query from cache."""
        self._cache.pop(query, None)
        self._cache_timestamps.pop(query, None)

    def clear_expired_cache(self) -> int:
        """
        Clear expired entries from cache.

        Returns:
            Number of entries cleared
        """
        current_time = time.time()
        expired_queries = [
            query
            for query, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self._cache_ttl
        ]

        for query in expired_queries:
            self._remove_from_cache(query)

        return len(expired_queries)

    def clear_cache(self) -> int:
        """
        Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        cleared_count = len(self._cache)
        self._cache.clear()
        self._cache_timestamps.clear()
        return cleared_count

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache),
            "expired_entries": self.clear_expired_cache(),
        }
