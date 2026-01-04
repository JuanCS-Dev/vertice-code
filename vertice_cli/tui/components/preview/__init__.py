"""
Preview Module - Real-Time Edit Preview (Cursor-inspired).

Submodules:
    - types: Domain models (ChangeType, DiffLine, etc.)
    - undo: UndoRedoStack for state management
    - generator: DiffGenerator for creating diffs
    - widgets: DiffView visual widget
    - manager: PreviewManager for multiple files
    - interactive: EditPreview interactive review

Features:
    - Side-by-side diff view (original vs proposed)
    - Syntax highlighting for both sides
    - Line-by-line changes (additions, deletions, modifications)
    - Accept/Reject controls
    - Partial accept (select specific hunks)
    - Undo support
    - Git-style diff colors
"""

from .types import (
    ChangeType,
    DiffLine,
    DiffHunk,
    FileDiff,
    UndoRedoState,
)
from .undo import UndoRedoStack
from .generator import DiffGenerator, preview_file_change
from .widgets import DiffView
from .manager import PreviewManager, create_preview_manager
from .interactive import EditPreview

__all__ = [
    # Types
    "ChangeType",
    "DiffLine",
    "DiffHunk",
    "FileDiff",
    "UndoRedoState",
    # Undo
    "UndoRedoStack",
    # Generator
    "DiffGenerator",
    "preview_file_change",
    # Widgets
    "DiffView",
    # Manager
    "PreviewManager",
    "create_preview_manager",
    # Interactive
    "EditPreview",
]
