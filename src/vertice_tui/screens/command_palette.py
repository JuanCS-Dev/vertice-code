"""
Command Palette Screen - Ctrl+K modal for quick command access.

Integrates existing CommandPaletteBridge with Textual ModalScreen.

Phase 11: Visual Upgrade - Interactive Components.
"""

from __future__ import annotations

from typing import Optional, List, Dict

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from rich.text import Text


class CommandPaletteScreen(ModalScreen[Optional[str]]):
    """
    Command palette modal with fuzzy search.

    Features:
    - Fuzzy search through commands
    - Category grouping
    - Keyboard navigation
    - Recent commands boost
    """

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    DEFAULT_CSS = """
    CommandPaletteScreen {
        align: center top;
        padding-top: 3;
    }

    CommandPaletteScreen > Vertical {
        width: 70;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 0;
    }

    CommandPaletteScreen .palette-header {
        background: $panel;
        height: 1;
        padding: 0 1;
        color: $text-muted;
    }

    CommandPaletteScreen Input {
        margin: 1;
        border: none;
        background: $surface;
    }

    CommandPaletteScreen .results {
        height: auto;
        max-height: 20;
        padding: 0 1;
        overflow-y: auto;
    }

    CommandPaletteScreen .result-item {
        height: 2;
        padding: 0 1;
    }

    CommandPaletteScreen .result-item.selected {
        background: $accent 20%;
    }

    CommandPaletteScreen .result-title {
        text-style: bold;
    }

    CommandPaletteScreen .result-desc {
        color: $text-muted;
    }

    CommandPaletteScreen .result-key {
        color: $accent;
        text-align: right;
    }

    CommandPaletteScreen .no-results {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    def __init__(self, bridge=None) -> None:
        super().__init__()
        self.bridge = bridge
        self._results: List[Dict] = []
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(" Command Palette (Ctrl+K)", classes="palette-header")
            yield Input(placeholder="Type to search commands...", id="search")
            yield Static("", classes="results", id="results")

    def on_mount(self) -> None:
        self.query_one("#search", Input).focus()
        self._update_results("")

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._select_current()

    def _update_results(self, query: str) -> None:
        """Update search results."""
        if self.bridge and hasattr(self.bridge, "palette"):
            self._results = self.bridge.palette.search(query, max_results=10)
        else:
            # Fallback: use CLI palette directly
            try:
                from vertice_cli.tui.components.palette import create_default_palette

                palette = create_default_palette()
                commands = palette.search(query, limit=10)
                self._results = [
                    {
                        "id": cmd.id,
                        "command": cmd.title,
                        "description": cmd.description,
                        "category": cmd.category.value,
                        "keybinding": cmd.keybinding,
                    }
                    for cmd in commands
                ]
            except ImportError:
                self._results = []

        self._selected_index = 0
        self._render_results()

    def _render_results(self) -> None:
        """Render results list."""
        results_widget = self.query_one("#results", Static)

        if not self._results:
            results_widget.update(Text("No commands found", style="dim"))
            return

        text = Text()
        for idx, result in enumerate(self._results):
            is_selected = idx == self._selected_index

            # Indicator
            if is_selected:
                text.append("▶ ", style="bold cyan")
            else:
                text.append("  ")

            # Title
            text.append(result.get("command", ""), style="bold" if is_selected else "")

            # Keybinding
            keybinding = result.get("keybinding")
            if keybinding:
                text.append(f"  [{keybinding}]", style="cyan dim")

            text.append("\n")

            # Description
            text.append("  ")
            text.append(result.get("description", ""), style="dim")
            text.append("\n")

        results_widget.update(text)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_move_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._render_results()

    def action_move_down(self) -> None:
        if self._selected_index < len(self._results) - 1:
            self._selected_index += 1
            self._render_results()

    def action_select(self) -> None:
        self._select_current()

    def _select_current(self) -> None:
        """Select and execute current command."""
        if not self._results:
            self.dismiss(None)
            return

        selected = self._results[self._selected_index]
        command_id = selected.get("id")

        # Execute via bridge if available
        if self.bridge and hasattr(self.bridge, "palette"):
            try:
                self.bridge.palette.execute(command_id)
            except (AttributeError, ValueError, KeyError):
                pass

        self.dismiss(command_id)
