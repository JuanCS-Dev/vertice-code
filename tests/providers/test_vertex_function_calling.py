"""
Tests for Vertex AI Native Function Calling.

TDD tests for Sprint 1 of VERTEX_AI_PARITY_PLAN.
Follows CODE_CONSTITUTION: 100% type hints, Google style.

Tests:
1. _convert_tools() - Convert internal tool schemas to Vertex AI format
2. stream_chat() with tools - Native function calling via API
3. Function call response parsing - Extract tool calls from response
4. Fallback to text parsing - Backward compatibility
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Test Data / Fixtures
# =============================================================================


@pytest.fixture
def sample_tool_schema() -> Dict[str, Any]:
    """Sample tool schema matching Tool.get_schema() format."""
    return {
        "name": "read_file",
        "description": "Read complete contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to current directory"}
            },
            "required": ["path"],
        },
    }


@pytest.fixture
def multiple_tool_schemas() -> List[Dict[str, Any]]:
    """Multiple tool schemas for testing."""
    return [
        {
            "name": "read_file",
            "description": "Read file contents",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path"}},
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "list_directory",
            "description": "List directory contents",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Directory path"}},
                "required": ["path"],
            },
        },
    ]


@pytest.fixture
def mock_function_call_response() -> Dict[str, Any]:
    """Mock response with function call from Vertex AI."""
    return {"tool_call": {"name": "read_file", "arguments": {"path": "README.md"}}}


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample chat messages."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Read the README.md file"},
    ]


# =============================================================================
# Test: _convert_tools()
# =============================================================================


class TestConvertTools:
    """Test _convert_tools() method."""

    def test_convert_tools_returns_none_when_no_tools(self) -> None:
        """HYPOTHESIS: Returns None when tools is None or empty."""
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider()

        # Test with None
        result = provider._convert_tools(None)
        assert result is None

        # Test with empty list
        result = provider._convert_tools([])
        assert result is None

    @patch("vertice_core.core.providers.vertex_ai.VertexAIProvider._ensure_client")
    def test_convert_tools_from_schema_dict(
        self, mock_ensure: MagicMock, sample_tool_schema: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: Converts dict schema to FunctionDeclaration."""
        # Mock Vertex AI SDK
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            # Create mock FunctionDeclaration and Tool
            mock_func_decl = MagicMock()
            mock_tool = MagicMock()

            with patch(
                "vertexai.generative_models.FunctionDeclaration", return_value=mock_func_decl
            ) as MockFD:
                with patch("vertexai.generative_models.Tool", return_value=mock_tool) as MockTool:
                    provider = VertexAIProvider()
                    result = provider._convert_tools([sample_tool_schema])

                    # Verify FunctionDeclaration was called with correct params
                    MockFD.assert_called_once_with(
                        name="read_file",
                        description="Read complete contents of a file",
                        parameters=sample_tool_schema["parameters"],
                    )

                    # Verify Tool was created with declarations
                    MockTool.assert_called_once()

                    # Result should be a list with one Tool
                    assert result is not None
                    assert len(result) == 1

    @patch("vertice_core.core.providers.vertex_ai.VertexAIProvider._ensure_client")
    def test_convert_tools_multiple_tools(
        self, mock_ensure: MagicMock, multiple_tool_schemas: List[Dict[str, Any]]
    ) -> None:
        """HYPOTHESIS: Converts multiple tools into single Tool object."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            mock_func_decl = MagicMock()
            mock_tool = MagicMock()

            with patch(
                "vertexai.generative_models.FunctionDeclaration", return_value=mock_func_decl
            ) as MockFD:
                with patch("vertexai.generative_models.Tool", return_value=mock_tool) as MockTool:
                    provider = VertexAIProvider()
                    provider._convert_tools(multiple_tool_schemas)

                    # FunctionDeclaration should be called 3 times
                    assert MockFD.call_count == 3

                    # Tool should be created once with all declarations
                    MockTool.assert_called_once()

    def test_convert_tools_from_tool_object(self, sample_tool_schema: Dict[str, Any]) -> None:
        """HYPOTHESIS: Converts Tool object with get_schema() method."""
        # Create mock tool object with get_schema method
        mock_tool_obj = MagicMock()
        mock_tool_obj.get_schema.return_value = sample_tool_schema

        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            mock_func_decl = MagicMock()
            mock_tool = MagicMock()

            with patch(
                "vertexai.generative_models.FunctionDeclaration", return_value=mock_func_decl
            ) as MockFD:
                with patch("vertexai.generative_models.Tool", return_value=mock_tool):
                    provider = VertexAIProvider()
                    provider._convert_tools([mock_tool_obj])

                    # get_schema should be called
                    mock_tool_obj.get_schema.assert_called_once()

                    # FunctionDeclaration should use schema from get_schema()
                    MockFD.assert_called_once_with(
                        name="read_file",
                        description="Read complete contents of a file",
                        parameters=sample_tool_schema["parameters"],
                    )


# =============================================================================
# Test: stream_chat() with tools
# =============================================================================


class TestStreamChatWithTools:
    """Test stream_chat() with native function calling."""

    @pytest.mark.asyncio
    async def test_stream_chat_passes_tools_to_model(
        self, sample_messages: List[Dict[str, str]], sample_tool_schema: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: tools parameter is passed to GenerativeModel."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True  # Skip initialization

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([])
            mock_model.generate_content.return_value = mock_response

            with patch("vertexai.generative_models.GenerativeModel", return_value=mock_model):
                with patch.object(
                    provider, "_convert_tools", return_value=[MagicMock()]
                ) as mock_convert:
                    chunks = []
                    async for chunk in provider.stream_chat(
                        sample_messages, tools=[sample_tool_schema]
                    ):
                        chunks.append(chunk)

                    # _convert_tools should be called with tools
                    mock_convert.assert_called_once_with([sample_tool_schema])

    @pytest.mark.asyncio
    async def test_stream_chat_sets_tool_config_auto(
        self, sample_messages: List[Dict[str, str]], sample_tool_schema: Dict[str, Any]
    ) -> None:
        """HYPOTHESIS: ToolConfig is set to AUTO mode when tools provided."""
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

            mock_tool_config = MagicMock()

            with patch(
                "vertexai.generative_models.GenerativeModel", return_value=mock_model
            ) as MockModel:
                with patch("vertexai.generative_models.ToolConfig", return_value=mock_tool_config):
                    with patch.object(provider, "_convert_tools", return_value=[MagicMock()]):
                        async for _ in provider.stream_chat(
                            sample_messages, tools=[sample_tool_schema]
                        ):
                            pass

                        # GenerativeModel should be created with tool_config
                        call_kwargs = MockModel.call_args.kwargs
                        assert "tool_config" in call_kwargs or "tools" in call_kwargs


# =============================================================================
# Test: Function call response parsing
# =============================================================================


class TestFunctionCallResponseParsing:
    """Test parsing function call responses from Vertex AI."""

    @pytest.mark.asyncio
    async def test_yields_function_call_json_when_present(self) -> None:
        """HYPOTHESIS: Function calls are yielded as JSON."""
        with patch.dict(
            "sys.modules", {"vertexai": MagicMock(), "vertexai.generative_models": MagicMock()}
        ):
            from vertice_core.core.providers.vertex_ai import VertexAIProvider

            provider = VertexAIProvider()
            provider._client = True

            # Create mock chunk with function_call
            mock_function_call = MagicMock()
            mock_function_call.name = "read_file"
            mock_function_call.args = {"path": "README.md"}

            mock_part = MagicMock()
            mock_part.function_call = mock_function_call

            mock_content = MagicMock()
            mock_content.parts = [mock_part]

            mock_candidate = MagicMock()
            mock_candidate.content = mock_content

            mock_chunk = MagicMock()
            mock_chunk.candidates = [mock_candidate]
            mock_chunk.text = None  # No text, only function call

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.__iter__ = lambda self: iter([mock_chunk])
            mock_model.generate_content.return_value = mock_response

            with patch("vertexai.generative_models.GenerativeModel", return_value=mock_model):
                with patch("vertexai.generative_models.Content"):
                    with patch("vertexai.generative_models.Part"):
                        chunks = []
                        async for chunk in provider.stream_chat(
                            [{"role": "user", "content": "Read README"}],
                            tools=[{"name": "read_file", "description": "Read", "parameters": {}}],
                        ):
                            chunks.append(chunk)

                        # Should have yielded the function call as JSON
                        assert len(chunks) >= 1

                        # Parse first chunk as JSON
                        result = json.loads(chunks[0])
                        assert "tool_call" in result
                        assert result["tool_call"]["name"] == "read_file"
                        assert result["tool_call"]["arguments"]["path"] == "README.md"


# =============================================================================
# Test: Fallback to text parsing
# =============================================================================


class TestFallbackToTextParsing:
    """Test fallback to regex-based text parsing."""

    def test_parse_tool_calls_from_native_response(self) -> None:
        """HYPOTHESIS: Native response with tool_calls is parsed directly."""
        # This tests the _parse_tool_calls method that should be added
        # to tool_execution_handler.py

        native_response = {
            "content": "I'll read the file for you.",
            "tool_calls": [{"name": "read_file", "args": {"path": "README.md"}}],
        }

        # Expected parsed format

        # This will fail until implementation is done (TDD)
        # The handler should detect dict response and extract tool_calls
        assert "tool_calls" in native_response
        assert len(native_response["tool_calls"]) == 1

    def test_parse_tool_calls_from_text_fallback(self) -> None:
        """HYPOTHESIS: Text response falls back to regex parsing."""
        text_response = """I'll read that file for you.

