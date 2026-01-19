"""
Phase 6 Caching Module Tests.

Tests for LLM response caching:
- ExactCache with hash-based lookup
- SemanticCache with vector similarity
- CachingMixin integration
"""

from __future__ import annotations

import asyncio
from typing import List

import pytest

from core.caching import (
    ExactCache,
    SemanticCache,
    CachingMixin,
    CacheConfig,
    CacheEntry,
    CacheStats,
    CacheHit,
    CacheMiss,
)
from core.caching.types import CacheStrategy


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_entry_creation(self) -> None:
        """Creates entry with defaults."""
        entry = CacheEntry(key="test", value="response")
        assert entry.key == "test"
        assert entry.value == "response"
        assert entry.access_count == 0

    def test_entry_expiration(self) -> None:
        """Entry expires based on TTL."""
        entry = CacheEntry(key="test", value="response")
        assert not entry.is_expired(3600)  # Not expired

    def test_entry_touch(self) -> None:
        """Touch updates access time and count."""
        entry = CacheEntry(key="test", value="response")
        entry.touch()
        assert entry.access_count == 1


class TestCacheStats:
    """Tests for CacheStats."""

    def test_hit_rate_empty(self) -> None:
        """Hit rate is 0 when no requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self) -> None:
        """Hit rate calculated correctly."""
        stats = CacheStats(hits=7, misses=3, total_requests=10)
        assert stats.hit_rate == 0.7


class TestExactCache:
    """Tests for ExactCache."""

    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        """Stores and retrieves value."""
        cache = ExactCache()
        await cache.set("What is Python?", "Python is a programming language.")

        result = await cache.get("What is Python?")
        assert isinstance(result, CacheHit)
        assert result.value == "Python is a programming language."
        assert result.similarity == 1.0

    @pytest.mark.asyncio
    async def test_cache_miss(self) -> None:
        """Returns miss for unknown key."""
        cache = ExactCache()
        result = await cache.get("unknown query")
        assert isinstance(result, CacheMiss)
        assert result.reason == "not_found"

    @pytest.mark.asyncio
    async def test_case_insensitive(self) -> None:
        """Normalizes query case."""
        cache = ExactCache()
        await cache.set("Hello World", "response")

        result = await cache.get("hello world")
        assert isinstance(result, CacheHit)

    @pytest.mark.asyncio
    async def test_lru_eviction(self) -> None:
        """Evicts least recently used entries."""
        config = CacheConfig(max_size=2)
        cache = ExactCache(config=config)

        await cache.set("query1", "response1")
        await cache.set("query2", "response2")
        await cache.set("query3", "response3")  # Should evict query1

        result = await cache.get("query1")
        assert isinstance(result, CacheMiss)

    @pytest.mark.asyncio
    async def test_ttl_expiration(self) -> None:
        """Expires entries after TTL."""
        config = CacheConfig(ttl_seconds=0)  # Immediate expiration
        cache = ExactCache(config=config)

        await cache.set("query", "response")
        await asyncio.sleep(0.01)

        result = await cache.get("query")
        assert isinstance(result, CacheMiss)
        assert result.reason == "expired"

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Deletes entry from cache."""
        cache = ExactCache()
        await cache.set("query", "response")
        deleted = await cache.delete("query")
        assert deleted

        result = await cache.get("query")
        assert isinstance(result, CacheMiss)

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """Clears all entries."""
        cache = ExactCache()
        await cache.set("q1", "r1")
        await cache.set("q2", "r2")

        count = await cache.clear()
        assert count == 2

    def test_get_stats(self) -> None:
        """Returns statistics."""
        cache = ExactCache()
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_prometheus_metrics(self) -> None:
        """Generates Prometheus metrics."""
        cache = ExactCache()
        metrics = cache.get_prometheus_metrics()
        assert "cache_hits_total" in metrics
        assert 'type="exact"' in metrics


