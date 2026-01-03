"""
Split View - Horizontal/Vertical split containers.

Resizable split containers for comparing content.

Phase 11: Visual Upgrade - Layout & Navigation.
"""

from __future__ import annotations

from typing import Optional, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Static
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message


class SplitHandle(Static):
    """Draggable handle for resizing splits."""

    DEFAULT_CSS = """
    SplitHandle {
        width: 1;
        height: 100%;
        background: $border;
    }

    SplitHandle:hover {
        background: $primary;
    }

    SplitHandle.horizontal {
        width: 100%;
        height: 1;
        cursor: row-resize;
    }

    SplitHandle.vertical {
        width: 1;
        height: 100%;
        cursor: col-resize;
    }

    SplitHandle.dragging {
        background: $accent;
    }
    """

    def __init__(
        self,
        orientation: str = "vertical",
        id: Optional[str] = None,
    ) -> None:
        super().__init__("│" if orientation == "vertical" else "─", id=id)
        self._orientation = orientation
        self.add_class(orientation)
        self._dragging = False

    def on_mouse_down(self, event) -> None:
        self._dragging = True
        self.add_class("dragging")
        self.capture_mouse()

    def on_mouse_up(self, event) -> None:
        self._dragging = False
        self.remove_class("dragging")
        self.release_mouse()

    def on_mouse_move(self, event) -> None:
        if self._dragging:
            self.post_message(SplitView.HandleDragged(
                delta_x=event.delta_x,
                delta_y=event.delta_y,
                orientation=self._orientation,
            ))


class SplitPane(Container):
    """Individual pane in a split view."""

    DEFAULT_CSS = """
    SplitPane {
        width: 1fr;
        height: 100%;
        overflow: auto;
    }

    SplitPane.horizontal {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(
        self,
        *children,
        orientation: str = "vertical",
        id: Optional[str] = None,
    ) -> None:
        super().__init__(*children, id=id)
        if orientation == "horizontal":
            self.add_class("horizontal")


class SplitView(Widget):
    """
    Resizable split container.

    Features:
    - Horizontal or vertical split
    - Draggable resize handle
    - Min/max pane sizes
    - Toggle split orientation
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+\\", "toggle_orientation", "Toggle Split", show=False),
        Binding("ctrl+shift+\\", "reset_split", "Reset Split", show=False),
    ]

    DEFAULT_CSS = """
    SplitView {
        width: 100%;
        height: 100%;
    }

    SplitView > Horizontal {
        width: 100%;
        height: 100%;
    }

    SplitView > Vertical {
        width: 100%;
        height: 100%;
    }
    """

    split_ratio: reactive[float] = reactive(0.5)
    orientation: reactive[str] = reactive("vertical")

    class HandleDragged(Message):
        """Handle was dragged."""
        def __init__(self, delta_x: int, delta_y: int, orientation: str) -> None:
            self.delta_x = delta_x
            self.delta_y = delta_y
            self.orientation = orientation
            super().__init__()

    class SplitChanged(Message):
        """Split ratio changed."""
        def __init__(self, ratio: float) -> None:
            self.ratio = ratio
            super().__init__()

    def __init__(
        self,
        orientation: str = "vertical",
        ratio: float = 0.5,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._initial_orientation = orientation
        self._initial_ratio = ratio
        self._left_content: Optional[Widget] = None
        self._right_content: Optional[Widget] = None

    def compose(self) -> ComposeResult:
        self.orientation = self._initial_orientation
        self.split_ratio = self._initial_ratio

        if self.orientation == "vertical":
            with Horizontal(id="split-container"):
                yield SplitPane(id="left-pane")
                yield SplitHandle(orientation="vertical", id="split-handle")
                yield SplitPane(id="right-pane")
        else:
            with Vertical(id="split-container"):
                yield SplitPane(orientation="horizontal", id="top-pane")
                yield SplitHandle(orientation="horizontal", id="split-handle")
                yield SplitPane(orientation="horizontal", id="bottom-pane")

    def on_mount(self) -> None:
        self._update_pane_sizes()

    def on_split_view_handle_dragged(self, event: HandleDragged) -> None:
        """Handle drag events from the split handle."""
        if event.orientation == "vertical":
            # Calculate new ratio based on x delta
            container_width = self.size.width
            if container_width > 0:
                delta_ratio = event.delta_x / container_width
                new_ratio = self.split_ratio + delta_ratio
                self.split_ratio = max(0.1, min(0.9, new_ratio))
        else:
            # Calculate new ratio based on y delta
            container_height = self.size.height
            if container_height > 0:
                delta_ratio = event.delta_y / container_height
                new_ratio = self.split_ratio + delta_ratio
                self.split_ratio = max(0.1, min(0.9, new_ratio))

    def watch_split_ratio(self, ratio: float) -> None:
        """Update pane sizes when ratio changes."""
        self._update_pane_sizes()
        self.post_message(self.SplitChanged(ratio))

    def _update_pane_sizes(self) -> None:
        """Update pane sizes based on ratio."""
        try:
            if self.orientation == "vertical":
                left = self.query_one("#left-pane", SplitPane)
                right = self.query_one("#right-pane", SplitPane)

                # Use percentages
                left_pct = int(self.split_ratio * 100)
                right_pct = 100 - left_pct - 1  # -1 for handle

                left.styles.width = f"{left_pct}%"
                right.styles.width = f"{right_pct}%"
            else:
                top = self.query_one("#top-pane", SplitPane)
                bottom = self.query_one("#bottom-pane", SplitPane)

                top_pct = int(self.split_ratio * 100)
                bottom_pct = 100 - top_pct - 1

                top.styles.height = f"{top_pct}%"
                bottom.styles.height = f"{bottom_pct}%"
        except Exception:
            pass

    def action_toggle_orientation(self) -> None:
        """Toggle between horizontal and vertical split."""
        self.orientation = "horizontal" if self.orientation == "vertical" else "vertical"
        self.refresh(layout=True)

    def action_reset_split(self) -> None:
        """Reset split to 50/50."""
        self.split_ratio = 0.5

    def set_left_content(self, widget: Widget) -> None:
        """Set content for left/top pane."""
        try:
            pane_id = "left-pane" if self.orientation == "vertical" else "top-pane"
            pane = self.query_one(f"#{pane_id}", SplitPane)
            pane.remove_children()
            pane.mount(widget)
        except Exception:
            pass

    def set_right_content(self, widget: Widget) -> None:
        """Set content for right/bottom pane."""
        try:
            pane_id = "right-pane" if self.orientation == "vertical" else "bottom-pane"
            pane = self.query_one(f"#{pane_id}", SplitPane)
            pane.remove_children()
            pane.mount(widget)
        except Exception:
            pass


class DualPane(Widget):
    """
    Simple two-pane split view.

    Convenience wrapper for common side-by-side layouts.
    """

    DEFAULT_CSS = """
    DualPane {
        width: 100%;
        height: 100%;
    }

    DualPane > Horizontal {
        width: 100%;
        height: 100%;
    }

    DualPane .pane-left {
        width: 1fr;
        height: 100%;
        border-right: solid $border;
    }

    DualPane .pane-right {
        width: 1fr;
        height: 100%;
    }
    """

    def __init__(
        self,
        left: Optional[Widget] = None,
        right: Optional[Widget] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._left = left
        self._right = right

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(classes="pane-left", id="dual-left"):
                if self._left:
                    yield self._left
            with Container(classes="pane-right", id="dual-right"):
                if self._right:
                    yield self._right
