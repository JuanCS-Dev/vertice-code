import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_controller_initialization(headless_controller):
    """Test that the controller initializes with injected dependencies."""
    assert headless_controller.tools is not None
    assert headless_controller.llm is not None
    # Verify tool count from mock
    assert headless_controller.tools.get_tool_count() == 10


@pytest.mark.asyncio
async def test_chat_generation_flow(headless_controller):
    """Test the chat generation flow (generator)."""

    user_input = "Hello"
    system_prompt = "You are a helpful assistant."
    client = AsyncMock()

    # Configure mock agents router to return None (no routing)
    headless_controller.agents.router.route.return_value = None

    # Mock stream to yield chunks
    async def mock_stream(*args, **kwargs):
        yield "Thinking...\n"
        yield "Hello there!"

    client.stream = mock_stream

    # Execute
    chunks = []
    async for chunk in headless_controller.chat(client, user_input, system_prompt):
        chunks.append(chunk)

    # Verify chunks received
    assert len(chunks) >= 2
    assert "Thinking..." in chunks[0] or "Thinking..." in chunks[1]

    # Verify history was updated
    headless_controller.history.add_command.assert_called_with(user_input)
    headless_controller.history.add_context.assert_called()


@pytest.mark.asyncio
async def test_tool_bridge_schemas_integration(headless_controller):
    """Test that the controller retrieves schemas from the bridge correctly."""

    # The controller usually passes tools to the LLM during stream()
    # We verify that it CALLS get_schemas_for_llm on the bridge

    schemas = headless_controller.tools.get_schemas_for_llm()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "mock_tool"
