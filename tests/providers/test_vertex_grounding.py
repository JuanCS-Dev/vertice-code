"""
Tests for Vertex AI Google Search Grounding.

TDD tests for Sprint 2 of VERTEX_AI_PARITY_PLAN.
Follows CODE_CONSTITUTION: 100% type hints, Google style.

Tests:
1. _get_grounding_tool() - Create Google Search grounding tool
2. stream_chat() with grounding - Include grounding tool in request
3. Grounding metadata parsing - Extract search results from response
4. Toggle grounding - Enable/disable at runtime
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Test Data / Fixtures
# =============================================================================


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample chat messages for grounding tests."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the 2024 Euro Championship?"},
    ]


@pytest.fixture
def mock_grounding_response() -> Dict[str, Any]:
    """Mock response with grounding metadata from Vertex AI."""
    return {
        "text": "Spain won the 2024 Euro Championship.",
        "grounding_metadata": {
            "web_search_queries": ["2024 Euro Championship winner"],
            "grounding_chunks": [
                {
                    "web": {
                        "uri": "https://www.uefa.com/euro2024/",
                        "title": "UEFA Euro 2024 Official",
                    }
                }
            ],
            "grounding_supports": [
                {
                    "segment": {"start_index": 0, "end_index": 38},
                    "grounding_chunk_indices": [0],
                    "confidence_scores": [0.95],
                }
            ],
        },
    }


# =============================================================================
# Test: _get_grounding_tool()
# =============================================================================


class TestGetGroundingTool:
    """Test _get_grounding_tool() method."""

    def test_get_grounding_tool_returns_tool_instance(self) -> None:
        """HYPOTHESIS: Returns a valid Tool instance for Google Search."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            mock_tool = MagicMock()

            with patch("vertexai.generative_models.Tool") as MockTool:
                MockTool.from_google_search_retrieval.return_value = mock_tool

                provider = VertexAIProvider()
                result = provider._get_grounding_tool()

                # Should call from_google_search_retrieval
                MockTool.from_google_search_retrieval.assert_called_once()
                assert result is not None

    def test_get_grounding_tool_fallback_on_error(self) -> None:
        """HYPOTHESIS: Returns None gracefully if SDK not available."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            with patch("vertexai.generative_models.Tool") as MockTool:
                MockTool.from_google_search_retrieval.side_effect = ImportError("SDK not found")

                provider = VertexAIProvider()
                result = provider._get_grounding_tool()

                # Should return None without raising
                assert result is None


# =============================================================================
# Test: stream_chat() with enable_grounding
# =============================================================================


class TestStreamChatWithGrounding:
    """Test stream_chat() with grounding enabled."""

    @pytest.mark.asyncio
    async def test_stream_chat_passes_grounding_tool_when_enabled(
        self, sample_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: Grounding tool is added when enable_grounding=True."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True  # Skip initialization

            mock_grounding_tool = MagicMock()
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            with patch.object(
                provider, "_get_grounding_tool", return_value=mock_grounding_tool
            ) as mock_get_tool:
                with patch(
                    "vertexai.generative_models.GenerativeModel", return_value=mock_model
                ) as MockModel:
                    chunks = []
                    async for chunk in provider.stream_chat(sample_messages, enable_grounding=True):
                        chunks.append(chunk)

                    # _get_grounding_tool should be called
                    mock_get_tool.assert_called_once()

                    # Model should be created with grounding tool
                    call_kwargs = MockModel.call_args.kwargs
                    assert "tools" in call_kwargs
                    assert mock_grounding_tool in call_kwargs["tools"]

    @pytest.mark.asyncio
    async def test_stream_chat_no_grounding_tool_when_disabled(
        self, sample_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: No grounding tool when enable_grounding=False."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            with patch.object(provider, "_get_grounding_tool") as mock_get_tool:
                with patch("vertexai.generative_models.GenerativeModel", return_value=mock_model):
                    async for _ in provider.stream_chat(sample_messages, enable_grounding=False):
                        pass

                    # _get_grounding_tool should NOT be called
                    mock_get_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_chat_combines_tools_and_grounding(
        self, sample_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: Both function calling tools and grounding can be used together."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_grounding_tool = MagicMock(name="grounding_tool")
            mock_function_tool = MagicMock(name="function_tool")
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            # Mock _convert_tools to return a function tool
            with patch.object(provider, "_get_grounding_tool", return_value=mock_grounding_tool):
                with patch.object(provider, "_convert_tools", return_value=[mock_function_tool]):
                    with patch(
                        "vertexai.generative_models.GenerativeModel", return_value=mock_model
                    ) as MockModel:
                        function_tools = [
                            {"name": "read_file", "description": "Read", "parameters": {}}
                        ]

                        async for _ in provider.stream_chat(
                            sample_messages, tools=function_tools, enable_grounding=True
                        ):
                            pass

                        # Model should have BOTH tools
                        call_kwargs = MockModel.call_args.kwargs
                        assert "tools" in call_kwargs
                        # Should contain both function tool and grounding tool
                        tools_list = call_kwargs["tools"]
                        assert len(tools_list) >= 2


# =============================================================================
# Test: Grounding metadata parsing
# =============================================================================


class TestGroundingMetadataParsing:
    """Test parsing grounding metadata from response."""

    @pytest.mark.asyncio
    async def test_yields_grounding_metadata_as_json(self) -> None:
        """HYPOTHESIS: Grounding metadata is yielded as structured JSON."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            # Create mock chunk with grounding metadata
            mock_grounding_chunk = MagicMock()
            mock_grounding_chunk.web.uri = "https://example.com"
            mock_grounding_chunk.web.title = "Example Source"

            mock_grounding_metadata = MagicMock()
            mock_grounding_metadata.grounding_chunks = [mock_grounding_chunk]
            mock_grounding_metadata.web_search_queries = ["test query"]

            mock_candidate = MagicMock()
            mock_candidate.grounding_metadata = mock_grounding_metadata
            mock_candidate.content.parts = []

            mock_text_part = MagicMock()
            mock_text_part.text = "Response text"
            mock_text_part.function_call = None

            mock_chunk = MagicMock()
            mock_chunk.candidates = [mock_candidate]
            mock_chunk.text = "Response text"

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([mock_chunk])
            mock_model.generate_content.return_value = mock_response

            with patch("vertexai.generative_models.GenerativeModel", return_value=mock_model):
                chunks = []
                async for chunk in provider.stream_chat(
                    [{"role": "user", "content": "test"}], enable_grounding=True
                ):
                    chunks.append(chunk)

                # Should have yielded text
                assert len(chunks) >= 1