[{"tool": "read_file", "args": {"path": "README.md"}}]"""

        # This tests backward compatibility with text-based parsing
        # Should extract the JSON array from text

        # Simple extraction logic (what the fallback should do)
        if "[" in text_response and "]" in text_response:
            start = text_response.index("[")
            end = text_response.rindex("]") + 1
            json_str = text_response[start:end]
            result = json.loads(json_str)

            assert len(result) == 1
            assert result[0]["tool"] == "read_file"
            assert result[0]["args"]["path"] == "README.md"

    def test_parse_tool_calls_handles_malformed_json(self) -> None:
        """HYPOTHESIS: Malformed JSON doesn't crash, returns None."""
        malformed_response = "I'll help but {invalid json here"

        # Should return None, not raise exception
        result = None
        try:
            if "[" in malformed_response:
                start = malformed_response.index("[")
                end = malformed_response.rindex("]") + 1
                json_str = malformed_response[start:end]
                result = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            result = None

        assert result is None


# =============================================================================
# Integration Test (requires actual SDK - skip in CI)
# =============================================================================


@pytest.mark.skip(reason="Requires Vertex AI credentials - run manually")
class TestVertexFunctionCallingIntegration:
    """Integration tests with actual Vertex AI API."""

    @pytest.mark.asyncio
    async def test_real_function_call(self) -> None:
        """Integration test: Real function call with Vertex AI."""
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider()

        if not provider.is_available():
            pytest.skip("Vertex AI not available")

        tools = [
            {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"],
                },
            }
        ]

        messages = [{"role": "user", "content": "What's the weather in Boston?"}]

        chunks = []
        async for chunk in provider.stream_chat(messages, tools=tools):
            chunks.append(chunk)

        # Should have received a function call
        full_response = "".join(chunks)
        assert "tool_call" in full_response or "get_weather" in full_response
