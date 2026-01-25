"""
Streaming Markdown Module - Claude Code Web Style Rendering.

This module provides comprehensive streaming markdown support for TUI:
- StreamingMarkdownWidget: Main widget for live markdown rendering
- StreamingMarkdownPanel: Scrollable container with status bar
- BlockWidgetFactory: Specialized block rendering
- AdaptiveFPSController: Performance management

Features:
- Live markdown rendering during streaming (INCREMENTAL)
- Optimistic block detection (bold, code, tables before closing)
- 30 FPS with 33.33ms frame budget
- Automatic fallback to plain text when FPS < 25
- Pulsing cursor at end of content
- Widget Factory for specialized blocks

Architecture:
    - types.py: RenderMode, PerformanceMetrics
    - renderers.py: Specialized block renderers
    - factory.py: BlockWidgetFactory
    - fps_controller.py: AdaptiveFPSController
    - widget.py: StreamingMarkdownWidget
    - panel.py: StreamingMarkdownPanel

Usage:
    from vertice_core.vertice_core.tui.components.streaming_markdown import (
        StreamingMarkdownWidget,
        StreamingMarkdownPanel,
    )

    # In a Textual app
    panel = StreamingMarkdownPanel()
    await panel.stream(content_iterator)

Philosophy:
    "Streaming should feel instant, even when it's not."
"""

# Types
from .types import RenderMode, PerformanceMetrics

# Renderers (for custom usage)
from .renderers import (
    render_heading,
    render_status_badge,
    render_diff,
    render_tool_call,
    TOOL_ICONS,
    HEADING_STYLES,
    STATUS_BADGE_STYLES,
)

# Factory
from .factory import BlockWidgetFactory

# FPS Controller
from .fps_controller import AdaptiveFPSController

# Widgets
from .widget import StreamingMarkdownWidget
from .panel import StreamingMarkdownPanel


__all__ = [
    # Types
    "RenderMode",
    "PerformanceMetrics",
    # Renderers
    "render_heading",
    "render_status_badge",
    "render_diff",
    "render_tool_call",
    "TOOL_ICONS",
    "HEADING_STYLES",
    "STATUS_BADGE_STYLES",
    # Factory
    "BlockWidgetFactory",
    # FPS Controller
    "AdaptiveFPSController",
    # Widgets
    "StreamingMarkdownWidget",
    "StreamingMarkdownPanel",
]
