"""
Selectable Static Widget.

Static widget with mouse selection and copy support.
"""

from __future__ import annotations

from typing import Optional

from textual import events
from textual.geometry import Offset
from textual.widgets import Static

import pyperclip


class SelectableStatic(Static):
    """
    Static widget with mouse selection and copy support.

    Features:
    - Click and drag to select text
    - Right-click to copy selection
    - Double-click to select word
    """

    can_focus = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.selection_start: Optional[Offset] = None
        self.selection_end: Optional[Offset] = None
        self.selected_text: str = ""

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Start selection on mouse down."""
        # DISABLED: Allow terminal native mouse for copy/paste
        pass

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Update selection while dragging."""
        if self.selection_start and event.button == 1:
            self.selection_end = event.offset
            self._update_selection()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Finalize selection on mouse up."""
        if event.button == 1:  # Left click
            self.release_mouse()
            self._extract_selected_text()
        elif event.button == 3:  # Right click - copy to clipboard
            if self.selected_text:
                try:
                    pyperclip.copy(self.selected_text)
                    self.app.bell()  # Audio feedback
                except Exception as e:
                    # Clipboard access may fail in some environments
                    import logging

                    logging.warning(f"Clipboard copy failed: {e}")

    def on_double_click(self, event: events.Click) -> None:
        """Select word on double-click."""
        pass

    def _update_selection(self) -> None:
        """Update visual selection (highlighted area)."""
        pass

    def _extract_selected_text(self) -> None:
        """Extract selected text from widget."""
        if not self.selection_start or not self.selection_end:
            return

        try:
            if hasattr(self.renderable, "plain"):
                text = self.renderable.plain
            elif isinstance(self.renderable, str):
                text = self.renderable
            else:
                text = str(self.renderable)

            # For simplicity, copy entire content if there's a selection
            if (
                abs(self.selection_end.y - self.selection_start.y) > 0
                or abs(self.selection_end.x - self.selection_start.x) > 5
            ):
                self.selected_text = text
            else:
                self.selected_text = ""
        except (AttributeError, TypeError):
            self.selected_text = ""