class TestSemanticCache:
    """Tests for SemanticCache."""

    @pytest.mark.asyncio
    async def test_set_and_get_exact(self) -> None:
        """Exact match works like ExactCache."""
        cache = SemanticCache()
        await cache.set("What is Python?", "Python is a programming language.")

        result = await cache.get("What is Python?")
        assert isinstance(result, CacheHit)
        assert result.value == "Python is a programming language."

    @pytest.mark.asyncio
    async def test_semantic_similarity(self) -> None:
        """Finds semantically similar queries."""

        # Use custom embedding that returns same vector for similar queries
        async def mock_embed(text: str) -> List[float]:
            if "python" in text.lower():
                return [1.0, 0.0, 0.0] * 10 + [0.1]
            return [0.0, 1.0, 0.0] * 10 + [0.1]

        config = CacheConfig(similarity_threshold=0.8)
        cache = SemanticCache(config=config, embed_func=mock_embed)

        await cache.set("What is Python?", "Python is a programming language.")

        # Similar query should hit
        result = await cache.get("Tell me about Python programming")
        assert isinstance(result, CacheHit)
        assert result.similarity > 0.8

    @pytest.mark.asyncio
    async def test_semantic_miss_low_similarity(self) -> None:
        """Misses when similarity too low."""

        async def mock_embed(text: str) -> List[float]:
            if "python" in text.lower():
                return [1.0, 0.0, 0.0] * 11
            return [0.0, 1.0, 0.0] * 11  # Very different

        config = CacheConfig(similarity_threshold=0.9)
        cache = SemanticCache(config=config, embed_func=mock_embed)

        await cache.set("What is Python?", "Python response")

        result = await cache.get("What is JavaScript?")
        assert isinstance(result, CacheMiss)

    @pytest.mark.asyncio
    async def test_stores_embedding(self) -> None:
        """Stores embedding with entry."""
        cache = SemanticCache()
        entry = await cache.set("test query", "test response")
        assert entry.embedding is not None
        assert len(entry.embedding) > 0

    def test_get_stats(self) -> None:
        """Returns statistics with threshold."""
        config = CacheConfig(similarity_threshold=0.85)
        cache = SemanticCache(config=config)
        stats = cache.get_stats()
        assert stats["similarity_threshold"] == 0.85


class TestCachingMixin:
    """Tests for CachingMixin."""

    @pytest.mark.asyncio
    async def test_cached_call_miss_then_hit(self) -> None:
        """Caches on miss, returns cached on hit."""

        class TestAgent(CachingMixin):
            pass

        agent = TestAgent()
        call_count = 0

        async def expensive_call(query: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"response for {query}"

        # First call - cache miss
        result1 = await agent.cached_call(expensive_call, "test query", cache_key="test")
        assert result1 == "response for test query"
        assert call_count == 1

        # Second call - cache hit
        result2 = await agent.cached_call(expensive_call, "test query", cache_key="test")
        assert result2 == "response for test query"
        assert call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_skip_cache(self) -> None:
        """skip_cache bypasses cache lookup."""

        class TestAgent(CachingMixin):
            pass

        agent = TestAgent()
        call_count = 0

        async def call_func() -> str:
            nonlocal call_count
            call_count += 1
            return "response"

        await agent.cached_call(call_func, cache_key="key")
        await agent.cached_call(call_func, cache_key="key", skip_cache=True)

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_cache(self) -> None:
        """Invalidates specific key."""

        class TestAgent(CachingMixin):
            pass

        agent = TestAgent()

        async def func() -> str:
            return "response"

        await agent.cached_call(func, cache_key="key")
        count = await agent.invalidate_cache(key="key")
        assert count >= 1

    @pytest.mark.asyncio
    async def test_clear_all_cache(self) -> None:
        """Clears entire cache."""

        class TestAgent(CachingMixin):
            pass

        agent = TestAgent()

        async def func(x: int) -> str:
            return f"response{x}"

        await agent.cached_call(func, 1, cache_key="k1")
        await agent.cached_call(func, 2, cache_key="k2")

        count = await agent.invalidate_cache(clear_all=True)
        assert count >= 2

    def test_get_cache_stats(self) -> None:
        """Returns cache statistics."""

        class TestAgent(CachingMixin):
            pass

        agent = TestAgent()
        agent._init_caching()

        stats = agent.get_cache_stats()
        assert "total_calls" in stats
        assert "cache_hits" in stats
        assert "overall_hit_rate" in stats

    def test_prometheus_cache_metrics(self) -> None:
        """Generates Prometheus metrics."""

        class TestAgent(CachingMixin):
            agent_id = "test_agent"

        agent = TestAgent()
        agent._init_caching()

        metrics = agent.get_prometheus_cache_metrics()
        assert "cache_calls_total" in metrics
        assert "test_agent" in metrics

    @pytest.mark.asyncio
    async def test_with_caching_decorator(self) -> None:
        """Decorator wraps function with caching."""

        class TestAgent(CachingMixin):
            def __init__(self):
                self.call_count = 0

            async def generate(self, prompt: str) -> str:
                self.call_count += 1
                return f"response: {prompt}"

        agent = TestAgent()

        @agent.with_caching(cache_key_func=lambda p: p)
        async def cached_generate(prompt: str) -> str:
            return await agent.generate(prompt)

        result1 = await cached_generate("hello")
        result2 = await cached_generate("hello")

        assert result1 == result2
        assert agent.call_count == 1


class TestCacheConfig:
    """Tests for CacheConfig."""

    def test_default_strategy(self) -> None:
        """Default strategy is exact."""
        config = CacheConfig()
        assert config.strategy == CacheStrategy.EXACT

    def test_custom_config(self) -> None:
        """Accepts custom configuration."""
        config = CacheConfig(
            strategy=CacheStrategy.SEMANTIC,
            max_size=500,
            ttl_seconds=1800,
            similarity_threshold=0.9,
        )
        assert config.strategy == CacheStrategy.SEMANTIC
        assert config.max_size == 500
        assert config.ttl_seconds == 1800
        assert config.similarity_threshold == 0.9
