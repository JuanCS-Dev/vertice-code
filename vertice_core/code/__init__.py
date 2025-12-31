"""
Code Intelligence Module - Sprint 3.

Components:
- LSPClient: Unified Language Server Protocol client
- ASTEditor: Context-aware code editing with Tree-sitter
- CodeValidator: Post-edit validation with LSP diagnostics

Features:
- Multi-language LSP support (Python, TypeScript, Go, Rust, etc.)
- AST-aware search and replace (avoids strings/comments)
- Before/after validation pattern (Claude Code/Codex style)
- Automatic rollback on validation failure

Phase 10: Sprint 3 - Code Intelligence

Soli Deo Gloria
"""

from __future__ import annotations

from .lsp_client import (
    # Types
    DiagnosticSeverity,
    SymbolKind,
    Position,
    Range,
    Location,
    Diagnostic,
    DocumentSymbol,
    HoverInfo,
    CompletionItem,
    LanguageServerConfig,
    # Exceptions
    JsonRpcError,
    LSPConnectionError,
    LSPTimeoutError,
    # Client
    LSPClient,
    get_lsp_client,
    close_lsp_client,
    # Configs
    DEFAULT_LANGUAGE_SERVERS,
)

from .ast_editor import (
    NodeContext,
    CodeLocation,
    CodeMatch,
    CodeSymbol,
    EditResult,
    LanguageConfig,
    ASTEditor,
    get_ast_editor,
    LANGUAGE_CONFIGS,
    TREE_SITTER_AVAILABLE,
)

from .validator import (
    ValidationLevel,
    CheckType,
    Check,
    ValidationResult,
    EditValidation,
    FileBackup,
    CodeValidator,
    validate_file,
    validate_edit,
)

__all__ = [
    # LSP Client
    "DiagnosticSeverity",
    "SymbolKind",
    "Position",
    "Range",
    "Location",
    "Diagnostic",
    "DocumentSymbol",
    "HoverInfo",
    "CompletionItem",
    "LanguageServerConfig",
    "JsonRpcError",
    "LSPConnectionError",
    "LSPTimeoutError",
    "LSPClient",
    "get_lsp_client",
    "close_lsp_client",
    "DEFAULT_LANGUAGE_SERVERS",
    # AST Editor
    "NodeContext",
    "CodeLocation",
    "CodeMatch",
    "CodeSymbol",
    "EditResult",
    "LanguageConfig",
    "ASTEditor",
    "get_ast_editor",
    "LANGUAGE_CONFIGS",
    "TREE_SITTER_AVAILABLE",
    # Validator
    "ValidationLevel",
    "CheckType",
    "Check",
    "ValidationResult",
    "EditValidation",
    "FileBackup",
    "CodeValidator",
    "validate_file",
    "validate_edit",
]
