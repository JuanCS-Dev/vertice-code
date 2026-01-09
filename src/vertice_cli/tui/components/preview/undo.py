"""
Undo/Redo Stack - State management for preview changes.

Cursor-inspired undo/redo with visual history timeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from rich.table import Table

from .types import UndoRedoState


class UndoRedoStack:
    """Undo/Redo stack for preview changes (+5pts to match Cursor).

    Features:
    - Ctrl+Z / Ctrl+Y keyboard shortcuts
    - Visual history timeline
    - State snapshots with timestamps
    """

    def __init__(self, max_history: int = 50):
        """Initialize undo/redo stack.

        Args:
            max_history: Maximum number of states to keep.
        """
        self.undo_stack: List[UndoRedoState] = []
        self.redo_stack: List[UndoRedoState] = []
        self.max_history = max_history
        self.current_state: Optional[UndoRedoState] = None

    def push(self, content: str, description: str, hunks_applied: List[int] = None) -> None:
        """Push new state to undo stack.

        Args:
            content: Content snapshot.
            description: Description of the change.
            hunks_applied: List of hunk indices applied.
        """
        state = UndoRedoState(
            content=content,
            timestamp=datetime.now(),
            description=description,
            hunks_applied=hunks_applied or [],
        )

        self.undo_stack.append(state)
        self.redo_stack.clear()  # Clear redo stack on new action

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        self.current_state = state

    def undo(self) -> Optional[UndoRedoState]:
        """Undo last change.

        Returns:
            Previous state or None if nothing to undo.
        """
        if not self.can_undo():
            return None

        state = self.undo_stack.pop()
        self.redo_stack.append(state)

        if self.undo_stack:
            self.current_state = self.undo_stack[-1]
            return self.current_state
        else:
            self.current_state = None
            return None

    def redo(self) -> Optional[UndoRedoState]:
        """Redo last undone change.

        Returns:
            Redone state or None if nothing to redo.
        """
        if not self.can_redo():
            return None

        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.current_state = state
        return state

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def get_history(self) -> List[UndoRedoState]:
        """Get full history."""
        return self.undo_stack.copy()

    def render_history_timeline(self) -> Table:
        """Render visual timeline of changes.

        Returns:
            Rich Table with history timeline.
        """
        table = Table(title="Undo History", show_header=True, border_style="cyan")
        table.add_column("#", width=4, justify="right")
        table.add_column("Time", width=12)
        table.add_column("Action", width=40)
        table.add_column("Hunks", width=10, justify="center")

        for idx, state in enumerate(reversed(self.undo_stack[-10:]), 1):
            time_str = state.timestamp.strftime("%H:%M:%S")
            hunk_count = len(state.hunks_applied) if state.hunks_applied else 0

            style = "bold green" if state == self.current_state else "dim"
            marker = ">" if state == self.current_state else " "

            table.add_row(
                f"{marker}{idx}",
                time_str,
                state.description,
                str(hunk_count) if hunk_count > 0 else "-",
                style=style,
            )

        return table


__all__ = ["UndoRedoStack"]
