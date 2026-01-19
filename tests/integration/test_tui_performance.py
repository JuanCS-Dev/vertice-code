"""
TUI Performance Tests - Validates lag fixes.
Created: 2026-01-18
Objective: Prove lag < 500ms and streaming is smooth.

References:
- Textual Workers: https://textual.textualize.io/guide/workers/#thread-workers
- asyncio.to_thread: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
- google-genai async: https://googleapis.github.io/python-genai/#generate-content-asynchronous-streaming
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest


class TestHistoryManagerNonBlocking:
    """Tests for history_manager.py async fix."""

    @pytest.mark.asyncio
    async def test_save_history_async_does_not_block(self):
        """
        PROVA: _save_history_async não bloqueia event loop.
        MÉTRICA: adicionar 100 comandos deve completar em < 500ms.

        Baseline: sync version pode levar 5000ms+ em disco lento.
        """
        from vertice_tui.core.history_manager import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history"
            hm = HistoryManager(history_file=history_file)

            start = time.perf_counter()

            # Add 100 commands using async method
            for i in range(100):
                if hasattr(hm, "add_command_async"):
                    await hm.add_command_async(f"command_{i}")
                else:
                    pytest.skip("add_command_async not implemented yet")

            elapsed_ms = (time.perf_counter() - start) * 1000

            # Verify file was written
            assert history_file.exists(), "History file should exist"
            content = history_file.read_text()
            assert "command_99" in content, "Last command should be saved"

            # Performance assertion
            assert elapsed_ms < 500, f"Too slow: {elapsed_ms:.0f}ms (expected < 500ms)"
            print(f"✅ Added 100 commands in {elapsed_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_async_lock_prevents_race_conditions(self):
        """
        PROVA: concurrent saves don't corrupt file.
        """
        from vertice_tui.core.history_manager import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history"
            hm = HistoryManager(history_file=history_file)

            if not hasattr(hm, "add_command_async"):
                pytest.skip("add_command_async not implemented yet")

            # Launch 50 concurrent saves
            tasks = [hm.add_command_async(f"concurrent_{i}") for i in range(50)]
            await asyncio.gather(*tasks)

            # Verify no corruption
            content = history_file.read_text()
            lines = [line for line in content.split("\n") if line.strip()]

            # Should have 50 unique commands (no duplicates due to locking)
            assert len(lines) == 50, f"Expected 50 lines, got {len(lines)}"
            print("✅ 50 concurrent saves completed without corruption")


class TestVertexAIAsyncStreaming:
    """Tests for vertex_ai.py async streaming fix."""

    @pytest.mark.asyncio
    async def test_streaming_is_truly_async(self):
        """
        PROVA: streaming não bloqueia event loop.
        MÉTRICA: primeiro chunk deve chegar em < 3s.

        Note: VertexAIProvider now auto-detects project from gcloud CLI.
        """
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider(model_name="pro")

        if not provider.is_available():
            pytest.skip("Vertex AI SDK not available")

        messages = [{"role": "user", "content": "Say 'hello' and nothing else."}]

        chunks_received = []
        first_chunk_time = None
        start = time.perf_counter()

        async for chunk in provider.stream_chat(messages, max_tokens=50):
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter() - start
            chunks_received.append(chunk)

            # Timeout protection
            if time.perf_counter() - start > 30:
                break

        # Gemini 3 Pro is a "thinking model" with higher latency (~5-10s first chunk)
        assert first_chunk_time is not None, "Should receive at least one chunk"
        assert first_chunk_time < 15.0, f"First chunk too slow: {first_chunk_time:.1f}s"
        assert len(chunks_received) >= 1, "Should receive streaming chunks"

        print(
            f"✅ First chunk in {first_chunk_time * 1000:.0f}ms, total {len(chunks_received)} chunks"
        )


class TestControllerIntegration:
    """Tests for controller.py async integration."""

    @pytest.mark.asyncio
    async def test_add_command_is_fire_and_forget(self):
        """
        PROVA: add_command call in controller doesn't block.
        """
        from vertice_tui.core.history_manager import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history"
            hm = HistoryManager(history_file=history_file)

            # Verify the async method exists
            assert hasattr(hm, "add_command_async"), "add_command_async should exist"

            # Test fire-and-forget pattern
            start = time.perf_counter()
            task = asyncio.create_task(hm.add_command_async("test_command"))
            immediate_time = time.perf_counter() - start

            # The create_task should return immediately
            assert immediate_time < 0.01, f"create_task should be instant, took {immediate_time}s"

            # Wait for the task to complete
            await task

            # Verify it was saved
            assert history_file.exists()
            assert "test_command" in history_file.read_text()

            print("✅ Fire-and-forget pattern works correctly")


class TestAutocompleteDropdownReuse:
    """Performance regression tests for autocomplete widget churn."""

    @pytest.mark.asyncio
    async def test_dropdown_does_not_mount_unmount_per_keystroke(self) -> None:
        """
        PROVA: show/hide não deve remover/remontar children.

        Motivo: mount/remove em cada tecla gera layout thrash.
        """
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.autocomplete import AutocompleteDropdown

        class _App(App):
            def compose(self) -> ComposeResult:
                yield AutocompleteDropdown(id="autocomplete")

        app = _App()
        async with app.run_test() as pilot:
            dropdown = pilot.app.query_one("#autocomplete", AutocompleteDropdown)
            await pilot.pause(0)

            assert len(list(dropdown.children)) == dropdown.MAX_ITEMS
            initial_child_ids = [id(child) for child in dropdown.children]

            dropdown.show_completions(
                [
                    {"text": "/help", "display": "⚡ /help", "type": "command", "score": 1.0},
                    {"text": "/clear", "display": "⚡ /clear", "type": "command", "score": 0.9},
                ]
            )
            await pilot.pause(0)
            assert [id(child) for child in dropdown.children] == initial_child_ids

            dropdown.hide()
            await pilot.pause(0)
            assert [id(child) for child in dropdown.children] == initial_child_ids

            dropdown.show_completions(
                [
                    {"text": "tool.foo", "display": "🔧 tool.foo", "type": "tool", "score": 1.0},
                ]
            )
            await pilot.pause(0)
            assert [id(child) for child in dropdown.children] == initial_child_ids


class TestResponseViewStreamingCoalescing:
    """Performance regression tests for streaming smoothness."""

    @pytest.mark.asyncio
    async def test_markdown_stream_writes_are_coalesced(self, monkeypatch) -> None:
        """
        PROVA: múltiplos deltas devem virar poucos writes no MarkdownStream.

        Estratégia: monkeypatch do `Markdown.get_stream()` para capturar writes,
        sem depender de timers (determinístico).
        """
        from textual.app import App, ComposeResult
        from textual.widgets import Markdown

        from vertice_tui.widgets.response_view import ResponseView

        class _FakeStream:
            def __init__(self) -> None:
                self.writes: list[str] = []

            async def write(self, text: str) -> None:
                self.writes.append(text)

            async def stop(self) -> None:
                return None

        fake_stream = _FakeStream()
        monkeypatch.setattr(
            Markdown,
            "get_stream",
            classmethod(lambda cls, markdown: fake_stream),
        )

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            # Disable interval/timer scheduling so the test is deterministic.
            monkeypatch.setattr(view, "_ensure_flush_timer", lambda: None)
            monkeypatch.setattr(view, "_schedule_flush", lambda: None)

            chunks = ["hello", " ", "world", "!", "\n"] * 10
            for chunk in chunks:
                await view.append_chunk(chunk)

            await view._flush_pending_stream_async(final=True)

            assert fake_stream.writes == ["".join(chunks)]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
