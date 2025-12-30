"""
Caching Mixin - Unified caching integration for agents.

Provides:
- cached_call(): Automatic caching wrapper
- Hybrid exact + semantic caching
- Cache invalidation strategies
- Prometheus metrics

References:
- GPTCache patterns
- MeanCache: arXiv:2403.02694
"""

from __future__ import annotations

import logging
from typing import TypeVar, Callable, Awaitable, Optional, Dict, Any, List
from functools import wraps

from .types import CacheConfig, CacheStrategy, CacheHit
from .exact import ExactCache
from .semantic import SemanticCache

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CachingMixin:
    """Mixin providing caching capabilities to agents.

    Features:
    - Automatic response caching
    - Hybrid exact + semantic matching
    - Configurable cache strategies
    - Prometheus metrics

    Usage:
        class MyAgent(CachingMixin, BaseAgent):
            async def generate(self, prompt: str) -> str:
                return await self.cached_call(
                    self._llm.chat,
                    prompt,
                    cache_key=prompt,
                )

    Or with decorator:
        @self.with_caching()
        async def generate(self, prompt: str) -> str:
            return await self._llm.chat(prompt)
    """

    # Configuration (can be overridden by subclasses)
    CACHE_CONFIG = CacheConfig(
        strategy=CacheStrategy.EXACT,
        max_size=500,
        ttl_seconds=3600,
        similarity_threshold=0.85,
    )

    def _init_caching(self) -> None:
        """Initialize caching components."""
        if hasattr(self, "_caching_initialized"):
            return

        self._caching_initialized = True

        # Caches
        self._exact_cache = ExactCache(config=self.CACHE_CONFIG)
        self._semantic_cache: Optional[SemanticCache] = None

        # Initialize semantic cache if strategy requires it
        if self.CACHE_CONFIG.strategy in (CacheStrategy.SEMANTIC, CacheStrategy.HYBRID):
            self._semantic_cache = SemanticCache(config=self.CACHE_CONFIG)

        # Stats
        self._cache_stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tokens_saved": 0,
        }

    def set_embedding_function(
        self,
        embed_func: Callable[[str], Awaitable[List[float]]],
    ) -> None:
        """Set embedding function for semantic cache.

        Args:
            embed_func: Async function that returns embeddings
        """
        self._init_caching()

        if self._semantic_cache is None:
            self._semantic_cache = SemanticCache(
                config=self.CACHE_CONFIG,
                embed_func=embed_func,
            )
        else:
            self._semantic_cache._embed_func = embed_func

    async def cached_call(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        cache_key: Optional[str] = None,
        skip_cache: bool = False,
        cache_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> T:
        """Execute function with caching.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            cache_key: Key for caching (defaults to first arg)
            skip_cache: Skip cache lookup (but still store result)
            cache_metadata: Metadata to store with cached entry
            **kwargs: Keyword arguments for func

        Returns:
            Result from function or cache
        """
        self._init_caching()
        self._cache_stats["total_calls"] += 1

        # Determine cache key
        key = cache_key or (str(args[0]) if args else str(kwargs))

        # Try cache lookup
        if not skip_cache:
            hit = await self._lookup_cache(key)
            if hit is not None:
                self._cache_stats["cache_hits"] += 1
                logger.debug(f"Cache hit for key: {key[:50]}...")
                return hit

        # Cache miss - execute function
        self._cache_stats["cache_misses"] += 1
        result = await func(*args, **kwargs)

        # Store in cache
        await self._store_in_cache(key, result, cache_metadata)

        return result

    async def _lookup_cache(self, key: str) -> Optional[Any]:
        """Look up key in cache(s) based on strategy.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        strategy = self.CACHE_CONFIG.strategy

        # Exact match first (for EXACT and HYBRID)
        if strategy in (CacheStrategy.EXACT, CacheStrategy.HYBRID):
            result = await self._exact_cache.get(key)
            if isinstance(result, CacheHit):
                return result.value

        # Semantic match (for SEMANTIC and HYBRID fallback)
        if strategy in (CacheStrategy.SEMANTIC, CacheStrategy.HYBRID):
            if self._semantic_cache:
                result = await self._semantic_cache.get(key)
                if isinstance(result, CacheHit):
                    return result.value

        return None

    async def _store_in_cache(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store value in cache(s) based on strategy.

        Args:
            key: Cache key
            value: Value to store
            metadata: Additional metadata
        """
        strategy = self.CACHE_CONFIG.strategy

        if strategy in (CacheStrategy.EXACT, CacheStrategy.HYBRID):
            await self._exact_cache.set(key, value, metadata)

        if strategy in (CacheStrategy.SEMANTIC, CacheStrategy.HYBRID):
            if self._semantic_cache:
                await self._semantic_cache.set(key, value, metadata)

    def with_caching(
        self,
        cache_key_func: Optional[Callable[..., str]] = None,
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """Decorator to wrap function with caching.

        Args:
            cache_key_func: Function to generate cache key from args

        Example:
            @self.with_caching(cache_key_func=lambda prompt, **kw: prompt)
            async def generate(self, prompt: str) -> str:
                return await self._llm.chat(prompt)
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                # Generate cache key
                if cache_key_func:
                    key = cache_key_func(*args, **kwargs)
                else:
                    key = str(args) + str(sorted(kwargs.items()))

                return await self.cached_call(func, *args, cache_key=key, **kwargs)

            return wrapper

        return decorator

    async def invalidate_cache(
        self,
        key: Optional[str] = None,
        clear_all: bool = False,
    ) -> int:
        """Invalidate cache entries.

        Args:
            key: Specific key to invalidate
            clear_all: Clear entire cache

        Returns:
            Number of entries invalidated
        """
        self._init_caching()
        count = 0

        if clear_all:
            count += await self._exact_cache.clear()
            if self._semantic_cache:
                count += await self._semantic_cache.clear()
        elif key:
            if await self._exact_cache.delete(key):
                count += 1
            if self._semantic_cache and await self._semantic_cache.delete(key):
                count += 1

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics.

        Returns:
            Dictionary with all cache stats
        """
        self._init_caching()

        stats = {**self._cache_stats}
        stats["exact_cache"] = self._exact_cache.get_stats()

        if self._semantic_cache:
            stats["semantic_cache"] = self._semantic_cache.get_stats()

        # Calculate overall hit rate
        total = self._cache_stats["total_calls"]
        stats["overall_hit_rate"] = (
            self._cache_stats["cache_hits"] / total if total > 0 else 0.0
        )

        return stats

    def get_prometheus_cache_metrics(self) -> str:
        """Get Prometheus-formatted cache metrics.

        Returns:
            Prometheus metrics string
        """
        self._init_caching()

        agent_id = getattr(self, "agent_id", "unknown")
        lines = []

        lines.append(f'cache_calls_total{{agent="{agent_id}"}} {self._cache_stats["total_calls"]}')
        lines.append(f'cache_hits_total{{agent="{agent_id}"}} {self._cache_stats["cache_hits"]}')
        misses = self._cache_stats["cache_misses"]
        lines.append(f'cache_misses_total{{agent="{agent_id}"}} {misses}')

        # Include per-cache metrics
        lines.append(self._exact_cache.get_prometheus_metrics())
        if self._semantic_cache:
            lines.append(self._semantic_cache.get_prometheus_metrics())

        return "\n".join(lines)
