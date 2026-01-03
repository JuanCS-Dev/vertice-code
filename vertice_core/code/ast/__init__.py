"""
AST Editor - Context-Aware Code Editing with Tree-sitter.

Implements intelligent code editing that understands code structure:
- Avoids matching strings and comments
- Finds symbols by their AST node type
- Provides semantic search within code
- Supports incremental parsing for fast updates

Usage:
    from vertice_core.code.ast import ASTEditor, get_ast_editor

    editor = get_ast_editor()  # Singleton
    matches = editor.find_in_code(content, "my_function", "python")
    result = editor.replace_in_code(content, "old_name", "new_name", "python")
"""

from typing import Optional

from .types import (
    NodeContext,
    CodeLocation,
    CodeMatch,
    CodeSymbol,
    EditResult,
)
from .languages import (
    LanguageConfig,
    LANGUAGE_CONFIGS,
    LANGUAGE_GRAMMARS,
    TREE_SITTER_AVAILABLE,
)
from .editor import ASTEditor


# Singleton instance
_ast_editor: Optional[ASTEditor] = None


def get_ast_editor() -> ASTEditor:
    """Get singleton AST editor instance."""
    global _ast_editor
    if _ast_editor is None:
        _ast_editor = ASTEditor()
    return _ast_editor


__all__ = [
    # Types
    "NodeContext",
    "CodeLocation",
    "CodeMatch",
    "CodeSymbol",
    "EditResult",
    # Languages
    "LanguageConfig",
    "LANGUAGE_CONFIGS",
    "LANGUAGE_GRAMMARS",
    "TREE_SITTER_AVAILABLE",
    # Editor
    "ASTEditor",
    "get_ast_editor",
]
