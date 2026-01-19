import pytest
from textual.widgets import Input


@pytest.mark.asyncio
async def test_app_startup(tui_harness_ctx):
    """Verify that the app starts up without errors."""
    async with tui_harness_ctx() as tui_harness:
        assert tui_harness.app.is_running
        # Optional: check if prompt is focused
        assert tui_harness.app.query_one(Input).has_focus


@pytest.mark.asyncio
async def test_chat_interaction(tui_harness_ctx, mock_bridge):
    """Test sending a message and receiving a response."""
    # Configure mock response
    mock_bridge.responses["Hello TUI"] = "Greetings human!"

    async with tui_harness_ctx() as tui_harness:
        await tui_harness.send_message("Hello TUI")

        # Check if mock bridge was called
        assert "Hello TUI" in mock_bridge.called_with

        # Check response in UI
        response_text = await tui_harness.get_response_text()
        assert "Greetings human!" in response_text
        # Also user message should be there
        assert "Hello TUI" in response_text


@pytest.mark.asyncio
async def test_help_command(tui_harness_ctx):
    """Test the /help command."""
    async with tui_harness_ctx() as tui_harness:
        await tui_harness.send_command("/help")

        response_text = await tui_harness.get_response_text()
        # Help prints available commands or topics (in Portuguese in this app)
        assert any(
            s in response_text
            for s in ["Available commands", "Usage", "Navegue pelos tópicos", "Comandos"]
        )
        assert "/help commands" in response_text or "/clear" in response_text


@pytest.mark.asyncio
async def test_clear_command(tui_harness_ctx):
    """Test the /clear command."""
    async with tui_harness_ctx() as tui_harness:
        # First generate some content
        await tui_harness.send_message("Noise")
        content_before = await tui_harness.get_response_text()
        assert "Noise" in content_before

        # Clear it (force to skip confirmation dialog)
        await tui_harness.send_command("/clear --force")

        # Check if cleared
        content_after = await tui_harness.get_response_text()
        # Depending on implementation, clear might leave a system message or be empty
        # But "Noise" should be gone
        assert "Noise" not in content_after


@pytest.mark.asyncio
async def test_unknown_command(tui_harness_ctx):
    """Test functionality for unknown commands."""
    async with tui_harness_ctx() as tui_harness:
        await tui_harness.send_command("/gibberish")

        response_text = await tui_harness.get_response_text()
        assert "Unknown command" in response_text