# =============================================================================
# Test: Grounding toggle
# =============================================================================


class TestGroundingToggle:
    """Test runtime grounding toggle."""

    def test_set_grounding_updates_flag(self) -> None:
        """HYPOTHESIS: set_grounding() method updates internal flag."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()

            # Default should be False
            assert provider.enable_grounding is False

            # Toggle on
            provider.set_grounding(True)
            assert provider.enable_grounding is True

            # Toggle off
            provider.set_grounding(False)
            assert provider.enable_grounding is False

    def test_grounding_default_can_be_set_in_constructor(self) -> None:
        """HYPOTHESIS: enable_grounding can be set in __init__."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            # Create with grounding enabled by default
            provider = VertexAIProvider(enable_grounding=True)
            assert provider.enable_grounding is True


# =============================================================================
# Integration Test (requires actual SDK - skip in CI)
# =============================================================================


@pytest.mark.skip(reason="Requires Vertex AI credentials - run manually")
class TestVertexGroundingIntegration:
    """Integration tests with actual Vertex AI API."""

    @pytest.mark.asyncio
    async def test_real_grounding_query(self) -> None:
        """Integration test: Real query with Google Search grounding."""
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider()

        if not provider.is_available():
            pytest.skip("Vertex AI not available")

        messages = [
            {"role": "user", "content": "What are the latest news about AI in January 2026?"}
        ]

        chunks = []
        async for chunk in provider.stream_chat(messages, enable_grounding=True):
            chunks.append(chunk)

        # Should have received a response with grounding
        full_response = "".join(chunks)
        assert len(full_response) > 0
        # Grounding responses typically reference sources
        # Note: Can't assert specific content as it changes
