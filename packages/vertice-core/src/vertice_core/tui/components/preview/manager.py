"""
Preview Manager - Manage multiple file previews.

Cursor-inspired workflow for reviewing changes.
"""

from __future__ import annotations

from typing import List, Optional

from .types import FileDiff


class PreviewManager:
    """Manage multiple file previews.

    Cursor-inspired workflow:
    1. AI generates changes
    2. Show preview with diff
    3. User reviews + accepts/rejects
    4. Apply changes only if accepted
    """

    def __init__(self):
        """Initialize preview manager."""
        self.pending_diffs: List[FileDiff] = []
        self.current_index = 0

    def add_preview(self, diff: FileDiff) -> None:
        """Add a file diff to preview queue.

        Args:
            diff: FileDiff to add.
        """
        self.pending_diffs.append(diff)

    def get_current_preview(self) -> Optional[FileDiff]:
        """Get current preview.

        Returns:
            Current FileDiff or None if no previews.
        """
        if 0 <= self.current_index < len(self.pending_diffs):
            return self.pending_diffs[self.current_index]
        return None

    def next_preview(self) -> None:
        """Move to next preview."""
        if self.current_index < len(self.pending_diffs) - 1:
            self.current_index += 1

    def previous_preview(self) -> None:
        """Move to previous preview."""
        if self.current_index > 0:
            self.current_index -= 1

    def has_previews(self) -> bool:
        """Check if there are pending previews.

        Returns:
            True if there are pending previews.
        """
        return len(self.pending_diffs) > 0

    def clear_previews(self) -> None:
        """Clear all previews."""
        self.pending_diffs.clear()
        self.current_index = 0


def create_preview_manager() -> PreviewManager:
    """Create a preview manager.

    Returns:
        New PreviewManager instance.
    """
    return PreviewManager()


__all__ = ["PreviewManager", "create_preview_manager"]
