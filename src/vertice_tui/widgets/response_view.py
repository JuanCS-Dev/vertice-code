"""
Response View Widget - Phase 9 Visual Refresh.

Smooth 60fps Response Viewport for streaming AI responses.
Enhanced code blocks with headers, diffs, and Slate theme.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich import box

from vertice_tui.constants import BANNER
from vertice_tui.widgets.selectable import SelectableStatic
from vertice_tui.core.formatting import OutputFormatter, Colors, Icons
from vertice_tui.components.streaming_adapter import StreamingResponseWidget

if TYPE_CHECKING:
    pass


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
        self._response_widget: Static | StreamingResponseWidget | None = None
        self._thinking_widget: Static | None = None
        self._use_streaming_markdown: bool = True

    def add_banner(self) -> None:
        """Add startup banner."""
        widget = Static(BANNER, classes="banner")
        self.mount(widget)

    def add_user_message(self, message: str) -> None:
        """Add user message with prompt icon."""
        content = Text()
        content.append("❯ ", style=f"bold {Colors.PRIMARY}")
        content.append(message)

        widget = SelectableStatic(content, classes="user-message")
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_system_message(self, message: str) -> None:
        """Add system/help message with premium Panel styling."""
        # Detect Rich markup tags - if present, use Text.from_markup()
        if "[bold" in message or "[cyan]" in message or "[dim]" in message:
            content = Text.from_markup(message)
        else:
            # Standard markdown in a styled panel
            content = Markdown(message)

        # Wrap in a premium panel
        panel = Panel(
            content,
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

        widget = SelectableStatic(panel, classes="system-message")
        self.mount(widget)
        self.scroll_end(animate=True)

    def start_thinking(self) -> None:
        """Show advanced reasoning stream indicator."""
        from vertice_tui.widgets import ReasoningStream

        self.is_thinking = True
        self._thinking_widget = ReasoningStream(id="reasoning-stream")
        self.mount(self._thinking_widget)
        self.scroll_end(animate=True)

    def end_thinking(self) -> None:
        """Remove thinking indicator and finalize response."""
        self.is_thinking = False
        if self._thinking_widget:
            self._thinking_widget.remove()
            self._thinking_widget = None

        # Wrap completed response in Panel
        if self.current_response and self._response_widget:
            if self._use_streaming_markdown and isinstance(
                self._response_widget, StreamingResponseWidget
            ):
                self._response_widget.finalize_sync()
            else:
                formatted_panel = OutputFormatter.format_response(
                    self.current_response, title="Response", border_style=Colors.PRIMARY
                )
                self._response_widget.update(formatted_panel)

        # Reset for next response
        self.current_response = ""
        self._response_widget = None

    def append_chunk(self, chunk: str) -> None:
        """Append streaming chunk. Optimized for 60fps."""
        self.current_response += chunk

        if self._response_widget:
            if self._use_streaming_markdown and isinstance(
                self._response_widget, StreamingResponseWidget
            ):
                self._response_widget.append_chunk(chunk)
            else:
                self._response_widget.update(self.current_response)
        else:
            # Create new widget (first chunk)
            if self._thinking_widget:
                self._thinking_widget.remove()
                self._thinking_widget = None

            if self._use_streaming_markdown:
                self._response_widget = StreamingResponseWidget(
                    classes="ai-response", enable_markdown=True
                )
            else:
                self._response_widget = SelectableStatic(
                    self.current_response, classes="ai-response"
                )
            self.mount(self._response_widget)

            if self._use_streaming_markdown and isinstance(
                self._response_widget, StreamingResponseWidget
            ):
                self._response_widget.append_chunk(chunk)

        # Throttled scroll (max 20fps = 50ms) to prevent layout thrashing
        current_time = time.time()
        if not hasattr(self, "_last_scroll_time"):
            self._last_scroll_time = 0.0

        if current_time - self._last_scroll_time >= 0.05:
            self.scroll_end(animate=False)
            self._last_scroll_time = current_time

    def handle_open_responses_event(self, event) -> None:
        """
        Handle Open Responses streaming event.

        Args:
            event: OpenResponsesEvent instance
        """
        from vertice_tui.core.openresponses_events import (
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

        elif isinstance(event, OpenResponsesResponseInProgressEvent):
            # Response is now in progress
            pass

        elif isinstance(event, OpenResponsesOutputItemAddedEvent):
            # New item added (message, function call, etc.)
            if event.item_type == "reasoning":
                self.start_thinking()
            elif event.item_type == "message":
                # Prepare for message content
                pass

        elif isinstance(event, OpenResponsesOutputTextDeltaEvent):
            # Text chunk received
            self.append_chunk(event.delta)

        elif isinstance(event, OpenResponsesReasoningContentDeltaEvent):
            # Reasoning chunk received
            if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                self._thinking_widget.append_chunk(event.delta)
            else:
                # Fallback if reasoning stream not active
                self.current_response += f"\n> [Thinking] {event.delta}"

        elif isinstance(event, OpenResponsesReasoningSummaryDeltaEvent):
            # Reasoning summary chunk received
            if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                self._thinking_widget.append_chunk(f"Summary: {event.delta}")
            else:
                # Fallback
                self.current_response += f"\n> [Summary] {event.delta}"

        elif isinstance(event, OpenResponsesFunctionCallArgumentsDeltaEvent):
            # Function call arguments chunk received
            if self._thinking_widget and hasattr(self._thinking_widget, "append_chunk"):
                self._thinking_widget.append_chunk(f"Args: {event.delta}")
            else:
                # Fallback
                self.current_response += f"\n> [Function Args] {event.delta}"

        elif isinstance(event, OpenResponsesContentPartAddedEvent):
            # Content part starts
            pass

        elif isinstance(event, OpenResponsesContentPartDoneEvent):
            # Content part finishes
            pass

        elif isinstance(event, OpenResponsesOutputTextDoneEvent):
            # Text completed
            self.current_response = event.text

        elif isinstance(event, OpenResponsesResponseCompletedEvent):
            # Response finished successfully
            self.end_thinking()

        elif isinstance(event, OpenResponsesResponseFailedEvent):
            # Response failed
            if event.error and hasattr(event.error, "get"):
                error_msg = event.error.get("message", "Unknown error")
            else:
                error_msg = "Response failed"
            self.add_system_message(f"[error]{Icons.ERROR} {error_msg}[/error]")
            self.end_thinking()

        elif isinstance(event, OpenResponsesDoneEvent):
            # Stream terminated
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
        syntax = Syntax(
            code.strip(),
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
        self.scroll_end(animate=True)

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
        lines = diff_content.strip().split("\n")
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
        self.scroll_end(animate=True)

    def add_action(self, action: str) -> None:
        """Add action indicator with accent color."""
        widget = SelectableStatic(
            f"[bold {Colors.ACCENT}]{Icons.EXECUTING}[/] [{Colors.MUTED}]{action}[/]",
            classes="action",
        )
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_warning(self, message: str) -> None:
        """Add warning message with triangle icon."""
        widget = SelectableStatic(
            f"[bold {Colors.WARNING}]{Icons.WARNING}[/] [{Colors.WARNING}]{message}[/]",
            classes="warning",
        )
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_success(self, message: str) -> None:
        """Add success message with checkmark."""
        widget = SelectableStatic(
            f"[bold {Colors.SUCCESS}]{Icons.SUCCESS}[/] [{Colors.SUCCESS}]{message}[/]",
            classes="success",
        )
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_error(self, message: str) -> None:
        """Add error message with X."""
        widget = SelectableStatic(
            f"[bold {Colors.ERROR}]{Icons.ERROR}[/] [{Colors.ERROR}]{message}[/]", classes="error"
        )
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_tool_result(
        self, tool_name: str, success: bool, data: str | None = None, error: str | None = None
    ) -> None:
        """Add tool execution result with Panel formatting."""
        panel = OutputFormatter.format_tool_result(tool_name, success, data, error)
        widget = SelectableStatic(panel, classes="tool-result")
        self.mount(widget)
        self.scroll_end(animate=True)

    def add_response_panel(self, text: str, title: str = "Response") -> None:
        """Add a formatted response panel."""
        panel = OutputFormatter.format_response(text, title)
        widget = SelectableStatic(panel, classes="ai-response")
        self.mount(widget)
        self.scroll_end(animate=True)

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
        content = Markdown(message)

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
        self.scroll_end(animate=True)

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
            self.scroll_end(animate=True)
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

        self.scroll_end(animate=True)

    def clear_all(self) -> None:
        """Clear all content."""
        self.current_response = ""
        self._response_widget = None
        self._thinking_widget = None

        for child in list(self.children):
            child.remove()
