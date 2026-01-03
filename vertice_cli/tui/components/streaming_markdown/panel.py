"""
Streaming Markdown Panel - Scrollable Container.

This module provides StreamingMarkdownPanel, a scrollable container
that wraps StreamingMarkdownWidget with auto-scroll and status bar.

Features:
- Auto-scroll during streaming
- Performance indicator
- Status bar with current block type
- Event handlers for streaming events

Philosophy:
    "The panel provides context, the widget provides content."
"""

from __future__ import annotations

from typing import Optional, AsyncIterator

from textual.widgets import Static
from textual.containers import ScrollableContainer
from textual.app import ComposeResult

from ..block_detector import BlockType

from .types import PerformanceMetrics
from .widget import StreamingMarkdownWidget


class StreamingMarkdownPanel(ScrollableContainer):
    """
    Scrollable panel with StreamingMarkdownWidget.

    Includes:
    - Auto-scroll during streaming
    - Performance indicator
    - Status bar with block type
    """

    DEFAULT_CSS = """
    StreamingMarkdownPanel {
        width: 100%;
        height: 100%;
        overflow-y: auto;
        border: solid #bd93f9;
    }

    StreamingMarkdownPanel > StreamingMarkdownWidget {
        width: 100%;
    }

    StreamingMarkdownPanel .status-bar {
        dock: bottom;
        height: 1;
        background: #282a36;
        color: #6272a4;
    }
    """

    # Block type icons for status bar
    BLOCK_ICONS = {
        BlockType.CODE_FENCE: " Code",
        BlockType.TABLE: " Table",
        BlockType.CHECKLIST: " Checklist",
        BlockType.HEADING: " Heading",
        BlockType.LIST: " List",
        BlockType.PARAGRAPH: " Paragraph",
    }

    def __init__(
        self,
        auto_scroll: bool = True,
        show_status: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        """
        Initialize panel.

        Args:
            auto_scroll: Enable auto-scroll during streaming
            show_status: Show status bar
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.auto_scroll = auto_scroll
        self.show_status = show_status
        self._markdown_widget: Optional[StreamingMarkdownWidget] = None
        self._status_bar: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        self._markdown_widget = StreamingMarkdownWidget()
        yield self._markdown_widget

        if self.show_status:
            self._status_bar = Static("", classes="status-bar")
            yield self._status_bar

    def on_streaming_markdown_widget_stream_started(
        self, event: StreamingMarkdownWidget.StreamStarted
    ) -> None:
        """Handler: streaming started."""
        if self._status_bar:
            self._status_bar.update(" Streaming...")

    def on_streaming_markdown_widget_stream_ended(
        self, event: StreamingMarkdownWidget.StreamEnded
    ) -> None:
        """Handler: streaming ended."""
        if self._status_bar:
            metrics = event.metrics
            self._status_bar.update(
                f" Done | {metrics.frames_rendered} frames | "
                f"Avg: {metrics.avg_render_time_ms:.1f}ms | "
                f"Min FPS: {metrics.min_fps:.0f}"
            )

    def on_streaming_markdown_widget_block_detected(
        self, event: StreamingMarkdownWidget.BlockDetected
    ) -> None:
        """Handler: block detected."""
        if (
            self._status_bar
            and self._markdown_widget
            and self._markdown_widget.is_streaming
        ):
            icon = self.BLOCK_ICONS.get(event.block_type, " Block")
            self._status_bar.update(f" Streaming... {icon}")

        # Auto-scroll
        if self.auto_scroll:
            self.scroll_end(animate=False)

    def on_streaming_markdown_widget_fps_warning(
        self, event: StreamingMarkdownWidget.FPSWarning
    ) -> None:
        """Handler: FPS warning."""
        if self._status_bar:
            if event.action == "FALLBACK_TO_PLAIN":
                self._status_bar.update(f" Performance mode | FPS: {event.fps:.0f}")
            elif event.action == "TRY_MARKDOWN_AGAIN":
                self._status_bar.update(" Restored markdown mode")

    async def stream(self, content_iterator: AsyncIterator[str]) -> str:
        """
        Start streaming content.

        Args:
            content_iterator: Iterator of chunks

        Returns:
            Complete content
        """
        if self._markdown_widget:
            return await self._markdown_widget.stream_content(content_iterator)
        return ""

    def get_widget(self) -> Optional[StreamingMarkdownWidget]:
        """Return the markdown widget."""
        return self._markdown_widget

    def get_metrics(self) -> Optional[PerformanceMetrics]:
        """Return performance metrics if available."""
        if self._markdown_widget:
            return self._markdown_widget.get_metrics()
        return None


__all__ = ["StreamingMarkdownPanel"]
