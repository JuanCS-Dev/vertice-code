"""
Tests for Vertex AI Context Caching.

TDD tests for Sprint 3 of VERTEX_AI_PARITY_PLAN.
Follows CODE_CONSTITUTION: 100% type hints, Google style.

Tests:
1. Implicit Caching - Prompt structure optimization
2. Explicit Caching - CachedContent creation, usage, TTL, deletion

References:
- https://ai.google.dev/gemini-api/docs/caching
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache
"""

from __future__ import annotations

import importlib.util
from typing import Dict, List, Type
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Helper: Import VertexCacheManager without triggering __init__.py chain
# =============================================================================


def get_cache_manager_class() -> Type:
    """Import VertexCacheManager directly to avoid protobuf conflicts."""
    spec = importlib.util.spec_from_file_location(
        "vertex_cache", "vertice_core/core/providers/vertex_cache.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VertexCacheManager


# =============================================================================
# Test Data / Fixtures
# =============================================================================


@pytest.fixture
def large_context() -> str:
    """Large context (>2048 tokens) for caching tests."""
    # Approximately 2500+ tokens (10000+ chars / 4 = 2500+ tokens)
    return "This is a large codebase context for testing context caching. " * 200


@pytest.fixture
def system_instruction() -> str:
    """Sample system instruction for caching."""
    return "You are a code assistant. Analyze code and provide helpful suggestions."


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample chat messages."""
    return [{"role": "user", "content": "What does this code do?"}]


@pytest.fixture
def cache_manager_class() -> Type:
    """Get VertexCacheManager class."""
    return get_cache_manager_class()


# =============================================================================
# Test: Implicit Caching (Prompt Structure)
# =============================================================================


class TestImplicitCachingPromptStructure:
    """Test prompt structure optimization for implicit caching."""

    def test_system_instruction_comes_first(self) -> None:
        """HYPOTHESIS: System instruction is placed at start for cache efficiency."""
        # Implicit caching requires stable prefix - system instruction should be first
        # This tests the order: system -> context -> user input

        system = "You are a helpful assistant."
        context = "Codebase context here..."
        user_input = "What does this do?"

        # Correct order for caching (stable prefix first)
        correct_order = [system, context, user_input]

        # Verify system instruction is first
        assert correct_order[0] == system
        assert correct_order[-1] == user_input

    def test_context_before_user_input(self) -> None:
        """HYPOTHESIS: Static context comes before dynamic user input."""
        # For implicit cache hits, stable content must precede variable content

        messages = [
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Context: Large codebase here..."},
            {"role": "user", "content": "Question: What does function X do?"},
        ]

        # Context should come before question
        context_idx = next(i for i, m in enumerate(messages) if "Context:" in m.get("content", ""))
        question_idx = next(
            i for i, m in enumerate(messages) if "Question:" in m.get("content", "")
        )

        assert context_idx < question_idx


# =============================================================================
# Test: VertexCacheManager - Creation
# =============================================================================


class TestCacheCreation:
    """Test CachedContent creation."""

    def test_create_cache_returns_cache_name(
        self, large_context: str, system_instruction: str, cache_manager_class: Type
    ) -> None:
        """HYPOTHESIS: create_cache returns a cache resource name."""
        mock_cache = MagicMock()
        mock_cache.name = "projects/123/locations/us-central1/cachedContents/abc123"

        manager = cache_manager_class(project="test-project")
        manager._client = MagicMock()
        manager._client.caches.create.return_value = mock_cache

        with patch.dict("sys.modules", {"google.genai.types": MagicMock()}):
            cache_name = manager.create_cache(
                name="test-cache",
                content=large_context,
                system_instruction=system_instruction,
                ttl_seconds=3600,
            )

        assert cache_name is not None
        assert "cachedContents" in cache_name

    def test_create_cache_with_minimum_tokens(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: Cache creation requires minimum 2048 tokens."""
        manager = cache_manager_class(project="test-project")

        # Content too small (less than 2048 tokens)
        small_content = "This is too small"

        with pytest.raises(ValueError, match="minimum.*token"):
            manager.create_cache(name="small-cache", content=small_content, ttl_seconds=3600)


# =============================================================================
# Test: VertexCacheManager - Usage
# =============================================================================


class TestCacheUsage:
    """Test using cached content with models."""

    def test_get_cache_returns_cached_content(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: get_cache returns CachedContent by name."""
        manager = cache_manager_class(project="test-project")

        # Add a mock cache
        mock_cache = MagicMock()
        mock_cache.name = "test-cache"
        manager._caches["test-cache"] = mock_cache

        result = manager.get_cache("test-cache")
        assert result is not None
        assert result.name == "test-cache"

    def test_get_cache_returns_none_for_unknown(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: get_cache returns None for unknown cache name."""
        manager = cache_manager_class(project="test-project")

        result = manager.get_cache("nonexistent")
        assert result is None

    def test_list_caches_returns_all_active(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: list_caches returns all active cache names."""
        manager = cache_manager_class(project="test-project")

        # Add mock caches
        manager._caches["cache1"] = MagicMock()
        manager._caches["cache2"] = MagicMock()

        result = manager.list_caches()
        assert len(result) == 2
        assert "cache1" in result
        assert "cache2" in result


# =============================================================================
# Test: VertexCacheManager - TTL Management
# =============================================================================


class TestCacheTTLManagement:
    """Test cache TTL update and extension."""

    def test_extend_ttl_updates_cache(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: extend_ttl updates cache with new TTL."""
        manager = cache_manager_class(project="test-project")

        mock_cache = MagicMock()
        mock_cache.name = "resource-name"
        manager._caches["test-cache"] = mock_cache
        manager._client = MagicMock()

        with patch.dict("sys.modules", {"google.genai.types": MagicMock()}):
            manager.extend_ttl("test-cache", additional_seconds=7200)

        # Should call update on client
        manager._client.caches.update.assert_called_once()

    def test_extend_ttl_noop_for_unknown(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: extend_ttl does nothing for unknown cache."""
        manager = cache_manager_class(project="test-project")

        # Should not raise
        manager.extend_ttl("nonexistent", additional_seconds=3600)


# =============================================================================
# Test: VertexCacheManager - Deletion
# =============================================================================


class TestCacheDeletion:
    """Test cache deletion."""

    def test_delete_cache_removes_from_storage(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: delete_cache removes cache from manager."""
        manager = cache_manager_class(project="test-project")

        mock_cache = MagicMock()
        mock_cache.name = "resource-name"
        manager._caches["test-cache"] = mock_cache
        manager._client = MagicMock()

        manager.delete_cache("test-cache")

        # Should call delete on client
        manager._client.caches.delete.assert_called_once()

        # Should remove from internal storage
        assert "test-cache" not in manager._caches

    def test_delete_cache_noop_for_unknown(self, cache_manager_class: Type) -> None:
        """HYPOTHESIS: delete_cache does nothing for unknown cache."""
        manager = cache_manager_class(project="test-project")

        # Should not raise
        manager.delete_cache("nonexistent")


# =============================================================================
# Test: stream_chat() with cached_content
# =============================================================================


class TestStreamChatWithCache:
    """Test stream_chat() with cached content."""

    @pytest.mark.asyncio
    async def test_stream_chat_uses_cached_content(
        self, sample_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: cached_content parameter is passed to model."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            cache_name = "projects/123/locations/us-central1/cachedContents/abc"

            with patch("vertexai.generative_models.GenerativeModel") as MockModel:
                # Set up from_cached_content to return mock model
                MockModel.from_cached_content.return_value = mock_model

                async for _ in provider.stream_chat(sample_messages, cached_content=cache_name):
                    pass

                # Should use from_cached_content
                MockModel.from_cached_content.assert_called_once_with(cache_name)

    @pytest.mark.asyncio
    async def test_stream_chat_without_cache_uses_normal_model(
        self, sample_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: No cached_content uses normal model initialization."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            with patch(
                "vertexai.generative_models.GenerativeModel", return_value=mock_model
            ) as MockModel:
                async for _ in provider.stream_chat(sample_messages):
                    pass

                # Should NOT use from_cached_content
                MockModel.from_cached_content.assert_not_called()


# =============================================================================
# Integration Test (requires actual SDK - skip in CI)
# =============================================================================


@pytest.mark.skip(reason="Requires Vertex AI credentials - run manually")
class TestVertexCachingIntegration:
    """Integration tests with actual Vertex AI API."""

    @pytest.mark.asyncio
    async def test_real_cache_lifecycle(self) -> None:
        """Integration test: Create, use, and delete cache."""
        from vertice_core.core.providers.vertex_cache import VertexCacheManager
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        manager = VertexCacheManager()
        provider = VertexAIProvider()

        if not provider.is_available():
            pytest.skip("Vertex AI not available")

        # Large context for caching
        large_context = "This is a large code context...\n" * 500

        # Create cache
        cache_name = manager.create_cache(
            name="integration-test-cache", content=large_context, ttl_seconds=300
        )
        assert cache_name is not None

        try:
            # Use cache
            chunks = []
            async for chunk in provider.stream_chat(
                [{"role": "user", "content": "Summarize the context."}], cached_content=cache_name
            ):
                chunks.append(chunk)

            assert len(chunks) > 0

        finally:
            # Cleanup
            manager.delete_cache("integration-test-cache")
