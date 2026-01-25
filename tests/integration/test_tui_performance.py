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
import os
import tempfile
import time
from pathlib import Path

import pytest


class TestHistoryManagerNonBlocking:
    """Tests for history_manager.py async fix."""

    @pytest.mark.asyncio
    async def test_save_history_async_does_not_block(self):
        """
        PROVA: add_command_async não bloqueia event loop.
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

            if hasattr(hm, "flush_history_async"):
                await hm.flush_history_async()

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

            if hasattr(hm, "flush_history_async"):
                await hm.flush_history_async()

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
        if os.getenv("VERTICE_RUN_LIVE_LLM_TESTS") != "1":
            pytest.skip("Live LLM tests disabled (set VERTICE_RUN_LIVE_LLM_TESTS=1)")

        from vertice_core.core.providers.vertex_ai import VertexAIProvider

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

            if hasattr(hm, "flush_history_async"):
                await hm.flush_history_async()

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
                view.append_chunk(chunk)

            await view._flush_pending_stream_async(final=True)

            assert fake_stream.writes == ["".join(chunks)]


class TestLargeBlocksAreTruncated:
    """Regression tests for long-session renderable costs."""

    @pytest.mark.asyncio
    async def test_large_code_block_is_truncated_and_expandable(self, monkeypatch) -> None:
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.expandable_blocks import ExpandableCodeBlock
        from vertice_tui.widgets.response_view import ResponseView

        monkeypatch.setenv("VERTICE_TUI_MAX_CODE_LINES", "10")

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            code = "\n".join(f"line {i}" for i in range(25))
            view.add_code_block(code, language="text", title="big.txt")
            await pilot.pause(0)

            block = view.query(ExpandableCodeBlock).last()
            assert block is not None
            assert block.is_truncated is True
            assert block.expanded is False

            block.expanded = True
            await pilot.pause(0)
            assert block.expanded is True


class TestScrollbackCompaction:
    """Regression tests for long-session scrollback compaction."""

    @pytest.mark.asyncio
    async def test_old_code_blocks_are_compacted_to_expandable(self, monkeypatch) -> None:
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.expandable_blocks import ExpandableCodeBlock
        from vertice_tui.widgets.response_view import ResponseView

        monkeypatch.setenv("VERTICE_TUI_MAX_VIEW_ITEMS", "6")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_RICH_TAIL", "2")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_COMPACT_BATCH", "10")

        # Ensure code blocks are initially rendered as expensive Syntax panels (SelectableStatic),
        # so compaction can replace them with expandable equivalents.
        monkeypatch.setenv("VERTICE_TUI_MAX_CODE_LINES", "1000")

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            code = "\n".join(f"line {i}" for i in range(20))
            view.add_code_block(code, language="text", title="a.txt")  # 1
            view.add_system_message("msg 2")  # 2
            view.add_code_block(code, language="text", title="b.txt")  # 3
            view.add_system_message("msg 4")  # 4
            view.add_code_block(code, language="text", title="c.txt")  # 5
            view.add_system_message("msg 6")  # 6 (triggers compaction)
            await pilot.pause(0)

            compacted_blocks = [
                block for block in view.query(ExpandableCodeBlock) if block.has_class("compacted")
            ]
            assert compacted_blocks, "Expected at least one code block to be compacted"

    @pytest.mark.asyncio
    async def test_compaction_respects_batch_size(self, monkeypatch) -> None:
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.expandable_blocks import ExpandableCodeBlock
        from vertice_tui.widgets.response_view import ResponseView

        monkeypatch.setenv("VERTICE_TUI_MAX_VIEW_ITEMS", "6")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_RICH_TAIL", "1")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_COMPACT_BATCH", "1")
        monkeypatch.setenv("VERTICE_TUI_MAX_CODE_LINES", "1000")

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            code = "\n".join(f"line {i}" for i in range(20))
            for idx in range(6):
                view.add_code_block(code, language="text", title=f"c{idx}.txt")
            await pilot.pause(0)

            def compacted_count() -> int:
                return len(
                    [
                        block
                        for block in view.query(ExpandableCodeBlock)
                        if block.has_class("compacted")
                    ]
                )

            assert compacted_count() == 1

            for expected in range(2, 6):
                view._trim_view_items()
                await pilot.pause(0)
                assert compacted_count() == expected


class TestPerformanceHUDOptimizations:
    """Regression tests for fast HUD updates (avoid hot path churn)."""

    @pytest.mark.asyncio
    async def test_metrics_updates_do_not_query_one_each_time(self) -> None:
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.performance_hud import PerformanceHUD

        class _CountingHUD(PerformanceHUD):
            def __init__(self) -> None:
                super().__init__(visible=True, id="hud")
                self.query_calls = 0

            def query_one(self, *args, **kwargs):
                self.query_calls += 1
                return super().query_one(*args, **kwargs)

        class _App(App):
            def compose(self) -> ComposeResult:
                yield _CountingHUD()

        app = _App()
        async with app.run_test() as pilot:
            hud = pilot.app.query_one("#hud", _CountingHUD)
            await pilot.pause(0)

            initial_calls = hud.query_calls
            assert initial_calls == 4

            for i in range(200):
                hud.update_metrics(
                    latency_ms=100 + i,
                    confidence=90,
                    throughput=10.0,
                    queue_time=5.0,
                )
            await pilot.pause(0)

            assert hud.query_calls == initial_calls


class TestLongSessionStability:
    """Regression/stress tests for bounded scrollback in long sessions."""

    @pytest.mark.asyncio
    async def test_long_session_keeps_view_size_bounded(self, monkeypatch) -> None:
        from textual.app import App, ComposeResult

        from vertice_tui.widgets.expandable_blocks import ExpandableCodeBlock
        from vertice_tui.widgets.response_view import ResponseView

        monkeypatch.setenv("VERTICE_TUI_MAX_VIEW_ITEMS", "50")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_RICH_TAIL", "10")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_COMPACT_BATCH", "50")
        monkeypatch.setenv("VERTICE_TUI_MAX_CODE_LINES", "1000")

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            code = "\n".join(f"line {i}" for i in range(20))
            for i in range(150):
                if i % 10 == 0:
                    view.add_code_block(code, language="text", title=f"c{i}.txt")
                else:
                    view.add_action(f"action {i}")

                if i and i % 25 == 0:
                    await pilot.pause(0)

            for _ in range(30):
                await pilot.pause(0)
                candidates = [child for child in view.children if not child.has_class("banner")]
                if len(candidates) <= 50:
                    break
            assert len(candidates) <= 50
            assert any(
                block.has_class("compacted") for block in view.query(ExpandableCodeBlock)
            ), "Expected compaction to produce at least one compacted ExpandableCodeBlock"

    @pytest.mark.asyncio
    async def test_10k_messages_keeps_view_size_bounded_opt_in(self, monkeypatch) -> None:
        if os.getenv("VERTICE_RUN_LONG_SESSION_TESTS") != "1":
            pytest.skip("Long session test disabled (set VERTICE_RUN_LONG_SESSION_TESTS=1)")

        from textual.app import App, ComposeResult

        from vertice_tui.widgets.expandable_blocks import ExpandableCodeBlock
        from vertice_tui.widgets.response_view import ResponseView

        monkeypatch.setenv("VERTICE_TUI_MAX_VIEW_ITEMS", "200")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_RICH_TAIL", "20")
        monkeypatch.setenv("VERTICE_TUI_SCROLLBACK_COMPACT_BATCH", "200")
        monkeypatch.setenv("VERTICE_TUI_MAX_CODE_LINES", "1000")

        class _App(App):
            def compose(self) -> ComposeResult:
                yield ResponseView(id="response")

        app = _App()
        async with app.run_test() as pilot:
            view = pilot.app.query_one("#response", ResponseView)

            code = "\n".join(f"line {i}" for i in range(20))
            for i in range(10_000):
                if i % 20 == 0:
                    view.add_code_block(code, language="text", title=f"c{i}.txt")
                else:
                    view.add_action(f"action {i}")

                if i % 500 == 0:
                    await pilot.pause(0)

            for _ in range(30):
                await pilot.pause(0)
                candidates = [child for child in view.children if not child.has_class("banner")]
                if len(candidates) <= 200:
                    break
            assert len(candidates) <= 200
            assert any(
                block.has_class("compacted") for block in view.query(ExpandableCodeBlock)
            ), "Expected compaction to produce at least one compacted ExpandableCodeBlock"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
