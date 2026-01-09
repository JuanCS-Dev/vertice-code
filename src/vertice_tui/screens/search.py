"""
Search Screen - Ctrl+F search within conversation.

Simple search modal for finding text in ResponseView.

Phase 11: Visual Upgrade - Interactive Components.
"""

from __future__ import annotations

from typing import List, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from rich.text import Text


class SearchScreen(ModalScreen[None]):
    """
    Simple search modal for finding text in conversation.

    Features:
    - Real-time search as you type
    - Match count display
    - Navigate with N (next) / P (previous)
    - ESC to close
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "next_match", "Next", show=False),
        Binding("n", "next_match", "Next", show=False),
        Binding("p", "prev_match", "Previous", show=False),
    ]

    DEFAULT_CSS = """
    SearchScreen {
        align: center top;
        padding-top: 2;
    }

    SearchScreen > Horizontal {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }

    SearchScreen Input {
        width: 1fr;
        border: none;
        background: $surface;
    }

    SearchScreen .match-info {
        width: auto;
        min-width: 12;
        text-align: right;
        padding: 0 1;
        color: $text-muted;
    }

    SearchScreen .match-info.has-matches {
        color: $success;
    }

    SearchScreen .match-info.no-matches {
        color: $error;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._matches: List[Tuple[int, int]] = []  # (widget_index, char_offset)
        self._current_match = -1
        self._query = ""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="Search... (n/p to navigate)", id="search-input")
            yield Static("", classes="match-info", id="match-info")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._query = event.value
        self._search()

    def _search(self) -> None:
        """Search through ResponseView content."""
        self._matches = []
        self._current_match = -1

        if not self._query:
            self._update_match_info()
            return

        # Get ResponseView from main app
        try:
            response_view = self.app.query_one("#response")
            query_lower = self._query.lower()

            for idx, child in enumerate(response_view.children):
                # Get text content from widget
                text = self._get_widget_text(child)
                if query_lower in text.lower():
                    self._matches.append((idx, text.lower().find(query_lower)))

            if self._matches:
                self._current_match = 0
                self._scroll_to_match()

        except (AttributeError, ValueError):
            pass

        self._update_match_info()

    def _get_widget_text(self, widget) -> str:
        """Extract text content from a widget."""
        # Try renderable first
        if hasattr(widget, "renderable"):
            renderable = widget.renderable
            if isinstance(renderable, Text):
                return renderable.plain
            elif hasattr(renderable, "text"):
                return str(renderable.text)
            elif isinstance(renderable, str):
                return renderable

        # Try render() method
        if hasattr(widget, "render"):
            try:
                rendered = widget.render()
                if isinstance(rendered, Text):
                    return rendered.plain
                elif hasattr(rendered, "text"):
                    return str(rendered.text)
                elif isinstance(rendered, str):
                    return rendered
            except (AttributeError, TypeError, RuntimeError):
                pass

        return ""

    def _update_match_info(self) -> None:
        """Update match count display."""
        info = self.query_one("#match-info", Static)

        if not self._query:
            info.update("")
            info.remove_class("has-matches", "no-matches")
            return

        if self._matches:
            current = self._current_match + 1
            total = len(self._matches)
            info.update(f"{current}/{total}")
            info.remove_class("no-matches")
            info.add_class("has-matches")
        else:
            info.update("0/0")
            info.remove_class("has-matches")
            info.add_class("no-matches")

    def _scroll_to_match(self) -> None:
        """Scroll to current match in ResponseView."""
        if not self._matches or self._current_match < 0:
            return

        try:
            response_view = self.app.query_one("#response")
            widget_idx, _ = self._matches[self._current_match]

            if 0 <= widget_idx < len(response_view.children):
                target = response_view.children[widget_idx]
                target.scroll_visible(animate=False)

        except (AttributeError, ValueError, IndexError):
            pass

    def action_close(self) -> None:
        self.dismiss(None)

    def action_next_match(self) -> None:
        if not self._matches:
            return

        self._current_match = (self._current_match + 1) % len(self._matches)
        self._scroll_to_match()
        self._update_match_info()

    def action_prev_match(self) -> None:
        if not self._matches:
            return

        self._current_match = (self._current_match - 1) % len(self._matches)
        self._scroll_to_match()
        self._update_match_info()
