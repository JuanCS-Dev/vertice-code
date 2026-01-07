"""
Integration tests for Chat API

Tests the full request/response cycle with mocked LLM
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test_token"}


@patch("app.api.v1.chat.anthropic_client")
@pytest.mark.asyncio
async def test_chat_stream_endpoint(mock_anthropic, auth_headers):
    """Test SSE streaming endpoint"""

    # Mock Anthropic response
    mock_stream = AsyncMock()
    mock_stream.__aenter__.return_value.events = [
        {"type": "content_block_delta", "delta": {"text": "Hello"}},
        {"type": "content_block_delta", "delta": {"text": " world"}},
    ]

    mock_anthropic.messages.stream.return_value = mock_stream

    # Make request
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Parse SSE events
    events = []
    for line in response.iter_lines():
        line_str = line.decode("utf-8") if isinstance(line, bytes) else line
        if line_str.startswith("data:"):
            events.append(line_str[5:])  # Remove "data:" prefix

    assert len(events) >= 2


@patch("app.api.v1.chat.anthropic_client")
@pytest.mark.asyncio
async def test_chat_non_stream_endpoint(mock_anthropic, auth_headers):
    """Test regular (non-streaming) chat endpoint"""

    # Mock Anthropic response
    mock_response = AsyncMock()
    mock_response.content = [{"text": "Hello, how can I help you?"}]
    mock_response.usage = {"input_tokens": 10, "output_tokens": 8}

    mock_anthropic.messages.create.return_value = mock_response

    # Make request
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "content" in data
    assert "usage" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_chat_unauthenticated():
    """Test that unauthenticated requests are rejected"""

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_invalid_input():
    """Test validation of malformed input"""

    response = client.post(
        "/api/v1/chat",
        json={"invalid": "input"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 422  # Validation error


@patch("app.api.v1.chat.anthropic_client")
@pytest.mark.asyncio
async def test_chat_with_artifacts(mock_anthropic, auth_headers):
    """Test chat with artifact context"""

    # Mock response
    mock_response = AsyncMock()
    mock_response.content = [{"text": "I see you're working on a React component."}]
    mock_response.usage = {"input_tokens": 100, "output_tokens": 15}

    mock_anthropic.messages.create.return_value = mock_response

    # Make request with artifact context
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Help me with this code"}],
            "artifacts": ["artifact-123"],
            "stream": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "content" in data
    assert data["content"] is not None
