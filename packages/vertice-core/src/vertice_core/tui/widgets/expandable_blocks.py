"""
Expandable render blocks (code / diff) for long sessions.

Goal: keep scrollback responsive by avoiding expensive renderables (e.g. Rich Syntax)
for very large blocks unless the user explicitly expands them.
"""

from __future__ import annotations

from typing import Final

from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.reactive import reactive
from textual.widgets import Static

from vertice_core.tui.core.formatting import Colors, Icons


class ExpandableCodeBlock(Static):
    """Code block that renders a cheap preview until expanded."""

    can_focus: Final[bool] = True

    expanded: reactive[bool] = reactive(False)

    def __init__(
        self,
        code: str,
        *,
        language: str = "text",
        title: str | None = None,
        file_path: str | None = None,
        max_preview_lines: int = 200,
        **kwargs,
    ) -> None:
        self._code = code.strip("\n")
        self._language = language or "text"
        self._title = title
        self._file_path = file_path
        self._max_preview_lines = max(1, max_preview_lines)

        self._code_lines = self._code.splitlines() if self._code else [""]
        self._is_truncated = len(self._code_lines) > self._max_preview_lines
        self._expanded_panel: Panel | None = None

        super().__init__(self._render_collapsed(), **kwargs)

        self.add_class("code-block")
        if self._is_truncated:
            self.add_class("truncated")

    @property
    def total_lines(self) -> int:
        return len(self._code_lines)

    @property
    def is_truncated(self) -> bool:
        return self._is_truncated

    def on_click(self, event: events.Click) -> None:
        self.expanded = not self.expanded
        event.stop()

    def on_key(self, event: events.Key) -> None:
        if event.key in {"enter", "space"}:
            self.expanded = not self.expanded
            event.stop()

    def watch_expanded(self, expanded: bool) -> None:
        self.set_class(expanded, "expanded")
        if expanded:
            self.update(self._render_expanded())
        else:
            # Free heavy renderables when collapsing to keep long-session memory stable.
            self._expanded_panel = None
            self.update(self._render_collapsed())

    def _format_panel_title(self, *, expanded: bool) -> str:
        symbol = "▼" if expanded else "▶"
        header_parts = [f"{symbol} {Icons.CODE_FILE} {self._language.upper()}"]
        if self._file_path:
            header_parts.append(f"[{Colors.MUTED}]{self._file_path}[/]")
        elif self._title:
            header_parts.append(f"[{Colors.MUTED}]{self._title}[/]")
        return " ".join(header_parts)

    def _render_collapsed(self) -> Panel:
        preview_lines = self._code_lines[: self._max_preview_lines]
        omitted = max(len(self._code_lines) - len(preview_lines), 0)

        content = Text("\n".join(preview_lines), style=Colors.FOREGROUND)
        if omitted:
            content.append(
                f"\n\n… +{omitted:,} lines (click/Enter to expand)",
                style=Colors.MUTED,
            )

        return Panel(
            content,
            title=f"[bold {Colors.PRIMARY}]{self._format_panel_title(expanded=False)}[/]",
            title_align="left",
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_expanded(self) -> Panel:
        if self._expanded_panel is None:
            syntax = Syntax(
                self._code,
                self._language,
                theme="one-dark",
                line_numbers=True,
                word_wrap=True,
                background_color=Colors.SURFACE,
            )
            self._expanded_panel = Panel(
                syntax,
                title=f"[bold {Colors.PRIMARY}]{self._format_panel_title(expanded=True)}[/]",
                title_align="left",
                border_style=Colors.BORDER,
                box=box.ROUNDED,
                padding=(0, 1),
            )
        return self._expanded_panel


__all__ = ["ExpandableCodeBlock"]


class ExpandableDiffBlock(Static):
    """Diff block that renders a cheap preview until expanded."""

    can_focus: Final[bool] = True

    expanded: reactive[bool] = reactive(False)

    def __init__(
        self,
        diff_content: str,
        *,
        title: str = "Diff",
        file_path: str | None = None,
        max_preview_lines: int = 400,
        **kwargs,
    ) -> None:
        self._diff = diff_content.strip("\n")
        self._title = title
        self._file_path = file_path
        self._max_preview_lines = max(1, max_preview_lines)

        self._diff_lines = self._diff.splitlines() if self._diff else [""]
        self._is_truncated = len(self._diff_lines) > self._max_preview_lines
        self._expanded_panel: Panel | None = None

        super().__init__(self._render_collapsed(), **kwargs)

        self.add_class("diff-block")
        if self._is_truncated:
            self.add_class("truncated")

    @property
    def total_lines(self) -> int:
        return len(self._diff_lines)

    @property
    def is_truncated(self) -> bool:
        return self._is_truncated

    def on_click(self, event: events.Click) -> None:
        if self._is_truncated:
            self.expanded = not self.expanded
            event.stop()

    def on_key(self, event: events.Key) -> None:
        if not self._is_truncated:
            return
        if event.key in {"enter", "space"}:
            self.expanded = not self.expanded
            event.stop()

    def watch_expanded(self, expanded: bool) -> None:
        if not self._is_truncated:
            return
        self.set_class(expanded, "expanded")
        if expanded:
            self.update(self._render_expanded())
        else:
            # Free heavy renderables when collapsing to keep long-session memory stable.
            self._expanded_panel = None
            self.update(self._render_collapsed())

    def _format_panel_title(self, *, expanded: bool) -> str:
        symbol = "▼" if expanded else "▶"
        header = f"{symbol} {Icons.GIT} {self._title}"
        if self._file_path:
            header += f" [{Colors.MUTED}]{self._file_path}[/]"
        return header

    def _build_diff_text(self, lines: list[str]) -> Text:
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
        return result

    def _render_collapsed(self) -> Panel:
        preview_lines = self._diff_lines[: self._max_preview_lines]
        omitted = max(len(self._diff_lines) - len(preview_lines), 0)

        content = self._build_diff_text(preview_lines)
        if omitted:
            content.append(
                f"\n… +{omitted:,} lines (click/Enter to expand)",
                style=Colors.MUTED,
            )

        return Panel(
            content,
            title=f"[bold {Colors.PRIMARY}]{self._format_panel_title(expanded=False)}[/]",
            title_align="left",
            border_style=Colors.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_expanded(self) -> Panel:
        if self._expanded_panel is None:
            content = self._build_diff_text(self._diff_lines)
            self._expanded_panel = Panel(
                content,
                title=f"[bold {Colors.PRIMARY}]{self._format_panel_title(expanded=True)}[/]",
                title_align="left",
                border_style=Colors.BORDER,
                box=box.ROUNDED,
                padding=(0, 1),
            )
        return self._expanded_panel


__all__.append("ExpandableDiffBlock")
