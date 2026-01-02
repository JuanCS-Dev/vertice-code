"""
Command Handlers Module - SCALE & SUSTAIN Phase 1.2+.

Extracted from shell_main.py to reduce cyclomatic complexity.

Components:
- CommandDispatcher: Routes commands to handlers
- LSPHandler: All LSP-related commands
- BasicHandler: Basic system commands (/help, /exit, etc.)
- HistoryHandler: History and session commands
- WorkflowHandler: Workflow and squad commands
- IndexHandler: Indexing and search commands
- RefactorHandler: Refactoring commands
- GitHandler: Git operations (Phase 1.3)
- FileOpsHandler: File operations (Phase 1.3)
- InputHandler: User input processing (Phase 1.2.4)

Author: Vertice Team
Date: 2025-11-26
Updated: 2026-01-02 (Phase 1.3 - Git/FileOps handlers)
"""

from .dispatcher import CommandDispatcher, CommandResult
from .lsp_handler import LSPHandler
from .basic_handler import BasicHandler
from .history_handler import HistoryHandler
from .workflow_handler import WorkflowHandler
from .index_handler import IndexHandler
from .refactor_handler import RefactorHandler
from .git_handler import GitHandler
from .file_ops_handler import FileOpsHandler
from .input_handler import (
    InputHandler,
    InputType,
    ParsedInput,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    'CommandDispatcher',
    'CommandResult',
    'LSPHandler',
    'BasicHandler',
    'HistoryHandler',
    'WorkflowHandler',
    'IndexHandler',
    'RefactorHandler',
    'GitHandler',
    'FileOpsHandler',
    'InputHandler',
    'InputType',
    'ParsedInput',
    'ValidationResult',
    'ValidationStatus',
]
