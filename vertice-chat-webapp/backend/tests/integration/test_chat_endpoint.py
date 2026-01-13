"""
Integration tests for Chat API

Tests the full request/response cycle with mocked Vertex AI.
Updated 2026-01-13 to use Vertex AI instead of Anthropic.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

# Set environment before importing app
os.environ["ENVIRONMENT"] = "development"
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"

from app.main import app

client = TestClient(app)


@pytest.fixture
def dev_auth_headers():
    """Development authentication headers using dev-token."""
    return {"Authorization": "Bearer dev-token"}


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer mock-jwt-token"}


class MockChunk:
    """Mock Vertex AI stream chunk."""
    def __init__(self, text: str):
        self._text = text
    
    @property
    def text(self):
        return self._text


class MockAsyncIterator:
    """Mock async iterator for streaming responses."""
    def __init__(self, chunks):
        self.chunks = chunks
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


def create_mock_vertex_model():
    """Create a mock GenerativeModel with chat capabilities."""
    mock_model = MagicMock()
    mock_chat = MagicMock()
    
    # Mock streaming response
    async def mock_send_message_async(message, stream=False):
        chunks = [MockChunk("Hello"), MockChunk(" world"), MockChunk("!")]
        return MockAsyncIterator(chunks)
    
    mock_chat.send_message_async = mock_send_message_async
    mock_model.start_chat.return_value = mock_chat
    
    return mock_model


@patch("app.api.v1.chat.vertexai")
@patch("app.api.v1.chat.GenerativeModel")
@pytest.mark.asyncio
async def test_chat_stream_endpoint(mock_gen_model, mock_vertexai, dev_auth_headers):
    """Test SSE streaming endpoint with Vercel AI SDK Data Stream Protocol."""
    
    # Setup mocks
    mock_vertexai.init = MagicMock()
    mock_gen_model.return_value = create_mock_vertex_model()
    
    # Make request
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        },
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 200
    
    # Verify content type (Vercel AI SDK expects text/plain)
    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type, f"Expected text/plain, got {content_type}"
    
    # Parse response and verify Data Stream Protocol format
    content = response.text
    lines = [line for line in content.strip().split("\n") if line]
    
    # Should have text chunks (0:) and finish signal (d:)
    text_chunks = [line for line in lines if line.startswith("0:")]
    finish_lines = [line for line in lines if line.startswith("d:")]
    
    assert len(text_chunks) >= 1, f"Expected text chunks, got: {content}"
    assert len(finish_lines) == 1, f"Expected finish signal, got: {content}"
    assert '"finishReason"' in finish_lines[0]


@patch("app.api.v1.chat.vertexai")
@patch("app.api.v1.chat.GenerativeModel")
@pytest.mark.asyncio
async def test_chat_with_conversation_history(mock_gen_model, mock_vertexai, dev_auth_headers):
    """Test chat preserves conversation history."""
    
    mock_vertexai.init = MagicMock()
    mock_model = create_mock_vertex_model()
    mock_gen_model.return_value = mock_model
    
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [
                {"role": "user", "content": "My name is Juan"},
                {"role": "assistant", "content": "Nice to meet you, Juan!"},
                {"role": "user", "content": "What is my name?"},
            ],
            "stream": True,
        },
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 200
    
    # Verify start_chat was called (which receives history)
    mock_model.start_chat.assert_called_once()
    call_args = mock_model.start_chat.call_args
    history = call_args.kwargs.get("history", [])
    
    # Should have 2 messages in history (excluding the last user message)
    assert len(history) == 2


@pytest.mark.asyncio
async def test_chat_unauthenticated():
    """Test that unauthenticated requests are rejected."""
    
    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_chat_empty_messages(dev_auth_headers):
    """Test validation of empty messages array."""
    
    response = client.post(
        "/api/v1/chat",
        json={"messages": []},
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_chat_invalid_input(dev_auth_headers):
    """Test validation of malformed input."""
    
    response = client.post(
        "/api/v1/chat",
        json={"invalid": "input"},
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 422  # Validation error


@patch("app.api.v1.chat.vertexai")
@patch("app.api.v1.chat.GenerativeModel")
@pytest.mark.asyncio
async def test_chat_model_fallback(mock_gen_model, mock_vertexai, dev_auth_headers):
    """Test that model fallback works when primary model fails."""
    
    mock_vertexai.init = MagicMock()
    
    # First call fails, second succeeds
    call_count = [0]
    def side_effect(model_name):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("Model not available")
        return create_mock_vertex_model()
    
    mock_gen_model.side_effect = side_effect
    
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        },
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 200
    assert call_count[0] >= 2  # Should have tried fallback


@patch("app.api.v1.chat.vertexai")
@patch("app.api.v1.chat.GenerativeModel")
@pytest.mark.asyncio
async def test_chat_stream_error_handling(mock_gen_model, mock_vertexai, dev_auth_headers):
    """Test error handling during streaming."""
    
    mock_vertexai.init = MagicMock()
    mock_model = MagicMock()
    mock_chat = MagicMock()
    
    # Mock streaming that raises an error
    async def mock_send_error(message, stream=False):
        raise Exception("Vertex AI error")
    
    mock_chat.send_message_async = mock_send_error
    mock_model.start_chat.return_value = mock_chat
    mock_gen_model.return_value = mock_model
    
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        },
        headers=dev_auth_headers,
    )
    
    assert response.status_code == 200  # Stream starts before error
    
    # Error should be in response as 3:"error" format
    content = response.text
    assert "3:" in content or "error" in content.lower()


@pytest.mark.asyncio
async def test_health_requires_no_auth():
    """Test that main health endpoint is public."""
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

