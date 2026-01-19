import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add src to path to ensure imports work
sys.path.insert(0, os.path.abspath("src"))

try:
    from vertice_tui.app import VerticeApp
    from vertice_tui.core.chat.controller import ChatController
    from vertice_tui.core.tools_bridge import ToolBridge
except ImportError:
    # Should not happen now if src exists
    VerticeApp = None
    ChatController = None
    ToolBridge = None


@pytest.fixture
def mock_tool_bridge():
    """Returns a mocked ToolBridge."""
    bridge = MagicMock(spec=ToolBridge)
    bridge.get_tool_count.return_value = 10
    bridge.execute_tool = AsyncMock(return_value={"success": True, "data": "mock_result"})
    # Ensure tool schemas return valid structure
    bridge.get_schemas_for_llm.return_value = [{"name": "mock_tool", "description": "A mock tool"}]
    return bridge


@pytest.fixture
def headless_controller(mock_tool_bridge):
    """Returns a ChatController initialized with mocks for headless testing."""
    if not ChatController:
        pytest.skip("Vertice TUI modules not available")

    # Mock the App interaction
    mock_app = MagicMock()

    # Initialize controller with mandatory dependencies
    # tools, history, governance, agents, agent_registry
    controller = ChatController(
        tools=mock_tool_bridge,
        history=MagicMock(),
        governance=MagicMock(),
        agents=MagicMock(),
        agent_registry=MagicMock(),
    )
    controller.app = mock_app

    # Mock LLM interaction
    controller.llm = AsyncMock()

    # Mock stream response
    async def mock_stream(*args, **kwargs):
        yield "Thinking process...\n"
        yield "Final answer."

    controller.llm.stream = mock_stream

    return controller
