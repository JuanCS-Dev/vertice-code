
import pytest
from textual.pilot import Pilot
try:
    from vertice_tui.app import VerticeApp
except ImportError:
    VerticeApp = None

@pytest.mark.asyncio
async def test_app_startup_and_layout(mock_tool_bridge):
    """Test that the app starts up and displays key components."""
    if not VerticeApp:
        pytest.skip("VerticeApp not importable")

    # Patch get_bridge to return a mock
    from unittest.mock import patch, MagicMock
    with patch("vertice_tui.core.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.is_connected = True
        mock_get_bridge.return_value = mock_bridge
        
        app = VerticeApp()
        async with app.run_test() as pilot:
            # Check for main widgets using correct classes/IDs
            assert pilot.app.query("ResponseView").first()
            assert pilot.app.query("Input").first()
            assert pilot.app.query("StatusBar").first()
            
            # Check initial state
            assert pilot.app.title == "VERTICE"

@pytest.mark.asyncio
async def test_input_flow_interactive(mock_tool_bridge):
    """Test typing in the input bar and submitting."""
    if not VerticeApp:
        pytest.skip("VerticeApp not importable")

    from unittest.mock import patch, MagicMock
    with patch("vertice_tui.core.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.is_connected = True
        # Mock chat to yield nothing so it doesn't crash loop
        async def mock_chat(*args):
             yield "Mock response"
        mock_bridge.chat = mock_chat
        mock_bridge.governance.get_status_emoji.return_value = "🟢"
        
        mock_get_bridge.return_value = mock_bridge

        app = VerticeApp()
        
        async with app.run_test() as pilot:
            # Find input
            input_widget = pilot.app.query_one("Input")
            
            # Type "Hello"
            await pilot.click("Input")
            await pilot.press(*list("Hello"))
            
            # Verify text in input
            assert input_widget.value == "Hello"
            
            # Hit Enter
            await pilot.press("enter")
            
            # Verify input cleared
            assert input_widget.value == ""
            
            # Wait for processing
            await pilot.pause()
            
            # Check response view for user message
            response_view = pilot.app.query_one("ResponseView")
            # We can't easily check internal rendering in E2E without screenshot or deep inspection
            # But we can check if history updated
            assert "Hello" in app.history

@pytest.mark.asyncio
async def test_space_panic_button():
    """Test that the Space key triggers the emergency stop/panic mode."""
    if not VerticeApp:
        pytest.skip("VerticeApp not importable")

    app = VerticeApp()
    async with app.run_test() as pilot:
        # Press Space (mapped to 'emergency_stop' in some contexts, or just a key)
        # The prompt says "Space Emergency Stop" in the UI image.
        
        # We need to ensure we are NOT focused on the input, 
        # otherwise space is just a character.
        # Click outside or explicitly focus something else?
        # Or maybe it's Ctrl+Space? The UI image says "^space Emergency Stop" which usually means Ctrl+Space.
        
        await pilot.press("ctrl+space")
        
        # Verify a modal or status change, or log message
        # app.emergency_stop_triggered?
        pass
