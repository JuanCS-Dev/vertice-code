"""
Response View Widget - Phase 9 Visual Refresh.

Smooth 60fps Response Viewport for streaming AI responses.
Enhanced code blocks with headers, diffs, and Slate theme.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TYPE_CHECKING

from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Markdown as TextualMarkdown

from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown as RichMarkdown
from rich.text import Text
from rich import box

from vertice_core.tui.constants import BANNER
from vertice_core.tui.widgets.selectable import SelectableStatic
from vertice_core.tui.widgets.expandable_blocks import ExpandableCodeBlock, ExpandableDiffBlock
from vertice_core.tui.core.formatting import OutputFormatter, Colors, Icons
from vertice_core.tui.core.streaming.soft_buffer import SoftBuffer

if TYPE_CHECKING:
    from textual.widgets._markdown import MarkdownStream


class ResponseView(VerticalScroll):
    """
    Smooth 60fps Response Viewport.

    Handles:
    - User messages
    - AI streaming responses
    - Code blocks with syntax highlighting
    - Action indicators
    """

    DEFAULT_CSS = """
    ResponseView {
        height: 1fr;
        background: $background;
        padding: 1 2;
        scrollbar-size: 0 0;
    }

    .user-message {
        margin-bottom: 1;
        color: $foreground;
    }

    .ai-response {
        margin-bottom: 1;
        color: $foreground;
    }

    .code-block {
        margin: 1 0;
        background: $surface;
    }

    .diff-block {
        margin: 1 0;
        background: $surface;
    }

    .action {
        color: $accent;
    }

    .success {
        color: $success;
    }

    .error {
        color: $error;
    }

    .warning {
        color: $warning;
    }

    .system-message {
        margin: 1 0;
        color: $foreground;
    }

    .tool-result {
        margin: 1 0;
    }

    .banner {
        text-align: center;
        width: 100%;
        color: $primary;
    }
    """

    is_thinking: reactive[bool] = reactive(False)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current_response = ""
        self._response_widget: Static | TextualMarkdown | None = None
        self._markdown_stream: MarkdownStream | None = None
        self._thinking_widget: Static | None = None
        self._use_textual_markdown_stream: bool = True
        self._max_view_items = self._get_max_view_items()
        self._scrollback_rich_tail = self._get_scrollback_rich_tail()
        self._scrollback_compact_batch = self._get_scrollback_compact_batch()
        self._pending_stream_chunks: list[str] = []
        self._soft_buffer = SoftBuffer()
        self._flush_timer = None
        self._flush_lock = asyncio.Lock()
        self._flush_scheduled = False
        self._stream_flush_interval_s = self._get_stream_flush_interval_s()

    def _get_max_view_items(self) -> int:
        """
        Max number of non-banner widgets kept in the scrollback.

        This prevents long sessions from degrading due to mounting unbounded widgets.
        """
        try:
            return int(os.getenv("VERTICE_TUI_MAX_VIEW_ITEMS", "300"))
        except ValueError:
            return 300

    def _get_stream_flush_interval_s(self) -> float:
        """
        Flush cadence for streaming updates.

        Goal: reduce layout thrash (many tiny writes) while keeping perceived latency low.
        """
        try:
            ms = int(os.getenv("VERTICE_TUI_STREAM_FLUSH_MS", "33"))
            return max(ms, 5) / 1000.0
        except ValueError:
            return 0.033

    def _get_scrollback_rich_tail(self) -> int:
        """
        Number of most-recent widgets kept "rich" (not compacted).

        Older renderables are degraded to cheaper equivalents to keep long-session scrollback
        responsive without sacrificing recent UX.
        """
        try:
            return int(os.getenv("VERTICE_TUI_SCROLLBACK_RICH_TAIL", "80"))
        except ValueError:
            return 80

    def _get_scrollback_compact_batch(self) -> int:
        """
        Max number of widgets compacted per trim call.

        This keeps compaction incremental to avoid UI jank when sessions get very long.
        """
        try:
            return int(os.getenv("VERTICE_TUI_SCROLLBACK_COMPACT_BATCH", "5"))
        except ValueError:
            return 5

    def _get_max_code_lines(self) -> int:
        """
        Max lines rendered for code blocks by default.

        Large blocks are truncated and can be expanded interactively to avoid
        expensive Rich Syntax rendering in long sessions.
        """
        try:
            return int(os.getenv("VERTICE_TUI_MAX_CODE_LINES", "200"))
        except ValueError:
            return 200

    def _get_max_diff_lines(self) -> int:
        """
        Max lines rendered for diff blocks by default.

        Large blocks are truncated and can be expanded interactively.
        """
        try:
            return int(os.getenv("VERTICE_TUI_MAX_DIFF_LINES", "400"))
        except ValueError:
            return 400

    def _ensure_flush_timer(self) -> None:
        if self._flush_timer is not None:
            return
        self._flush_timer = self.set_interval(self._stream_flush_interval_s, self._flush_tick)

    def _schedule_flush(self) -> None:
        if self._flush_scheduled or self._flush_lock.locked():
            return
        self._flush_scheduled = True
        self.call_later(self._flush_pending_stream_async)

    def _stop_flush_timer(self) -> None:
        if self._flush_timer is None:
            return
        try:
            self._flush_timer.stop()
        finally:
            self._flush_timer = None

    def _flush_tick(self) -> None:
        """Timer tick: schedule async flush if needed (keeps tick handler sync)."""
        if not self._pending_stream_chunks:
            return
        self._schedule_flush()

    def _trim_view_items(self) -> None:
        """Trim old widgets to keep the view responsive in long sessions."""
        max_items = self._max_view_items
        if max_items <= 0:
            return

        candidates = [child for child in self.children if not child.has_class("banner")]
        excess = len(candidates) - max_items
        if excess > 0:
            for child in candidates[:excess]:
                if child is self._thinking_widget:
                    continue
                child.remove()

        # When the view reaches its steady-state max size, compact older expensive renderables
        # (code/diff blocks) to keep long-session scrolling responsive.
        candidates = [child for child in self.children if not child.has_class("banner")]
        if len(candidates) >= max_items:
            self._compact_old_renderables(candidates)

    def _compact_old_renderables(self, candidates: list[Widget]) -> None:
        rich_tail = self._scrollback_rich_tail
        if rich_tail <= 0:
            return

        compact_budget = self._scrollback_compact_batch
        if compact_budget <= 0:
            return

        cutoff = max(len(candidates) - rich_tail, 0)
        if cutoff <= 0:
            return

        compacted = 0
        for child in candidates[:cutoff]:
            if compacted >= compact_budget:
                break

            if child is self._thinking_widget:
                continue

            # Auto-collapse expanded blocks to free heavy renderables.
            if isinstance(child, ExpandableCodeBlock):
                if child.expanded:
                    child.expanded = False
                    child.add_class("compacted")
                    compacted += 1
                continue

            if isinstance(child, ExpandableDiffBlock):
                if child.expanded:
                    child.expanded = False
                    child.add_class("compacted")
                    compacted += 1
                continue

            if child.has_class("compacted"):
                continue

            # Replace expensive Syntax panels with expandable (lazy materialized) equivalents.
            if not child.has_class("code-block"):
                continue

            if not isinstance(child, SelectableStatic):
                continue

            renderable = self._get_static_renderable(child)
            if not isinstance(renderable, Panel):
                continue

            if not isinstance(renderable.renderable, Syntax):
                continue

            syntax = renderable.renderable
            language = "text"
            try:
                lexer = getattr(syntax, "lexer", None)
                aliases = getattr(lexer, "aliases", None) if lexer is not None else None
                if aliases:
                    language = aliases[0]
                elif lexer is not None and getattr(lexer, "name", None):
                    language = str(getattr(lexer, "name")).lower()
            except Exception as e:
                language = "text"

            preview_lines = min(max(self._get_max_code_lines(), 1), 50)
            replacement = ExpandableCodeBlock(
                syntax.code,
                language=language,
                max_preview_lines=preview_lines,
            )
            replacement.add_class("compacted")

            self.mount(replacement, before=child)
            child.remove()
            compacted += 1

    @staticmethod
    def _get_static_renderable(widget: Widget) -> object | None:
        """
        Return the underlying Rich renderable for Static-derived widgets.

        Textual 6.x stores the content on a private attribute; there is no public `.renderable`.
        """
        if not isinstance(widget, Static):
            return None

        # Fast-path for Textual 6.x: name-mangled attribute set by `Static`.
        content = getattr(widget, "_Static__content", None)
        if content is not None:
            return content

        # Fallback: `render()` may wrap Rich renderables in a RichVisual.
        try:
            visual = widget.render()
        except Exception as e:
            return None

        return getattr(visual, "_renderable", visual)

    def add_banner(self) -> None:
        """Add startup banner."""
        widget = Static(BANNER, classes="banner")
        self.mount(widget)
        self._trim_view_items()

    def add_user_message(self, message: str) -> None:
        """Add user message with prompt icon."""
        content = Text()
        content.append("❯ ", style=f"bold {Colors.PRIMARY}")
        content.append(message)

        widget = SelectableStatic(content, classes="user-message")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_system_message(self, message: str) -> None:
        """Add system/help message with premium Panel styling."""
        # Detect Rich markup tags - if present, use Text.from_markup()
        if "[bold" in message or "[cyan]" in message or "[dim]" in message:
            content = Text.from_markup(message)
        else:
            # Standard markdown in a styled panel
            content = RichMarkdown(message)

        # Wrap in a premium panel
        panel = Panel(
            content,
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

        widget = SelectableStatic(panel, classes="system-message")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def start_thinking(self) -> None:
        """Show advanced reasoning stream indicator."""
        from vertice_core.tui.widgets import ReasoningStream

        # Safety: Check if widget already exists in DOM (even if self._thinking_widget is lost)
        existing = self.query("#reasoning-stream").first()
        if existing:
            self._thinking_widget = existing
            self.is_thinking = True
            return

        if self._thinking_widget is not None:
            return

        self.is_thinking = True
        self._thinking_widget = ReasoningStream(id="reasoning-stream")
        self.mount(self._thinking_widget)
        self.scroll_end(animate=False)

    async def end_thinking(self) -> None:
        """Remove thinking indicator and finalize response."""
        self.is_thinking = False

        # Remove from DOM if exists
        targets = self.query("#reasoning-stream")
        if targets:
            for t in targets:
                t.remove()

        # Reset internal reference
        self._thinking_widget = None

        self._stop_flush_timer()
        await self._flush_pending_stream_async(final=True)

        # Flush any pending markdown fragments.
        if self._markdown_stream is not None:
            try:
                await self._markdown_stream.stop()
            except Exception as e:
                pass
            finally:
                self._markdown_stream = None

        # Reset for next response
        self.current_response = ""
        self._response_widget = None
        self._pending_stream_chunks.clear()
        self._soft_buffer = SoftBuffer()

    def append_chunk(self, chunk: str) -> None:
        """Append streaming chunk (buffers + coalesces flushes for smooth rendering)."""
        self._pending_stream_chunks.append(chunk)
        self._ensure_flush_timer()

        if self._response_widget:
            if self._use_textual_markdown_stream and isinstance(
                self._response_widget, TextualMarkdown
            ):
                if self._markdown_stream is None:
                    self._markdown_stream = TextualMarkdown.get_stream(self._response_widget)
            else:
                # Non-streaming mode: flush will update the widget.
                pass
        else:
            # Create new widget (first chunk)
            if self._thinking_widget:
                self._thinking_widget.remove()
                self._thinking_widget = None

            if self._use_textual_markdown_stream:
                self._response_widget = TextualMarkdown("", classes="ai-response")
                self.mount(self._response_widget)
                self._trim_view_items()
                self._markdown_stream = TextualMarkdown.get_stream(self._response_widget)
            else:
                self._response_widget = SelectableStatic("", classes="ai-response")
                self.mount(self._response_widget)
                self._trim_view_items()
            # First token latency: flush as soon as possible, then keep cadence via timer.
            self._schedule_flush()

    async def _flush_pending_stream_async(self, final: bool = False) -> None:
        """
        Flush pending chunks to the UI.

        This coalesces many tiny deltas into fewer markdown stream writes to reduce
        render/layout overhead while streaming.
        """
        self._flush_scheduled = False
        async with self._flush_lock:
            pending = "".join(self._pending_stream_chunks)
            self._pending_stream_chunks.clear()

            safe = self._soft_buffer.feed(pending) if pending else ""
            if final:
                safe += self._soft_buffer.flush()

            if not safe:
                return

            if self._response_widget is None:
                return

            if (
                self._use_textual_markdown_stream
                and isinstance(self._response_widget, TextualMarkdown)
                and self._markdown_stream is not None
            ):
                await self._markdown_stream.write(safe)
            else:
                self.current_response += safe
                self._response_widget.update(self.current_response)

            # Throttled scroll (max 20fps = 50ms) to prevent layout thrashing
            current_time = time.time()
            if not hasattr(self, "_last_scroll_time"):
                self._last_scroll_time = 0.0

            if current_time - self._last_scroll_time >= 0.05:
                self.scroll_end(animate=False)
                self._last_scroll_time = current_time

    async def handle_open_responses_event(self, event) -> None:
        """
        Handle Open Responses streaming event.

        Args:
            event: OpenResponsesEvent instance
        """
        from vertice_core.tui.core.openresponses_events import (
            OpenResponsesResponseCreatedEvent,
            OpenResponsesResponseInProgressEvent,
            OpenResponsesOutputItemAddedEvent,
            OpenResponsesOutputTextDeltaEvent,
            OpenResponsesOutputTextDoneEvent,
            OpenResponsesResponseCompletedEvent,
            OpenResponsesResponseFailedEvent,
            OpenResponsesDoneEvent,
            OpenResponsesReasoningContentDeltaEvent,
            OpenResponsesReasoningSummaryDeltaEvent,
            OpenResponsesFunctionCallArgumentsDeltaEvent,
            OpenResponsesContentPartAddedEvent,
            OpenResponsesContentPartDoneEvent,
        )

        if isinstance(event, OpenResponsesResponseCreatedEvent):
            # Start new response session
            self.start_thinking()
            self.current_response = ""
            self._markdown_stream = None
            self._pending_stream_chunks.clear()
            self._soft_buffer = SoftBuffer()
            return

        match event:
            case OpenResponsesResponseInProgressEvent():
                pass

            case OpenResponsesOutputItemAddedEvent(item_type=item_type):
                if item_type == "reasoning":
                    self.start_thinking()
                elif item_type == "message":
                    pass

            case OpenResponsesOutputTextDeltaEvent(delta=delta):
                self.append_chunk(delta)

            case OpenResponsesReasoningContentDeltaEvent(delta=delta):
                if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                    self._thinking_widget.append_chunk(delta)
                else:
                    self.current_response += f"\n> [Thinking] {delta}"

            case OpenResponsesReasoningSummaryDeltaEvent(delta=delta):
                if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                    self._thinking_widget.append_chunk(f"Summary: {delta}")
                else:
                    self.current_response += f"\n> [Summary] {delta}"

            case OpenResponsesFunctionCallArgumentsDeltaEvent(delta=delta):
                if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                    self._thinking_widget.append_chunk(f"Args: {delta}")
                else:
                    self.current_response += f"\n> [Function Args] {delta}"

            case OpenResponsesContentPartAddedEvent() | OpenResponsesContentPartDoneEvent():
                pass

            case OpenResponsesOutputTextDoneEvent(text=text):
                self.current_response = text

            case OpenResponsesResponseCompletedEvent():
                await self.end_thinking()

            case OpenResponsesResponseFailedEvent(error=error):
                error_msg = error.get("message", "Unknown error") if error else "Response failed"
                self.add_system_message(f"[error]{Icons.ERROR} {error_msg}[/error]")
                await self.end_thinking()

            case OpenResponsesDoneEvent():
                pass

    def add_code_block(
        self,
        code: str,
        language: str = "text",
        title: str | None = None,
        file_path: str | None = None,
    ) -> None:
        """
        Add syntax-highlighted code block with enhanced header.

        Args:
            code: Source code to display
            language: Programming language for syntax highlighting
            title: Optional custom title
            file_path: Optional file path to show in header
        """
        stripped = code.strip()
        max_lines = self._get_max_code_lines()
        line_count = stripped.count("\n") + 1 if stripped else 0

        if max_lines > 0 and line_count > max_lines:
            widget = ExpandableCodeBlock(
                stripped,
                language=language,
                title=title,
                file_path=file_path,
                max_preview_lines=max_lines,
            )
            self.mount(widget)
            self._trim_view_items()
            self.scroll_end(animate=False)
            return

        syntax = Syntax(
            stripped,
            language,
            theme="one-dark",
            line_numbers=True,
            word_wrap=True,
            background_color=Colors.SURFACE,
        )

        # Build header: icon + language + optional path
        header_parts = [f"{Icons.CODE_FILE} {language.upper()}"]
        if file_path:
            header_parts.append(f"[{Colors.MUTED}]{file_path}[/]")
        elif title:
            header_parts.append(f"[{Colors.MUTED}]{title}[/]")

        panel_title = " ".join(header_parts)
        panel = Panel(
            syntax,
            title=f"[bold {Colors.PRIMARY}]{panel_title}[/]",
            title_align="left",
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

        widget = SelectableStatic(panel, classes="code-block")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_diff_block(
        self, diff_content: str, title: str = "Diff", file_path: str | None = None
    ) -> None:
        """
        Add diff block with colored additions/deletions.

        Args:
            diff_content: Diff text with +/- prefixes
            title: Block title
            file_path: Optional file path to show
        """
        stripped = diff_content.strip()
        max_lines = self._get_max_diff_lines()
        line_count = stripped.count("\n") + 1 if stripped else 0

        if max_lines > 0 and line_count > max_lines:
            widget = ExpandableDiffBlock(
                stripped,
                title=title,
                file_path=file_path,
                max_preview_lines=max_lines,
            )
            self.mount(widget)
            self._trim_view_items()
            self.scroll_end(animate=False)
            return

        lines = stripped.split("\n")
        result = Text()

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                result.append(line + "\n", style=f"bold {Colors.SUCCESS}")
            elif line.startswith("-") and not line.startswith("---"):
                result.append(line + "\n", style=f"bold {Colors.ERROR}")
            elif line.startswith("@@"):
                result.append(line + "\n", style=f"bold {Colors.ACCENT}")
            else:
                result.append(line + "\n", style=Colors.MUTED)

        # Header
        header = f"{Icons.GIT} {title}"
        if file_path:
            header += f" [{Colors.MUTED}]{file_path}[/]"

        panel = Panel(
            result,
            title=f"[bold {Colors.PRIMARY}]{header}[/]",
            title_align="left",
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

        widget = SelectableStatic(panel, classes="diff-block")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_action(self, action: str) -> None:
        """Add action indicator with accent color."""
        widget = SelectableStatic(
            f"[bold {Colors.ACCENT}]{Icons.EXECUTING}[/] [{Colors.MUTED}]{action}[/]",
            classes="action",
        )
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_warning(self, message: str) -> None:
        """Add warning message with triangle icon."""
        widget = SelectableStatic(
            f"[bold {Colors.WARNING}]{Icons.WARNING}[/] [{Colors.WARNING}]{message}[/]",
            classes="warning",
        )
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_success(self, message: str) -> None:
        """Add success message with checkmark."""
        widget = SelectableStatic(
            f"[bold {Colors.SUCCESS}]{Icons.SUCCESS}[/] [{Colors.SUCCESS}]{message}[/]",
            classes="success",
        )
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_error(self, message: str) -> None:
        """Add error message with X."""
        widget = SelectableStatic(
            f"[bold {Colors.ERROR}]{Icons.ERROR}[/] [{Colors.ERROR}]{message}[/]", classes="error"
        )
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_tool_result(
        self, tool_name: str, success: bool, data: str | None = None, error: str | None = None
    ) -> None:
        """Add tool execution result with Panel formatting."""
        panel = OutputFormatter.format_tool_result(tool_name, success, data, error)
        widget = SelectableStatic(panel, classes="tool-result")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_response_panel(self, text: str, title: str = "Response") -> None:
        """Add a formatted response panel."""
        panel = OutputFormatter.format_response(text, title)
        widget = SelectableStatic(panel, classes="ai-response")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_info_panel(
        self, message: str, title: str = "Info", icon: str = "ℹ️", border_color: str = Colors.PRIMARY
    ) -> None:
        """Add a premium info panel with title, icon, and styled border.

        Args:
            message: Markdown content to display
            title: Panel title
            icon: Emoji icon for the panel header
            border_color: Border color (from Colors constants)
        """
        content = RichMarkdown(message)

        panel = Panel(
            content,
            title=f"[bold {border_color}]{icon} {title}[/]",
            title_align="left",
            border_style=border_color,
            box=box.ROUNDED,
            padding=(1, 2),
        )

        widget = SelectableStatic(panel, classes="info-panel")
        self.mount(widget)
        self._trim_view_items()
        self.scroll_end(animate=False)

    def add_markdown_response(self, text: str, title: str = "Response") -> None:
        """Add markdown response with syntax highlighting for code blocks."""
        self._render_markdown_with_syntax(text, title)

    def _render_markdown_with_syntax(self, text: str, title: str) -> None:
        """Render markdown text with proper syntax highlighting for code blocks."""
        import re
        from rich.markdown import Markdown
        from rich.text import Text
        from rich.panel import Panel
        from rich.console import Group
        from rich.box import ROUNDED

        # Split text into markdown and code blocks
        parts = []
        last_end = 0

        # Find all code blocks
        code_block_pattern = r"```(\w+)?\n(.*?)\n```"
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            # Add text before code block
            if match.start() > last_end:
                markdown_text = text[last_end : match.start()]
                if markdown_text.strip():
                    parts.append(("markdown", markdown_text))

            # Add code block
            language = match.group(1) or "text"
            code = match.group(2)
            parts.append(("code", (language, code)))

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text.strip():
                parts.append(("markdown", remaining_text))

        # If no code blocks found, render as regular markdown
        if not any(part[0] == "code" for part in parts):
            panel = OutputFormatter.format_response(text, title)
            widget = SelectableStatic(panel, classes="ai-response")
            self.mount(widget)
            self._trim_view_items()
            self.scroll_end(animate=False)
            return

        # Render parts
        rendered_parts = []
        for part_type, content in parts:
            if part_type == "markdown":
                try:
                    rendered_parts.append(Markdown(content))
                except (ValueError, TypeError):
                    rendered_parts.append(Text(content))
            elif part_type == "code":
                language, code = content
                self.add_code_block(code, language)

        # Create panel with all parts
        if rendered_parts:
            content = Group(*rendered_parts)
            panel = Panel(
                content,
                title=f"[bold {Colors.PRIMARY}]{title}[/]",
                title_align="left",
                border_style=Colors.BORDER,
                box=ROUNDED,
                padding=(1, 2),
            )
            widget = SelectableStatic(panel, classes="ai-response")
            self.mount(widget)
            self._trim_view_items()

        self.scroll_end(animate=False)

    def clear_all(self) -> None:
        """Clear all content."""
        self.current_response = ""
        self._response_widget = None
        self._thinking_widget = None

        for child in list(self.children):
            child.remove()
