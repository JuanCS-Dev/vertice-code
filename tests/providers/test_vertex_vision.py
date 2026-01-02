"""
Tests for Vertex AI Multimodal Vision.

TDD tests for Sprint 4 of VERTEX_AI_PARITY_PLAN.
Follows CODE_CONSTITUTION: 100% type hints, Google style.

Tests:
1. Content block format - Image data as structured content
2. Part.from_data() creation - Native Vertex AI image parts
3. Screenshot/image analysis - End-to-end multimodal flow

References:
- https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/send-multimodal-prompts
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Test Data / Fixtures
# =============================================================================

@pytest.fixture
def sample_base64_image() -> str:
    """Small base64-encoded PNG (1x1 red pixel)."""
    # Minimal valid PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_image_content_block(sample_base64_image: str) -> Dict[str, Any]:
    """Sample image content block in Anthropic-style format."""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": sample_base64_image
        }
    }


@pytest.fixture
def sample_messages_with_image(sample_image_content_block: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Sample messages with image content."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                sample_image_content_block
            ]
        }
    ]


@pytest.fixture
def sample_text_messages() -> List[Dict[str, str]]:
    """Simple text messages without images."""
    return [
        {"role": "user", "content": "Hello, how are you?"}
    ]


# =============================================================================
# Test: Image Content Block Format
# =============================================================================

class TestImageContentBlockFormat:
    """Test image content block structure."""

    def test_content_block_has_required_fields(
        self,
        sample_image_content_block: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: Content block has type, source with type/media_type/data."""
        assert "type" in sample_image_content_block
        assert sample_image_content_block["type"] == "image"

        source = sample_image_content_block["source"]
        assert "type" in source
        assert source["type"] == "base64"
        assert "media_type" in source
        assert "data" in source

    def test_content_block_base64_is_valid(
        self,
        sample_image_content_block: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: Base64 data can be decoded."""
        data = sample_image_content_block["source"]["data"]

        # Should not raise
        decoded = base64.b64decode(data)
        assert len(decoded) > 0

    def test_supported_mime_types(self) -> None:
        """HYPOTHESIS: Common image mime types are supported."""
        supported = ["image/png", "image/jpeg", "image/gif", "image/webp"]

        for mime in supported:
            block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": "dGVzdA=="  # "test" in base64
                }
            }
            assert block["source"]["media_type"] == mime


# =============================================================================
# Test: _format_content_parts()
# =============================================================================

class TestFormatContentParts:
    """Test _format_content_parts() method in VertexAIProvider."""

    def test_format_text_content_returns_text_part(self) -> None:
        """HYPOTHESIS: String content returns Part.from_text()."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()

            mock_text_part = MagicMock()
            with patch('vertexai.generative_models.Part') as MockPart:
                MockPart.from_text.return_value = mock_text_part

                result = provider._format_content_parts("Hello world")

                MockPart.from_text.assert_called_once_with("Hello world")
                assert result == [mock_text_part]

    def test_format_image_content_returns_data_part(
        self,
        sample_image_content_block: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: Image content block returns Part.from_data()."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()

            mock_data_part = MagicMock()
            with patch('vertexai.generative_models.Part') as MockPart:
                MockPart.from_data.return_value = mock_data_part

                result = provider._format_content_parts(sample_image_content_block)

                # Should call from_data with decoded bytes and mime type
                MockPart.from_data.assert_called_once()
                call_kwargs = MockPart.from_data.call_args.kwargs
                assert "mime_type" in call_kwargs
                assert call_kwargs["mime_type"] == "image/png"
                assert "data" in call_kwargs

    def test_format_mixed_content_returns_multiple_parts(
        self,
        sample_image_content_block: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: Mixed text+image content returns multiple parts."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()

            mixed_content = [
                {"type": "text", "text": "What's in this image?"},
                sample_image_content_block
            ]

            mock_text_part = MagicMock(name="text_part")
            mock_data_part = MagicMock(name="data_part")

            with patch('vertexai.generative_models.Part') as MockPart:
                MockPart.from_text.return_value = mock_text_part
                MockPart.from_data.return_value = mock_data_part

                result = provider._format_content_parts(mixed_content)

                # Should have both parts
                assert len(result) == 2
                MockPart.from_text.assert_called_once()
                MockPart.from_data.assert_called_once()

    def test_format_content_handles_none(self) -> None:
        """HYPOTHESIS: None content returns empty list."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()

            result = provider._format_content_parts(None)
            assert result == []


# =============================================================================
# Test: stream_chat() with multimodal messages
# =============================================================================

class TestStreamChatMultimodal:
    """Test stream_chat() with image content."""

    @pytest.mark.asyncio
    async def test_stream_chat_processes_image_messages(
        self,
        sample_messages_with_image: List[Dict[str, Any]]
    ) -> None:
        """HYPOTHESIS: Messages with images are converted to Content with Parts."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            with patch('vertexai.generative_models.GenerativeModel', return_value=mock_model):
                with patch('vertexai.generative_models.Content') as MockContent:
                    with patch.object(provider, '_format_content_parts', return_value=[MagicMock()]) as mock_format:
                        async for _ in provider.stream_chat(sample_messages_with_image):
                            pass

                        # _format_content_parts should be called for user message
                        assert mock_format.called

    @pytest.mark.asyncio
    async def test_stream_chat_text_messages_still_work(
        self,
        sample_text_messages: List[Dict[str, str]]
    ) -> None:
        """HYPOTHESIS: Plain text messages continue to work."""
        with patch.dict('sys.modules', {
            'vertexai': MagicMock(),
            'vertexai.generative_models': MagicMock()
        }):
            from vertice_cli.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_chunk = MagicMock()
            mock_chunk.text = "Hello!"
            mock_response.__iter__ = lambda self: iter([mock_chunk])
            mock_model.generate_content.return_value = mock_response

            with patch('vertexai.generative_models.GenerativeModel', return_value=mock_model):
                chunks = []
                async for chunk in provider.stream_chat(sample_text_messages):
                    chunks.append(chunk)

                # Should get response
                assert len(chunks) >= 1


# =============================================================================
# Test: ImageReadTool content_block output
# =============================================================================

class TestImageReadToolContentBlock:
    """Test ImageReadTool returns content_block for vision."""

    @pytest.mark.asyncio
    async def test_image_read_returns_content_block_when_requested(
        self,
        tmp_path
    ) -> None:
        """HYPOTHESIS: ImageReadTool returns content_block format."""
        # Create a minimal test image
        test_image = tmp_path / "test.png"
        # Minimal valid PNG (1x1 transparent)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        test_image.write_bytes(png_data)

        from vertice_cli.tools.media_tools import ImageReadTool

        tool = ImageReadTool()
        result = await tool._execute_validated(
            file_path=str(test_image),
            include_base64=True,
            return_content_block=True
        )

        assert result.success
        assert "content_block" in result.data
        block = result.data["content_block"]
        assert block["type"] == "image"
        assert block["source"]["type"] == "base64"
        assert block["source"]["media_type"] == "image/png"
        assert len(block["source"]["data"]) > 0


# =============================================================================
# Integration Test (requires actual SDK - skip in CI)
# =============================================================================

@pytest.mark.skip(reason="Requires Vertex AI credentials - run manually")
class TestVertexVisionIntegration:
    """Integration tests with actual Vertex AI API."""

    @pytest.mark.asyncio
    async def test_real_image_analysis(self, tmp_path) -> None:
        """Integration test: Analyze a real image."""
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider
        from vertice_cli.tools.media_tools import ImageReadTool

        provider = VertexAIProvider()

        if not provider.is_available():
            pytest.skip("Vertex AI not available")

        # Create a simple test image
        test_image = tmp_path / "test.png"
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        test_image.write_bytes(png_data)

        # Read image
        tool = ImageReadTool()
        image_result = await tool._execute_validated(
            file_path=str(test_image),
            include_base64=True,
            return_content_block=True
        )

        # Create multimodal message
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in one word."},
                    image_result.data["content_block"]
                ]
            }
        ]

        chunks = []
        async for chunk in provider.stream_chat(messages):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert len(full_response) > 0

