import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.architect.reasoning_engine_app import ArchitectReasoningEngineApp
from agents.reviewer.reasoning_engine_app import ReviewerReasoningEngineApp


@pytest.fixture
def mock_vertex_ai_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="Mocked response")
    return provider


@pytest.mark.asyncio
async def test_architect_reasoning_engine_app_query_contract(mock_vertex_ai_provider):
    app = ArchitectReasoningEngineApp()
    app._provider = mock_vertex_ai_provider

    # Test str input
    resp = await app.query(input="Design a billing system")
    assert "output" in resp
    assert mock_vertex_ai_provider.generate.called

    # Test dict input
    resp = await app.query(input={"description": "Design a billing system"})
    assert "output" in resp


@pytest.mark.asyncio
async def test_reviewer_reasoning_engine_app_query_contract(mock_vertex_ai_provider):
    app = ReviewerReasoningEngineApp()
    app._provider = mock_vertex_ai_provider

    # Test str input
    resp = await app.query(input="Review this: print('hello')")
    assert "output" in resp

    # Test dict input (code field)
    resp = await app.query(input={"code": "print('hello')"})
    assert "output" in resp
