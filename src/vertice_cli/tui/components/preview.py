"""
Real-Time Edit Preview - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- preview/types.py: ChangeType, DiffLine, DiffHunk, FileDiff, UndoRedoState
- preview/undo.py: UndoRedoStack
- preview/generator.py: DiffGenerator
- preview/widgets.py: DiffView
- preview/manager.py: PreviewManager
- preview/interactive.py: EditPreview

All symbols are re-exported here for backward compatibility.
Import from 'preview' subpackage for new code.

Features:
- Side-by-side diff view (original vs proposed)
- Syntax highlighting for both sides
- Line-by-line changes (additions, deletions, modifications)
- Accept/Reject controls
- Partial accept (select specific hunks)
- Undo support
- Git-style diff colors
"""

# Re-export all public symbols for backward compatibility
from .preview import (
    # Types
    ChangeType,
    DiffLine,
    DiffHunk,
    FileDiff,
    UndoRedoState,
    # Undo
    UndoRedoStack,
    # Generator
    DiffGenerator,
    preview_file_change,
    # Widgets
    DiffView,
    # Manager
    PreviewManager,
    create_preview_manager,
    # Interactive
    EditPreview,
)

__all__ = [
    "ChangeType",
    "DiffLine",
    "DiffHunk",
    "FileDiff",
    "UndoRedoState",
    "UndoRedoStack",
    "DiffGenerator",
    "preview_file_change",
    "DiffView",
    "PreviewManager",
    "create_preview_manager",
    "EditPreview",
]
