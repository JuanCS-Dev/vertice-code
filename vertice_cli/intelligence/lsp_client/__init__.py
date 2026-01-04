"""
LSP Client Module - Language Server Protocol client for code intelligence.

This package provides LSP-based code intelligence:
- Hover documentation
- Go-to-definition
- Find references
- Code completion
- Signature help

Submodules:
    - types: Core LSP types (Language, Position, Range, etc.)
    - responses: Response data structures (HoverInfo, CompletionItem, etc.)
    - client: LSPClient class

Usage:
    from vertice_cli.intelligence.lsp_client import LSPClient, Language
    from vertice_cli.intelligence.lsp_client import HoverInfo, CompletionItem
"""

from .types import (
    Language,
    LSPServerConfig,
    LSPFeature,
    Position,
    Range,
    Location,
    Diagnostic,
)
from .responses import (
    HoverInfo,
    CompletionItem,
    ParameterInformation,
    SignatureInformation,
    SignatureHelp,
)
from .client import LSPClient


__all__ = [
    # Types
    "Language",
    "LSPServerConfig",
    "LSPFeature",
    "Position",
    "Range",
    "Location",
    "Diagnostic",
    # Responses
    "HoverInfo",
    "CompletionItem",
    "ParameterInformation",
    "SignatureInformation",
    "SignatureHelp",
    # Client
    "LSPClient",
]
