"""
Enhanced Input Area - Full syntax highlighting with TextArea.

Uses Textual's TextArea with tree-sitter for real syntax highlighting.

Phase 11: Visual Upgrade - Interactive Components.
"""

from __future__ import annotations

from typing import ClassVar, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message

# Try to import TextArea with syntax highlighting
try:
    from textual.widgets import TextArea

    TEXTAREA_AVAILABLE = True
except ImportError:
    TEXTAREA_AVAILABLE = False


class InputArea(Widget):
    """
    Enhanced input with syntax highlighting.

    Features:
    - Auto language detection
    - Syntax highlighting via tree-sitter
    - Bracket matching
    - Line numbers (optional)
    - Submit on Ctrl+Enter
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+enter", "submit", "Submit", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+a", "select_all", "Select All", show=False),
        Binding("ctrl+u", "clear_line", "Clear Line", show=False),
        Binding("ctrl+k", "kill_to_end", "Kill to End", show=False),
    ]

    DEFAULT_CSS = """
    InputArea {
        height: auto;
        min-height: 3;
        max-height: 15;
        width: 100%;
        border: solid $primary;
        background: $surface;
    }

    InputArea.single-line {
        min-height: 1;
        max-height: 3;
        border: none;
    }

    InputArea TextArea {
        height: auto;
        min-height: 1;
        border: none;
        background: transparent;
    }

    InputArea .status-bar {
        height: 1;
        dock: bottom;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }

    InputArea .status-bar .language {
        color: $accent;
    }
    """

    # Language detection patterns
    LANGUAGE_HINTS = {
        "python": [
            "def ",
            "import ",
            "class ",
            "from ",
            "async def",
            "elif ",
            "except Exception as e:",
        ],
        "javascript": ["const ", "let ", "function ", "=> ", "async ", "await "],
        "typescript": ["interface ", "type ", ": string", ": number", ": boolean"],
        "rust": ["fn ", "let mut", "impl ", "pub fn", "use ", "mod "],
        "go": ["func ", "package ", "import (", "type ", "var "],
        "bash": ["#!/bin/bash", "echo ", "if [", "fi", "done", "export "],
        "sql": ["SELECT ", "FROM ", "WHERE ", "INSERT ", "UPDATE ", "DELETE "],
        "json": ['{"', '": ', '"}', '": [', '": {'],
        "yaml": ["---", "- name:", "  - ", ": |"],
        "html": ["<html", "<div", "<span", "</", "/>"],
        "css": ["{", "}", ":", ";", "px", "em", "rem"],
        "markdown": ["# ", "## ", "```", "- ", "* ", "**", "__"],
    }

    language: reactive[str] = reactive("text")

    class Submitted(Message):
        """Emitted when user submits input."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    class Cancelled(Message):
        """Emitted when user cancels."""

        pass

    def __init__(
        self,
        placeholder: str = "Type your message...",
        language: str = "text",
        show_line_numbers: bool = False,
        single_line: bool = False,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._placeholder = placeholder
        self._initial_language = language
        self._show_line_numbers = show_line_numbers
        self._single_line = single_line
        self._text_area: Optional[TextArea] = None

    def compose(self) -> ComposeResult:
        if self._single_line:
            self.add_class("single-line")

        if TEXTAREA_AVAILABLE:
            self._text_area = TextArea(
                language=self._initial_language if self._initial_language != "text" else None,
                show_line_numbers=self._show_line_numbers,
                soft_wrap=True,
                tab_behavior="indent",
                id="text-area",
            )
            yield self._text_area

            if not self._single_line:
                yield Static("", classes="status-bar", id="status-bar")
        else:
            # Fallback to simple input
            from textual.widgets import Input

            yield Input(placeholder=self._placeholder, id="fallback-input")

    def on_mount(self) -> None:
        if self._text_area:
            self._text_area.focus()
            self._update_status()

    @property
    def value(self) -> str:
        """Get current input value."""
        if self._text_area:
            return self._text_area.text
        try:
            from textual.widgets import Input

            return self.query_one("#fallback-input", Input).value
        except (AttributeError, ValueError):
            return ""

    @value.setter
    def value(self, new_value: str) -> None:
        """Set input value."""
        if self._text_area:
            self._text_area.text = new_value
        else:
            try:
                from textual.widgets import Input

                self.query_one("#fallback-input", Input).value = new_value
            except (AttributeError, ValueError):
                pass

    def focus(self) -> None:
        """Focus the input."""
        if self._text_area:
            self._text_area.focus()
        else:
            try:
                from textual.widgets import Input

                self.query_one("#fallback-input", Input).focus()
            except (AttributeError, ValueError):
                pass

    def clear(self) -> None:
        """Clear the input."""
        self.value = ""
        self.language = "text"
        if self._text_area:
            self._text_area.language = None

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Auto-detect language from content."""
        text = event.text_area.text
        detected = self._detect_language(text)

        if detected != self.language:
            self.language = detected
            if self._text_area and detected != "text":
                try:
                    self._text_area.language = detected
                except (AttributeError, ValueError):
                    pass

        self._update_status()

    def _detect_language(self, text: str) -> str:
        """Detect programming language from content."""
        if not text or len(text) < 3:
            return "text"

        # Check for code block markers
        if text.startswith("```"):
            # Extract language from fence
            first_line = text.split("\n")[0]
            lang = first_line[3:].strip().lower()
            if lang in self.LANGUAGE_HINTS:
                return lang

        # Score-based detection
        scores = {}
        text_lower = text.lower()

        for lang, hints in self.LANGUAGE_HINTS.items():
            score = sum(1 for hint in hints if hint.lower() in text_lower)
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)

        return "text"

    def _update_status(self) -> None:
        """Update status bar."""
        if self._single_line:
            return

        try:
            status = self.query_one("#status-bar", Static)
            if self._text_area:
                row, col = self._text_area.cursor_location
                lines = len(self._text_area.text.split("\n"))
                lang_display = self.language.upper() if self.language != "text" else ""

                parts = []
                if lang_display:
                    parts.append(f"[bold cyan]{lang_display}[/]")
                parts.append(f"Ln {row + 1}, Col {col + 1}")
                parts.append(f"{lines} lines")

                status.update(" │ ".join(parts))
        except (AttributeError, ValueError):
            pass

    def action_submit(self) -> None:
        """Submit the input."""
        if self.value.strip():
            self.post_message(self.Submitted(self.value))

    def action_cancel(self) -> None:
        """Cancel input."""
        self.post_message(self.Cancelled())

    def action_select_all(self) -> None:
        """Select all text."""
        if self._text_area:
            self._text_area.select_all()

    def action_clear_line(self) -> None:
        """Clear current line (Ctrl+U)."""
        if self._text_area:
            # Get current cursor position
            row, col = self._text_area.cursor_location
            lines = self._text_area.text.split("\n")
            if row < len(lines):
                # Clear from start of line to cursor
                lines[row] = lines[row][col:]
                self._text_area.text = "\n".join(lines)
                self._text_area.cursor_location = (row, 0)

    def action_kill_to_end(self) -> None:
        """Kill text to end of line (Ctrl+K)."""
        if self._text_area:
            row, col = self._text_area.cursor_location
            lines = self._text_area.text.split("\n")
            if row < len(lines):
                # Kill from cursor to end of line
                lines[row] = lines[row][:col]
                self._text_area.text = "\n".join(lines)
