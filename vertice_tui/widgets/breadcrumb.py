"""
Breadcrumb Navigation - Context path display.

Shows current location with clickable navigation.

Phase 11: Visual Upgrade - Layout & Navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Union

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from textual.widget import Widget
from textual.message import Message

from rich.text import Text


class BreadcrumbItem(Static):
    """Single breadcrumb item."""

    DEFAULT_CSS = """
    BreadcrumbItem {
        width: auto;
        height: 1;
        padding: 0 1;
    }

    BreadcrumbItem:hover {
        background: $accent 20%;
        text-style: underline;
    }

    BreadcrumbItem.current {
        text-style: bold;
    }

    BreadcrumbItem.separator {
        color: $text-muted;
        padding: 0;
    }

    BreadcrumbItem.separator:hover {
        background: transparent;
        text-style: none;
    }
    """

    def __init__(
        self,
        label: str,
        path: Optional[str] = None,
        is_current: bool = False,
        is_separator: bool = False,
        id: Optional[str] = None,
    ) -> None:
        self.path = path
        self._is_separator = is_separator

        if is_separator:
            super().__init__("›", id=id, classes="separator")
        else:
            super().__init__(label, id=id)
            if is_current:
                self.add_class("current")

    def on_click(self) -> None:
        if not self._is_separator and self.path:
            self.post_message(Breadcrumb.ItemClicked(self.path))


class Breadcrumb(Widget):
    """
    Breadcrumb navigation widget.

    Features:
    - Path-based navigation
    - Clickable items
    - Intelligent truncation
    - Custom separators
    """

    DEFAULT_CSS = """
    Breadcrumb {
        width: 100%;
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    Breadcrumb > Horizontal {
        width: 100%;
        height: 1;
    }

    Breadcrumb .breadcrumb-icon {
        width: 2;
        color: $primary;
    }
    """

    class ItemClicked(Message):
        """Breadcrumb item was clicked."""

        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    def __init__(
        self,
        path: Optional[Union[str, Path, List[str]]] = None,
        max_items: int = 5,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._max_items = max_items
        self._path_items: List[tuple[str, str]] = []

        if path:
            self.set_path(path)

    def compose(self) -> ComposeResult:
        with Horizontal(id="breadcrumb-container"):
            yield Static("📍", classes="breadcrumb-icon")
            # Items added dynamically

    def set_path(self, path: Union[str, Path, List[str]]) -> None:
        """Set the breadcrumb path."""
        if isinstance(path, Path):
            # Convert Path to parts
            self._path_items = [
                (part, str(Path(*path.parts[: i + 1])))
                for i, part in enumerate(path.parts)
                if part != "/"
            ]
        elif isinstance(path, list):
            # List of labels
            self._path_items = [(label, "/".join(path[: i + 1])) for i, label in enumerate(path)]
        else:
            # String path
            parts = path.strip("/").split("/")
            self._path_items = [
                (part, "/".join(parts[: i + 1])) for i, part in enumerate(parts) if part
            ]

        self._render_breadcrumb()

    def set_items(self, items: List[tuple[str, str]]) -> None:
        """Set breadcrumb items directly (label, path) tuples."""
        self._path_items = items
        self._render_breadcrumb()

    def _render_breadcrumb(self) -> None:
        """Render the breadcrumb items."""
        try:
            container = self.query_one("#breadcrumb-container", Horizontal)

            # Remove old items (keep icon)
            for child in list(container.children)[1:]:
                child.remove()

            if not self._path_items:
                return

            # Truncate if needed
            items = self._path_items
            if len(items) > self._max_items:
                # Show first, ellipsis, last N-1
                truncated = [items[0]]
                truncated.append(("...", ""))
                truncated.extend(items[-(self._max_items - 2) :])
                items = truncated

            # Add items with separators
            for i, (label, path) in enumerate(items):
                is_current = i == len(items) - 1

                if label == "...":
                    container.mount(BreadcrumbItem("...", is_separator=True))
                else:
                    container.mount(
                        BreadcrumbItem(
                            label,
                            path=path,
                            is_current=is_current,
                        )
                    )

                # Add separator except after last item
                if i < len(items) - 1 and label != "...":
                    container.mount(BreadcrumbItem("", is_separator=True))

        except (AttributeError, ValueError, RuntimeError):
            pass

    def push(self, label: str, path: Optional[str] = None) -> None:
        """Add item to breadcrumb."""
        if path is None:
            if self._path_items:
                path = f"{self._path_items[-1][1]}/{label}"
            else:
                path = label

        self._path_items.append((label, path))
        self._render_breadcrumb()

    def pop(self) -> Optional[tuple[str, str]]:
        """Remove last item from breadcrumb."""
        if self._path_items:
            item = self._path_items.pop()
            self._render_breadcrumb()
            return item
        return None

    def clear(self) -> None:
        """Clear all breadcrumb items."""
        self._path_items = []
        self._render_breadcrumb()

    def navigate_to(self, path: str) -> None:
        """Navigate to a specific path in the breadcrumb."""
        # Find the path and truncate to that point
        for i, (_, item_path) in enumerate(self._path_items):
            if item_path == path:
                self._path_items = self._path_items[: i + 1]
                self._render_breadcrumb()
                break


class ContextBreadcrumb(Breadcrumb):
    """
    Context-aware breadcrumb for AI conversations.

    Shows: Mode > Agent > Tool > Action
    """

    def __init__(self, id: Optional[str] = None) -> None:
        super().__init__(id=id)
        self._mode = "Chat"
        self._agent: Optional[str] = None
        self._tool: Optional[str] = None
        self._action: Optional[str] = None

    def set_mode(self, mode: str) -> None:
        """Set current mode (Chat, Plan, Review, etc)."""
        self._mode = mode
        self._update_context()

    def set_agent(self, agent: Optional[str]) -> None:
        """Set current agent."""
        self._agent = agent
        self._update_context()

    def set_tool(self, tool: Optional[str]) -> None:
        """Set current tool being used."""
        self._tool = tool
        self._update_context()

    def set_action(self, action: Optional[str]) -> None:
        """Set current action."""
        self._action = action
        self._update_context()

    def _update_context(self) -> None:
        """Update breadcrumb from context."""
        items = [(self._mode, self._mode)]

        if self._agent:
            items.append((self._agent, f"{self._mode}/{self._agent}"))

        if self._tool:
            path = f"{self._mode}/{self._agent or 'default'}/{self._tool}"
            items.append((self._tool, path))

        if self._action:
            path = (
                f"{self._mode}/{self._agent or 'default'}/{self._tool or 'default'}/{self._action}"
            )
            items.append((self._action, path))

        self.set_items(items)

    def clear_context(self) -> None:
        """Reset to default state."""
        self._mode = "Chat"
        self._agent = None
        self._tool = None
        self._action = None
        self._update_context()
