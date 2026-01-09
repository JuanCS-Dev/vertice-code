"""
Diff View Widget - Visual diff viewer (Cursor-inspired).

Rich-based widget for displaying file diffs.
"""

from __future__ import annotations

from typing import Callable, Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from vertice_cli.tui.theme import COLORS

from .types import ChangeType, FileDiff


class DiffView(Static):
    """Visual diff viewer (Cursor-inspired).

    Layout:
    +---------------------------------------------------+
    | file_path.py                           +10 -3 ~2  |
    +---------------------------------------------------+
    | @@ -10,7 +10,8 @@ function_name                    |
    | 10 | 10 |   def example():                        |
    | 11 |    | -     return "old"                      |
    |    | 11 | +     return "new"                      |
    | 12 | 12 |       pass                              |
    +---------------------------------------------------+
    | [A]ccept  [R]eject  [P]artial  [Q]uit             |
    +---------------------------------------------------+
    """

    def __init__(
        self,
        diff: FileDiff,
        on_accept: Optional[Callable] = None,
        on_reject: Optional[Callable] = None,
    ):
        """Initialize diff view.

        Args:
            diff: FileDiff to display.
            on_accept: Callback when accepted.
            on_reject: Callback when rejected.
        """
        super().__init__()
        self.diff = diff
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.selected_hunks: set = set(range(len(diff.hunks)))  # All selected by default

    def render(self) -> RenderableType:
        """Render the diff view.

        Returns:
            Rich renderable for display.
        """
        # Header with file path and stats
        stats = self.diff.stats
        header = Text()
        header.append("File: ", style="bold")
        header.append(self.diff.file_path, style=f"bold {COLORS['accent_blue']}")
        header.append(f"    +{stats['additions']}", style=f"bold {COLORS['diff_add_text']}")
        header.append(f" -{stats['deletions']}", style=f"bold {COLORS['diff_remove_text']}")
        if stats["modifications"] > 0:
            header.append(f" ~{stats['modifications']}", style=f"bold {COLORS['accent_yellow']}")

        # Build diff content
        content = Text()

        for idx, hunk in enumerate(self.diff.hunks):
            # Hunk header
            selected_marker = ">" if idx in self.selected_hunks else " "
            content.append(
                f"{selected_marker} {hunk.header}\n",
                style=f"bold {COLORS['accent_purple']}",
            )

            # Hunk lines
            for line in hunk.lines:
                # Line numbers
                old_num = str(line.line_num_old).rjust(4) if line.line_num_old else "    "
                new_num = str(line.line_num_new).rjust(4) if line.line_num_new else "    "

                # Change marker
                if line.change_type == ChangeType.ADDED:
                    marker = "+"
                elif line.change_type == ChangeType.REMOVED:
                    marker = "-"
                elif line.change_type == ChangeType.MODIFIED:
                    marker = "~"
                else:
                    marker = " "

                # Build line
                line_text = f"{old_num} | {new_num} | {marker} {line.content}\n"
                content.append(line_text, style=f"{line.color} on {line.bg_color}")

            content.append("\n")

        # Controls footer
        footer = Text()
        footer.append("[A]", style=f"bold {COLORS['accent_green']}")
        footer.append("ccept  ", style=COLORS["text_secondary"])
        footer.append("[R]", style=f"bold {COLORS['accent_red']}")
        footer.append("eject  ", style=COLORS["text_secondary"])
        footer.append("[P]", style=f"bold {COLORS['accent_yellow']}")
        footer.append("artial  ", style=COLORS["text_secondary"])
        footer.append("[Q]", style=f"bold {COLORS['text_tertiary']}")
        footer.append("uit", style=COLORS["text_secondary"])

        # Combine all parts
        full_content = Text()
        full_content.append(header)
        full_content.append("\n" + "-" * 70 + "\n", style=COLORS["border_default"])
        full_content.append(content)
        full_content.append("-" * 70 + "\n", style=COLORS["border_default"])
        full_content.append(footer)

        return Panel(
            full_content,
            border_style=COLORS["border_emphasis"],
            title="[bold]Preview Changes[/bold]",
            title_align="left",
        )


__all__ = ["DiffView"]
