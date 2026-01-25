"""
LSP Client Types - Core types for Language Server Protocol.

Enums, configs, and basic data structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Language(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    UNKNOWN = "unknown"

    @classmethod
    def detect(cls, file_path: Path) -> "Language":
        """Detect language from file extension."""
        suffix = file_path.suffix.lower()
        mapping = {
            ".py": cls.PYTHON,
            ".ts": cls.TYPESCRIPT,
            ".tsx": cls.TYPESCRIPT,
            ".js": cls.JAVASCRIPT,
            ".jsx": cls.JAVASCRIPT,
            ".go": cls.GO,
        }
        return mapping.get(suffix, cls.UNKNOWN)


@dataclass
class LSPServerConfig:
    """Configuration for an LSP server."""

    language: Language
    command: List[str]
    initialization_options: Optional[Dict[str, Any]] = None

    @classmethod
    def get_configs(cls) -> Dict[Language, "LSPServerConfig"]:
        """Get all LSP server configurations."""
        return {
            Language.PYTHON: cls(
                language=Language.PYTHON, command=["pylsp"], initialization_options={}
            ),
            Language.TYPESCRIPT: cls(
                language=Language.TYPESCRIPT,
                command=["typescript-language-server", "--stdio"],
                initialization_options={"preferences": {"includeCompletionsWithSnippetText": True}},
            ),
            Language.JAVASCRIPT: cls(
                language=Language.JAVASCRIPT,
                command=["typescript-language-server", "--stdio"],
                initialization_options={"preferences": {"includeCompletionsWithSnippetText": True}},
            ),
            Language.GO: cls(language=Language.GO, command=["gopls"], initialization_options={}),
        }


class LSPFeature(Enum):
    """Supported LSP features."""

    HOVER = "textDocument/hover"
    DEFINITION = "textDocument/definition"
    REFERENCES = "textDocument/references"
    COMPLETION = "textDocument/completion"
    DIAGNOSTICS = "textDocument/publishDiagnostics"


@dataclass
class Position:
    """Position in a text document (0-indexed)."""

    line: int
    character: int

    def to_lsp(self) -> Dict[str, int]:
        """Convert to LSP position format."""
        return {"line": self.line, "character": self.character}


@dataclass
class Range:
    """Range in a text document."""

    start: Position
    end: Position

    def to_lsp(self) -> Dict[str, Any]:
        """Convert to LSP range format."""
        return {"start": self.start.to_lsp(), "end": self.end.to_lsp()}


@dataclass
class Location:
    """Location (file + range)."""

    uri: str
    range: Range

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "Location":
        """Parse from LSP location."""
        return cls(
            uri=data["uri"],
            range=Range(
                start=Position(
                    line=data["range"]["start"]["line"],
                    character=data["range"]["start"]["character"],
                ),
                end=Position(
                    line=data["range"]["end"]["line"], character=data["range"]["end"]["character"]
                ),
            ),
        )


@dataclass
class Diagnostic:
    """LSP diagnostic (error/warning)."""

    range: Range
    severity: int  # 1=Error, 2=Warning, 3=Info, 4=Hint
    message: str
    source: Optional[str] = None

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "Diagnostic":
        """Parse from LSP diagnostic."""
        return cls(
            range=Range(
                start=Position(
                    line=data["range"]["start"]["line"],
                    character=data["range"]["start"]["character"],
                ),
                end=Position(
                    line=data["range"]["end"]["line"], character=data["range"]["end"]["character"]
                ),
            ),
            severity=data.get("severity", 1),
            message=data["message"],
            source=data.get("source"),
        )

    @property
    def severity_name(self) -> str:
        """Human-readable severity."""
        return {1: "Error", 2: "Warning", 3: "Info", 4: "Hint"}.get(self.severity, "Unknown")


__all__ = [
    "Language",
    "LSPServerConfig",
    "LSPFeature",
    "Position",
    "Range",
    "Location",
    "Diagnostic",
]
