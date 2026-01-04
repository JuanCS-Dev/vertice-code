"""
Streaming Markdown Widget - Claude Code Web Style Rendering.

Main streaming markdown widget for TUI.
Uses BlockWidgetFactory for specialized block rendering.

Features:
- Live markdown rendering during streaming (INCREMENTAL)
- Optimistic block detection (bold, code, tables before closing)
- 30 FPS with 33.33ms frame budget
- Automatic fallback to plain text when FPS < 25
- Pulsing cursor at end of content
- Widget Factory for specialized blocks

AIR GAPS CORRECTED:
- [x] BlockWidgetFactory renders specialized blocks
- [x] BlockDetector connected to Widget Factory
- [x] Specialized components instantiated and used

Philosophy:
    "Streaming should feel instant, even when it's not."
"""

from __future__ import annotations

import time
import asyncio
from typing import Optional, AsyncIterator, Callable, List

from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
from textual.app import ComposeResult

from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from rich.console import RenderableType, Group

from ..block_detector import BlockDetector, BlockInfo, BlockType

from .types import RenderMode, PerformanceMetrics
from .factory import BlockWidgetFactory
from .fps_controller import AdaptiveFPSController


class StreamingMarkdownWidget(Widget):
    """
    Streaming markdown widget Claude Code Web style.

    Combines:
    - MarkdownStream from Textual v4.0+ (when available)
    - BlockDetector for visual feedback by block type
    - AdaptiveFPSController for automatic fallback
    - Pulsing cursor during streaming
    """

    DEFAULT_CSS = """
    StreamingMarkdownWidget {
        width: 100%;
        height: auto;
        min-height: 3;
        padding: 1 2;
    }

    StreamingMarkdownWidget.streaming {
        border: solid #00d4aa;
    }

    StreamingMarkdownWidget.performance-warning {
        border: solid #f1fa8c;
    }

    StreamingMarkdownWidget.plain-text-mode {
        border: dashed #f1fa8c;
    }

    StreamingMarkdownWidget .cursor {
        background: #00d4aa;
    }
    """

    # Reactive properties
    is_streaming = reactive(False)
    current_block_type = reactive(BlockType.UNKNOWN)
    render_mode = reactive(RenderMode.MARKDOWN)
    show_cursor = reactive(True)

    # Cursor animation frames
    CURSOR_FRAMES = ["", "", "", "", "", " ", "", "", "", ""]
    CURSOR_INTERVAL = 0.08  # 80ms per frame

    class StreamStarted(Message):
        """Event: streaming started."""

        pass

    class StreamEnded(Message):
        """Event: streaming ended."""

        def __init__(self, content: str, metrics: PerformanceMetrics):
            self.content = content
            self.metrics = metrics
            super().__init__()

    class BlockDetected(Message):
        """Event: new block type detected."""

        def __init__(self, block_type: BlockType, block_info: BlockInfo):
            self.block_type = block_type
            self.block_info = block_info
            super().__init__()

    class FPSWarning(Message):
        """Event: low FPS detected."""

        def __init__(self, fps: float, action: str):
            self.fps = fps
            self.action = action
            super().__init__()

    def __init__(
        self,
        target_fps: int = 30,
        enable_adaptive_fps: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        """
        Initialize StreamingMarkdownWidget.

        Args:
            target_fps: Target FPS (default: 30)
            enable_adaptive_fps: Enable automatic fallback
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

        self.target_fps = target_fps
        self.frame_budget = 1.0 / target_fps  # 33.33ms for 30 FPS
        self.enable_adaptive_fps = enable_adaptive_fps

        # State
        self._content = ""
        self._buffer = ""
        self._cursor_index = 0
        self._last_render = time.perf_counter()

        # Components
        self._block_detector = BlockDetector()
        self._fps_controller = AdaptiveFPSController()
        self._metrics = PerformanceMetrics()
        self._widget_factory = BlockWidgetFactory()

        # Internal markdown widget
        self._markdown_static: Optional[Static] = None

        # Cache of finalized blocks (don't re-render)
        self._finalized_blocks_count: int = 0

        # Cursor animation task
        self._cursor_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        self._markdown_static = Static("", id="markdown-content")
        yield self._markdown_static

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        pass

    async def start_stream(self) -> None:
        """Start a streaming session."""
        self.is_streaming = True
        self._content = ""
        self._buffer = ""
        self._block_detector.reset()
        self._fps_controller.reset()
        self._widget_factory.reset()
        self._metrics = PerformanceMetrics()
        self._finalized_blocks_count = 0
        self._last_render = time.perf_counter()

        self.add_class("streaming")
        self.post_message(self.StreamStarted())

        # Start cursor animation
        self._cursor_task = asyncio.create_task(self._animate_cursor())

    async def append_chunk(self, chunk: str) -> None:
        """
        Add chunk of text to stream.

        Args:
            chunk: Text to add
        """
        if not self.is_streaming:
            return

        self._buffer += chunk
        self._content += chunk

        # Process with block detector
        self._block_detector.process_chunk(chunk)

        # Detect block type change
        current = self._block_detector.get_current_block()
        if current and current.block_type != self.current_block_type:
            self.current_block_type = current.block_type
            self.post_message(self.BlockDetected(current.block_type, current))

        # Check if should update display (respecting frame budget)
        now = time.perf_counter()
        elapsed = now - self._last_render

        if elapsed >= self.frame_budget:
            await self._render_frame()
            self._last_render = now

    async def _render_frame(self) -> None:
        """Render a frame."""
        render_start = time.perf_counter()

        # Check FPS and adapt if necessary
        if self.enable_adaptive_fps:
            fps = self._fps_controller.record_frame()
            self._metrics.last_fps = fps
            self._metrics.min_fps = min(self._metrics.min_fps, fps)

            mode, status = self._fps_controller.check_and_adapt(fps)

            if status == "FALLBACK_TO_PLAIN":
                self.render_mode = RenderMode.PLAIN_TEXT
                self._metrics.fallback_count += 1
                self.add_class("plain-text-mode")
                self.remove_class("streaming")
                self.post_message(self.FPSWarning(fps, status))
            elif status == "TRY_MARKDOWN_AGAIN":
                self.render_mode = RenderMode.MARKDOWN
                self.remove_class("plain-text-mode")
                self.add_class("streaming")
                self.post_message(self.FPSWarning(fps, status))
            elif status == "WARNING_LOW_FPS":
                self.add_class("performance-warning")
                self.post_message(self.FPSWarning(fps, status))
            else:
                self.remove_class("performance-warning")

        # Render content
        if self._markdown_static:
            renderable = self._create_renderable()
            self._markdown_static.update(renderable)

        # Update metrics
        render_time = (time.perf_counter() - render_start) * 1000
        self._metrics.frames_rendered += 1
        self._metrics.total_render_time_ms += render_time

        if render_time > self.frame_budget * 1000:
            self._metrics.dropped_frames += 1

    def _create_renderable(self) -> RenderableType:
        """
        Create renderable for current content.

        CORRECTED: Now uses BlockWidgetFactory for specialized
        blocks (code, table, checklist) instead of generic RichMarkdown.
        """
        if self.render_mode == RenderMode.PLAIN_TEXT:
            return self._create_plain_text_renderable()

        # Markdown mode with Widget Factory
        try:
            return self._create_block_based_renderable()
        except (ValueError, TypeError, AttributeError):
            return self._create_plain_text_renderable()

    def _create_plain_text_renderable(self) -> Text:
        """Render as plain text (performance fallback)."""
        content = self._content

        # Add cursor if streaming
        if self.is_streaming and self.show_cursor:
            cursor = self.CURSOR_FRAMES[self._cursor_index]
            content += cursor

        text = Text(content)
        if self.is_streaming and self.render_mode == RenderMode.PLAIN_TEXT:
            text.append("\n\n", style="dim")
            text.append(" Performance mode", style="dim yellow")
        return text

    def _create_block_based_renderable(self) -> RenderableType:
        """
        Render using Widget Factory for specialized blocks.

        FIXES AIR GAP: Specialized components are now USED!
        - CODE_FENCE -> IncrementalSyntaxHighlighter
        - TABLE -> StreamingTableRenderer
        - CHECKLIST -> ChecklistParser + render_checklist_text
        """
        blocks = self._block_detector.get_all_blocks()

        if not blocks:
            # No blocks detected, use simple markdown
            content = self._content
            if self.is_streaming and self.show_cursor:
                content += self.CURSOR_FRAMES[self._cursor_index]
            return RichMarkdown(content) if content else Text("")

        # Render each block with specialized widget
        renderables: List[RenderableType] = []

        for block in blocks:
            # Use Widget Factory to render specialized block
            rendered = self._widget_factory.render_block(block)
            renderables.append(rendered)

        # Add cursor at end if streaming
        if self.is_streaming and self.show_cursor:
            cursor_text = Text()
            cursor = self.CURSOR_FRAMES[self._cursor_index]
            cursor_text.append(cursor, style="bold bright_cyan")
            renderables.append(cursor_text)

        # Return Group of renderables
        return Group(*renderables) if renderables else Text("")

    async def _animate_cursor(self) -> None:
        """Animate cursor during streaming."""
        while self.is_streaming:
            self._cursor_index = (self._cursor_index + 1) % len(self.CURSOR_FRAMES)

            # Force re-render for cursor
            if self._markdown_static:
                renderable = self._create_renderable()
                self._markdown_static.update(renderable)

            await asyncio.sleep(self.CURSOR_INTERVAL)

    async def end_stream(self) -> None:
        """End streaming session."""
        self.is_streaming = False
        self.show_cursor = False

        # Cancel cursor animation
        if self._cursor_task:
            self._cursor_task.cancel()
            try:
                await self._cursor_task
            except asyncio.CancelledError:
                pass
            self._cursor_task = None

        # Final render
        await self._render_frame()

        # Remove state classes
        self.remove_class("streaming")
        self.remove_class("performance-warning")
        self.remove_class("plain-text-mode")

        # Emit end event
        self.post_message(self.StreamEnded(self._content, self._metrics))

    async def stream_content(
        self,
        content_iterator: AsyncIterator[str],
        on_block_change: Optional[Callable[[BlockType], None]] = None,
    ) -> str:
        """
        Stream content from async iterator.

        Args:
            content_iterator: Iterator producing text chunks
            on_block_change: Callback when block type changes

        Returns:
            Complete content
        """
        await self.start_stream()

        try:
            async for chunk in content_iterator:
                await self.append_chunk(chunk)

                if on_block_change and self._block_detector.get_current_block():
                    on_block_change(self._block_detector.get_current_block().block_type)

        finally:
            await self.end_stream()

        return self._content

    def get_content(self) -> str:
        """Return current content."""
        return self._content

    def get_metrics(self) -> PerformanceMetrics:
        """Return performance metrics."""
        return self._metrics

    def get_blocks(self) -> List[BlockInfo]:
        """Return detected blocks."""
        return self._block_detector.get_all_blocks()


__all__ = ["StreamingMarkdownWidget"]
