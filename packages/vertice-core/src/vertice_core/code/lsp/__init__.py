"""
LSP Module - Unified Language Server Protocol Client.

Provides multi-language LSP support:
- Python (pylsp)
- TypeScript/JavaScript (typescript-language-server)
- Go (gopls)
- Rust (rust-analyzer)
- Java (jdtls)
- C/C++ (clangd)

Performance target: 50ms for go-to-definition (vs 45s grep)

Usage:
    from vertice_core.code.lsp import LSPClient, get_lsp_client

    async with LSPClient(workspace_root) as client:
        location = await client.goto_definition("file.py", 10, 5)
"""

# Types
from .types import (
    DiagnosticSeverity,
    SymbolKind,
    Position,
    Range,
    Location,
    Diagnostic,
    DocumentSymbol,
    HoverInfo,
    CompletionItem,
)

# Config
from .config import (
    LanguageServerConfig,
    DEFAULT_LANGUAGE_SERVERS,
)

# Exceptions
from .exceptions import (
    JsonRpcError,
    LSPConnectionError,
    LSPTimeoutError,
)

# Protocol
from .protocol import JsonRpcConnection

# Client
from .client import (
    LSPClient,
    get_lsp_client,
    close_lsp_client,
)

__all__ = [
    # Types
    "DiagnosticSeverity",
    "SymbolKind",
    "Position",
    "Range",
    "Location",
    "Diagnostic",
    "DocumentSymbol",
    "HoverInfo",
    "CompletionItem",
    # Config
    "LanguageServerConfig",
    "DEFAULT_LANGUAGE_SERVERS",
    # Exceptions
    "JsonRpcError",
    "LSPConnectionError",
    "LSPTimeoutError",
    # Protocol
    "JsonRpcConnection",
    # Client
    "LSPClient",
    "get_lsp_client",
    "close_lsp_client",
]
