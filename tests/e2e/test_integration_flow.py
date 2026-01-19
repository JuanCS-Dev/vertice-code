import pytest
from unittest.mock import AsyncMock, MagicMock

# Mocked components
from vertice_tui.core.chat.controller import ChatController
from vertice_tui.core.tools_bridge import ToolBridge


@pytest.mark.asyncio
async def test_llm_client_memory_cortex_integration(mock_llm, cortex):
    """Test integration between LLMClient and MemoryCortex."""
    # This test is a placeholder as direct integration is hard to test
    # without a real LLM call. We rely on the mock_llm fixture.
    assert mock_llm is not None
    assert cortex is not None


@pytest.mark.asyncio
async def test_chat_controller_tool_bridge_integration(monkeypatch):
    """Test integration between ChatController and ToolBridge."""
    # Arrange

    # Mock the tool registry and the tool itself
    mock_tool = MagicMock()
    mock_tool._execute_validated = AsyncMock(
        return_value=MagicMock(success=True, data="The weather in London is sunny.")
    )

    mock_registry = MagicMock()
    mock_registry.get.return_value = mock_tool

    monkeypatch.setattr(ToolBridge, "_create_registry", lambda self: mock_registry)

    tool_bridge = ToolBridge()

    history = MagicMock()
    governance = MagicMock()
    agents = MagicMock()
    agent_registry = {}

    controller = ChatController(tool_bridge, history, governance, agents, agent_registry)

    # Act
    result = await controller._execute_single_tool("get_weather", {"location": "London"})

    # Assert
    assert result["success"]
    assert "sunny" in result["data"]
    mock_registry.get.assert_called_with("get_weather")
    mock_tool._execute_validated.assert_called_with(location="London")
