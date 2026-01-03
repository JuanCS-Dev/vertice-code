"""
Diff View Widget - VERTICE TUI Visual Upgrade.

Simple diff visualization using Python's difflib.
Shows unified diff with color-coded additions/deletions.

Phase 11: Visual Upgrade Sprint 1.

References:
- https://claudelog.com/faqs/claude-code-vscode-view-code-changes-diffs/
- https://docs.python.org/3/library/difflib.html
"""

from __future__ import annotations

import difflib
from typing import Optional, List

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static
from textual.widget import Widget

from rich.text import Text
from rich.style import Style


# Diff line styles (Rich doesn't support alpha in hex colors)
STYLE_ADDITION = Style(color="#22C55E", bold=True)  # Green
STYLE_DELETION = Style(color="#EF4444", strike=True)  # Red
STYLE_CONTEXT = Style(color="#94A3B8")  # Muted
STYLE_HEADER = Style(color="#3B82F6", bold=True)  # Blue
STYLE_HUNK = Style(color="#8B5CF6")  # Purple
STYLE_LINE_NUM = Style(color="#64748B", dim=True)


class DiffView(Widget):
    """
    Widget to display file diffs with color-coding.

    Features:
    - Unified diff format
    - Color-coded additions (green) and deletions (red)
    - Line numbers
    - Header with file names

    Usage:
        diff = DiffView()
        diff.set_diff(old_text, new_text, "original.py", "modified.py")
    """

    DEFAULT_CSS = """
    DiffView {
        width: 100%;
        height: auto;
        min-height: 3;
        background: $surface;
        border: round $border;
        padding: 0;
    }

    DiffView .diff-header {
        background: $panel;
        color: $primary;
        height: 1;
        padding: 0 1;
        text-style: bold;
    }

    DiffView .diff-content {
        padding: 0 1;
    }

    DiffView .diff-stats {
        background: $panel;
        height: 1;
        padding: 0 1;
        dock: bottom;
    }
    """

    def __init__(
        self,
        old_text: str = "",
        new_text: str = "",
        old_name: str = "original",
        new_name: str = "modified",
        context_lines: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.old_text = old_text
        self.new_text = new_text
        self.old_name = old_name
        self.new_name = new_name
        self.context_lines = context_lines
        self._additions = 0
        self._deletions = 0

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), classes="diff-header")
        yield Static(self._render_diff(), classes="diff-content")
        yield Static(self._format_stats(), classes="diff-stats")

    def set_diff(
        self,
        old_text: str,
        new_text: str,
        old_name: str = "original",
        new_name: str = "modified",
    ) -> None:
        """Set diff content and refresh display."""
        self.old_text = old_text
        self.new_text = new_text
        self.old_name = old_name
        self.new_name = new_name
        self.refresh()

    def _format_header(self) -> str:
        """Format diff header."""
        return f" {self.old_name} → {self.new_name}"

    def _format_stats(self) -> str:
        """Format diff statistics."""
        return f"[#22C55E]+{self._additions}[/] [#EF4444]-{self._deletions}[/] lines"

    def _render_diff(self) -> Text:
        """Render unified diff with colors."""
        if not self.old_text and not self.new_text:
            return Text("No changes", style=STYLE_CONTEXT)

        old_lines = self.old_text.splitlines(keepends=True)
        new_lines = self.new_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=self.old_name,
            tofile=self.new_name,
            n=self.context_lines,
        )

        result = Text()
        self._additions = 0
        self._deletions = 0
        line_num = 0

        for line in diff:
            line_num += 1
            line_stripped = line.rstrip('\n')

            # Line number prefix
            result.append(f"{line_num:4d} ", style=STYLE_LINE_NUM)

            if line.startswith('+++') or line.startswith('---'):
                result.append(line_stripped, style=STYLE_HEADER)
            elif line.startswith('@@'):
                result.append(line_stripped, style=STYLE_HUNK)
            elif line.startswith('+'):
                result.append(line_stripped, style=STYLE_ADDITION)
                self._additions += 1
            elif line.startswith('-'):
                result.append(line_stripped, style=STYLE_DELETION)
                self._deletions += 1
            else:
                result.append(line_stripped, style=STYLE_CONTEXT)

            result.append('\n')

        if not result.plain:
            return Text("No differences", style=STYLE_CONTEXT)

        return result

    def refresh(self, *args, **kwargs) -> None:
        """Refresh the diff display."""
        try:
            self.query_one(".diff-header", Static).update(self._format_header())
            self.query_one(".diff-content", Static).update(self._render_diff())
            self.query_one(".diff-stats", Static).update(self._format_stats())
        except Exception:
            pass
        super().refresh(*args, **kwargs)


class InlineDiff(Static):
    """
    Simple inline diff display for small changes.

    Shows additions in green and deletions in red inline.
    """

    DEFAULT_CSS = """
    InlineDiff {
        padding: 0 1;
    }
    """

    def __init__(
        self,
        old_text: str = "",
        new_text: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.old_text = old_text
        self.new_text = new_text
        self.update(self._render_inline())

    def set_diff(self, old_text: str, new_text: str) -> None:
        """Update the inline diff."""
        self.old_text = old_text
        self.new_text = new_text
        self.update(self._render_inline())

    def _render_inline(self) -> Text:
        """Render inline character-level diff."""
        result = Text()

        if not self.old_text and self.new_text:
            result.append(self.new_text, style=STYLE_ADDITION)
            return result

        if self.old_text and not self.new_text:
            result.append(self.old_text, style=STYLE_DELETION)
            return result

        # Character-level diff
        matcher = difflib.SequenceMatcher(None, self.old_text, self.new_text)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                result.append(self.old_text[i1:i2], style=STYLE_CONTEXT)
            elif tag == 'replace':
                result.append(self.old_text[i1:i2], style=STYLE_DELETION)
                result.append(self.new_text[j1:j2], style=STYLE_ADDITION)
            elif tag == 'delete':
                result.append(self.old_text[i1:i2], style=STYLE_DELETION)
            elif tag == 'insert':
                result.append(self.new_text[j1:j2], style=STYLE_ADDITION)

        return result


def create_diff_text(
    old_text: str,
    new_text: str,
    old_name: str = "original",
    new_name: str = "modified",
) -> Text:
    """
    Create a Rich Text object with colored diff.

    Utility function for embedding diffs in other widgets.

    Args:
        old_text: Original text
        new_text: Modified text
        old_name: Original file name
        new_name: Modified file name

    Returns:
        Rich Text with styled diff
    """
    view = DiffView(old_text, new_text, old_name, new_name)
    return view._render_diff()


__all__ = [
    "DiffView",
    "InlineDiff",
    "create_diff_text",
]
