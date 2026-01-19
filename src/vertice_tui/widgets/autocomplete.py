"""
Autocomplete Dropdown Widget.

Fuzzy autocomplete dropdown for commands and tools.
Shows suggestions as user types, with fuzzy matching.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static


class AutocompleteDropdown(VerticalScroll):
    """
    Fuzzy autocomplete dropdown for commands and tools.

    Shows suggestions as user types, with fuzzy matching.
    """

    DEFAULT_CSS = """
    AutocompleteDropdown {
        layer: autocomplete;
        background: $surface;
        border: round $primary;
        padding: 0 1;
        max-height: 16;
        min-height: 1;
        width: 100%;
        display: none;
        scrollbar-size: 0 0;
    }

    AutocompleteDropdown.visible {
        display: block;
    }

    AutocompleteDropdown .item {
        padding: 0 1;
        height: 1;
        color: $foreground;
    }

    AutocompleteDropdown .item.hidden {
        display: none;
    }

    AutocompleteDropdown .item.selected {
        background: $accent;
        color: $background;
    }

    AutocompleteDropdown .item-command {
        color: $primary;
    }

    AutocompleteDropdown .item-tool {
        color: $accent;
    }

    AutocompleteDropdown .item-file {
        color: $success;
    }

    AutocompleteDropdown .item-desc {
        color: $secondary;
    }
    """

    MAX_ITEMS: ClassVar[int] = 15

    selected_index: reactive[int] = reactive(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items: List[Dict] = []
        self._item_widgets: List[Static] = []

    def on_mount(self) -> None:
        """Pre-mount item widgets to avoid mount/remove churn per keystroke."""
        if self._item_widgets:
            return

        for _ in range(self.MAX_ITEMS):
            widget = Static("", classes="item hidden")
            self._item_widgets.append(widget)
            self.mount(widget)

    def show_completions(self, completions: List[Dict]) -> None:
        """Show completion items."""
        self.items = completions[: self.MAX_ITEMS]
        self.selected_index = 0

        if not self.items:
            self.hide()
            return

        with self.app.batch_update():
            for i, widget in enumerate(self._item_widgets):
                if i >= len(self.items):
                    widget.update("")
                    widget.add_class("hidden")
                    widget.remove_class("selected")
                    widget.set_class(False, "item-command")
                    widget.set_class(False, "item-tool")
                    widget.set_class(False, "item-file")
                    continue

                item = self.items[i]
                item_type = item.get("type", "tool")

                if "display" in item:
                    text = item["display"]
                else:
                    icon = "⚡" if item_type == "command" else "🔧"
                    text = f"{icon} {item['text']}"

                if desc := item.get("description"):
                    text += f" [dim]{desc}[/dim]"

                widget.update(text)
                widget.remove_class("hidden")
                widget.set_class(i == 0, "selected")
                widget.set_class(True, "item")
                widget.set_class(item_type == "command", "item-command")
                widget.set_class(item_type == "tool", "item-tool")
                widget.set_class(item_type == "file", "item-file")

        self.add_class("visible")

    def hide(self) -> None:
        """Hide dropdown."""
        with self.app.batch_update():
            self.remove_class("visible")
            for widget in self._item_widgets:
                widget.update("")
                widget.add_class("hidden")
                widget.remove_class("selected")
                widget.set_class(False, "item-command")
                widget.set_class(False, "item-tool")
                widget.set_class(False, "item-file")
        self.items = []

    def move_selection(self, delta: int) -> None:
        """Move selection up/down."""
        if not self.items:
            return

        # Update old selection
        if 0 <= self.selected_index < len(self.items):
            self._item_widgets[self.selected_index].remove_class("selected")

        # Calculate new index
        self.selected_index = (self.selected_index + delta) % len(self.items)

        # Update new selection
        if 0 <= self.selected_index < len(self.items):
            self._item_widgets[self.selected_index].add_class("selected")

    def get_selected(self) -> Optional[str]:
        """Get selected completion text."""
        if self.items and 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]["text"]
        return None
