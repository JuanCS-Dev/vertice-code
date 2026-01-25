"""
Preview Types - Domain models for diff preview.

Enums and dataclasses for diff representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from vertice_core.vertice_core.tui.theme import COLORS


class ChangeType(Enum):
    """Type of change in diff."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffLine:
    """Single line in a diff."""

    line_num_old: Optional[int]
    line_num_new: Optional[int]
    content: str
    change_type: ChangeType

    @property
    def color(self) -> str:
        """Get color for this line type."""
        if self.change_type == ChangeType.ADDED:
            return COLORS["diff_add_text"]
        elif self.change_type == ChangeType.REMOVED:
            return COLORS["diff_remove_text"]
        elif self.change_type == ChangeType.MODIFIED:
            return COLORS["accent_yellow"]
        else:
            return COLORS["text_secondary"]

    @property
    def bg_color(self) -> str:
        """Get background color for this line."""
        if self.change_type == ChangeType.ADDED:
            return COLORS["diff_add_bg"]
        elif self.change_type == ChangeType.REMOVED:
            return COLORS["diff_remove_bg"]
        else:
            return COLORS["bg_primary"]


@dataclass
class DiffHunk:
    """A continuous block of changes (hunk).

    Similar to git diff hunks:
    @@ -10,7 +10,8 @@ function_name
    """

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]
    context: str = ""  # Function/class context

    @property
    def header(self) -> str:
        """Get hunk header (git-style)."""
        header = f"@@ -{self.old_start},{self.old_count} +{self.new_start},{self.new_count} @@"
        if self.context:
            header += f" {self.context}"
        return header


@dataclass
class FileDiff:
    """Complete diff for a single file."""

    file_path: str
    language: str  # For syntax highlighting
    old_content: str
    new_content: str
    hunks: List[DiffHunk]

    @property
    def stats(self) -> Dict[str, int]:
        """Get diff statistics."""
        additions = sum(
            1 for hunk in self.hunks for line in hunk.lines if line.change_type == ChangeType.ADDED
        )
        deletions = sum(
            1
            for hunk in self.hunks
            for line in hunk.lines
            if line.change_type == ChangeType.REMOVED
        )
        modifications = sum(
            1
            for hunk in self.hunks
            for line in hunk.lines
            if line.change_type == ChangeType.MODIFIED
        )

        return {
            "additions": additions,
            "deletions": deletions,
            "modifications": modifications,
            "total_changes": additions + deletions + modifications,
        }


@dataclass
class UndoRedoState:
    """State snapshot for undo/redo."""

    content: str
    timestamp: datetime
    description: str
    hunks_applied: List[int] = None

    def __post_init__(self):
        if self.hunks_applied is None:
            self.hunks_applied = []


__all__ = [
    "ChangeType",
    "DiffLine",
    "DiffHunk",
    "FileDiff",
    "UndoRedoState",
]
