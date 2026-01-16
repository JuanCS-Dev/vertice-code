import pytest
import asyncio
import os
from pathlib import Path
from typing import Optional, List, Callable, Any, AsyncIterator
from textual.pilot import Pilot
from textual.widgets import Input

# Add src to python path for imports
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from vertice_tui.app import VerticeApp
from vertice_tui.widgets import ResponseView, StatusBar
from typing import AsyncIterator

from unittest.mock import MagicMock

from vertice_core.openresponses_stream import OpenResponsesStreamBuilder
from vertice_core.openresponses_types import TokenUsage


# Mock response generator using Open Responses protocol
async def mock_chat_generator(response_text: str) -> AsyncIterator[str]:
    """Yields Open Responses SSE events simulating streaming."""
    builder = OpenResponsesStreamBuilder(model="mock-gpt")

    # Initial events
    builder.start()
    for event in builder.get_events():
        yield event.to_sse()
    builder.clear_events()

    # Message item
    msg_item = builder.add_message()
    for event in builder.get_events():
        yield event.to_sse()
    builder.clear_events()

    # Streaming chunks
    chunk_size = 5
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i : i + chunk_size]
        builder.text_delta(msg_item, chunk)
        yield builder.get_last_event_sse()
        builder.clear_events()
        await asyncio.sleep(0.01)

    # Complete
    builder.complete(TokenUsage(input_tokens=10, output_tokens=len(response_text) // 4))
    for event in builder.get_events():
        yield event.to_sse()
    yield builder.done()


class MockBridge:
    """Mock bridge for E2E tests supporting Open Responses protocol."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.default_response = "I am a mock agent."
        self.called_with = []
        # Propriedades necessárias para o VerticeApp.on_mount
        self.prometheus_mode = False
        self.is_connected = True
        self._provider_mode = "auto"
        self.agents = type("MockAgents", (), {"available_agents": []})()
        self.tools = type("MockTools", (), {"get_tool_count": lambda: 0})()
        self.governance = type("MockGovernance", (), {"get_status_emoji": lambda: "🟢"})()
        self.history = type("MockHistory", (), {"clear_context": lambda self: None})()
        self.autocomplete = type(
            "MockAutocomplete", (), {"get_completions": lambda text, max_results=15: []}
        )()
        self.llm = type("MockLLM", (), {"_vertice_client": None})()

    def chat(self, request: str, stream: bool = True):
        self.called_with.append(request)
        response_text = self.responses.get(request, self.default_response)

        # If stream=True, we return the AsyncIterator of SSE events
        if stream:
            return mock_chat_generator(response_text)

        # For simple sync requests (if any), return the text or something else
        return response_text

    def is_ready(self):
        return True

    async def warmup(self):
        """Mock warmup method."""
        pass

    def cancel_all(self):
        """Mock cancel_all method."""
        pass

    def execute_custom_command(self, cmd_name, args):
        """Mock execute_custom_command method."""
        # Return None for unknown commands to let router handle them
        return None


class VerticeTUIHarness:
    """
    Test harness for Vertice TUI E2E tests.
    Abstracts interaction logic and provides high-level assertions.
    """

    def __init__(self, app: VerticeApp, pilot: Pilot):
        self.app = app
        self.pilot = pilot

    async def wait_for_ready(self, timeout: float = 5.0):
        """Wait for app to be ready (bridge connected or loaded)."""
        await self.pilot.pause(0.5)  # Wait for initial render

        # In real usage, we might wait for a specific status
        # For now, just ensuring no crash on startup
        assert self.app.is_running

    async def send_message(self, text: str, wait_for_response: bool = True):
        """Send a chat message and optionally wait for response completion."""
        await self.pilot.click("#prompt")
        await self.pilot.press(*list(text))
        await self.pilot.press("enter")

        if wait_for_response:
            await self.wait_for_processing_complete()

    async def send_command(self, command: str):
        """Send a slash command and wait for UI update."""
        await self.send_message(command, wait_for_response=False)
        # Commands like /help and /clear are sync but need a frame to mount/unmount widgets
        # Increased pause to 0.5s for stability
        await self.pilot.pause(0.5)
        if command not in ("/clear", "/help"):
            await self.wait_for_processing_complete()

    async def wait_for_processing_complete(self, timeout: float = 30.0):
        """Wait for the processing indicator to finish."""
        # Wait for status to become PROCESSING
        start = asyncio.get_running_loop().time()

        # Poll until MODE is READY
        while True:
            if asyncio.get_running_loop().time() - start > timeout:
                raise TimeoutError("Timeout waiting for processing to complete")

            try:
                status_bar = self.app.query_one(StatusBar)
                # If we are READY, we are done
                if status_bar.mode == "READY":
                    # Double check if response view has finished thinking
                    # await self.pilot.pause(0.1)
                    break
            except Exception:
                pass

            await asyncio.sleep(0.1)

    async def get_response_text(self) -> str:
        """Get the full text currently in the response view."""
        view = self.app.query_one(ResponseView)
        text_parts = []

        def _extract_text(obj: Any, depth: int = 0) -> str:
            if depth > 10:
                return ""  # Prevent infinite recursion
            if isinstance(obj, str):
                return obj

            # 1. Textual Static widgets - check content attribute first
            if hasattr(obj, "content"):
                content = obj.content
                if content is not obj:
                    return _extract_text(content, depth + 1)

            # 2. Content-bearing widgets or objects
            if hasattr(obj, "get_content") and callable(obj.get_content):
                return str(obj.get_content())
            if hasattr(obj, "plain") and isinstance(obj.plain, str):  # Core Rich Text
                return obj.plain
            if hasattr(obj, "markup") and not hasattr(obj, "render"):  # Core Markdown
                return str(obj.markup)

            # 3. Textual widgets - try renderable
            if hasattr(obj, "renderable"):
                renderable = obj.renderable
                if renderable is not obj:
                    return _extract_text(renderable, depth + 1)

            # 4. Try _renderable as fallback
            if hasattr(obj, "_renderable"):
                renderable = obj._renderable
                if renderable and renderable is not obj:
                    return _extract_text(renderable, depth + 1)

            # 5. Iterable renderables (Group)
            if hasattr(obj, "renderables"):
                return "\n".join(_extract_text(r, depth + 1) for r in obj.renderables)

            # 6. Fallback
            s = str(obj)
            if not s.startswith("<") or "object at" not in s:
                return s
            return ""

        for widget in view.query("*"):
            text = _extract_text(widget)
            if text.strip() and text not in text_parts:
                text_parts.append(text)

        full_text = "\n".join(text_parts).strip()
        return full_text

    async def expect_text(self, pattern: str, timeout: float = 5.0):
        """Assert that certain text eventually appears in the response."""
        start = asyncio.get_running_loop().time()
        while asyncio.get_running_loop().time() - start < timeout:
            text = await self.get_response_text()
            if pattern in text:
                return
            await asyncio.sleep(0.2)

        raise AssertionError(f"Pattern '{pattern}' not found in response text after {timeout}s")


@pytest.fixture
def mock_bridge():
    """Provides a MockBridge instance."""
    return MockBridge()


@pytest.fixture
async def app_instance(mock_bridge):
    """Provides a VerticeApp instance with mock bridge."""
    app = VerticeApp()
    app.bridge = mock_bridge
    return app


@pytest.fixture
async def tui_harness(app_instance):
    """Provides a VerticeTUIHarness instance for E2E testing."""
    async with app_instance.run_test() as pilot:
        harness = VerticeTUIHarness(app_instance, pilot)
        await harness.wait_for_ready()
        yield harness
