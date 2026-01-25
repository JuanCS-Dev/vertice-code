"""
Streaming Markdown Factory - Block Widget Factory.

This module provides BlockWidgetFactory that creates specialized
renderables for different block types.

Features:
- Code fence rendering with syntax highlighting
- Table rendering with progressive updates
- Checklist rendering with interactive items
- Specialized renderers for tool calls, status badges, diffs

Philosophy:
    "The factory knows which tool to use for each job."
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markdown import Markdown as RichMarkdown
from rich.text import Text
from rich.console import RenderableType

if TYPE_CHECKING:
    from ..block_detector import BlockInfo

from ..block_detector import BlockType
from ..streaming_code_block import IncrementalSyntaxHighlighter, create_code_block_panel
from ..streaming_table import StreamingTableRenderer
from ..interactive_checklist import ChecklistParser, render_checklist_text

from .renderers import (
    render_heading,
    render_status_badge,
    render_diff,
    render_tool_call,
)


class BlockWidgetFactory:
    """
    Factory for creating specialized renderables by block type.

    FIXES AIR GAP: Specialized components are now USED.

    Supported block types:
    - CODE_FENCE: IncrementalSyntaxHighlighter
    - TABLE: StreamingTableRenderer
    - CHECKLIST: ChecklistParser
    - HEADING: Styled headings
    - TOOL_CALL: Claude Code / Gemini style
    - STATUS_BADGE: Colored status indicators
    - DIFF_BLOCK: GitHub style diffs
    """

    def __init__(self):
        """Initialize factory with cached highlighters."""
        # Cache of highlighters by language (reuse for performance)
        self._highlighters: dict[str, IncrementalSyntaxHighlighter] = {}
        self._table_renderer = StreamingTableRenderer()

    def render_block(self, block: "BlockInfo") -> RenderableType:
        """
        Render a block using the appropriate specialized component.

        Args:
            block: Block info from BlockDetector

        Returns:
            Rich renderable formatted appropriately
        """
        if block.block_type == BlockType.CODE_FENCE:
            return self._render_code_fence(block)
        elif block.block_type == BlockType.TABLE:
            return self._render_table(block)
        elif block.block_type == BlockType.CHECKLIST:
            return self._render_checklist(block)
        elif block.block_type == BlockType.HEADING:
            return render_heading(block)
        elif block.block_type == BlockType.TOOL_CALL:
            return render_tool_call(block)
        elif block.block_type == BlockType.STATUS_BADGE:
            return render_status_badge(block)
        elif block.block_type == BlockType.DIFF_BLOCK:
            return render_diff(block)
        else:
            # Default: Rich Markdown for other blocks
            return self._render_default(block)

    def _render_code_fence(self, block: "BlockInfo") -> RenderableType:
        """Render code fence with incremental syntax highlighting."""
        language = block.language or "text"

        # 2026 FIX: If language is "markdown", render as actual markdown
        # not as a code block (common LLM pattern)
        if language.lower() in ("markdown", "md"):
            return self._render_default(block)

        # Reuse highlighter if exists for same language
        if language not in self._highlighters:
            self._highlighters[language] = IncrementalSyntaxHighlighter(language)

        highlighter = self._highlighters[language]

        # Reset and process content
        highlighter.reset()
        highlighter.process_chunk(block.content)

        # Return as styled Panel
        return create_code_block_panel(
            code=block.content,
            language=language,
            title=f"{language.upper()}" + ("" if block.is_complete else " ⏳"),
        )

    def _render_table(self, block: "BlockInfo") -> RenderableType:
        """Render table progressively."""
        self._table_renderer.reset()
        return self._table_renderer.process_chunk(block.content)

    def _render_checklist(self, block: "BlockInfo") -> RenderableType:
        """Render checklist with items."""
        items = ChecklistParser.parse_markdown(block.content)
        return render_checklist_text(items)

    def _render_default(self, block: "BlockInfo") -> RenderableType:
        """Render generic block as markdown."""
        try:
            return RichMarkdown(block.content)
        except (ValueError, TypeError):
            return Text(block.content)

    def reset(self) -> None:
        """Reset state of all renderers."""
        self._highlighters.clear()
        self._table_renderer.reset()


__all__ = ["BlockWidgetFactory"]
