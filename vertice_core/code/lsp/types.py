"""
LSP Types - Language Server Protocol data structures.

Contains:
- DiagnosticSeverity: Severity levels enum
- SymbolKind: Symbol kinds enum
- Position: LSP position (0-indexed)
- Range: LSP range
- Location: LSP location with URI
- Diagnostic: LSP diagnostic
- DocumentSymbol: Document symbol with hierarchy
- HoverInfo: Hover information
- CompletionItem: Completion suggestion
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DiagnosticSeverity(int, Enum):
    """LSP Diagnostic severity levels."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class SymbolKind(int, Enum):
    """LSP Symbol kinds."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


@dataclass
class Position:
    """LSP Position (0-indexed)."""
    line: int
    character: int

    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Position":
        return cls(line=data["line"], character=data["character"])


@dataclass
class Range:
    """LSP Range."""
    start: Position
    end: Position

    def to_dict(self) -> Dict[str, Any]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Range":
        return cls(
            start=Position.from_dict(data["start"]),
            end=Position.from_dict(data["end"]),
        )


@dataclass
class Location:
    """LSP Location."""
    uri: str
    range: Range

    @property
    def filepath(self) -> str:
        """Convert URI to filepath."""
        if self.uri.startswith("file://"):
            return self.uri[7:]
        return self.uri

    @property
    def line(self) -> int:
        """1-indexed line number."""
        return self.range.start.line + 1

    @property
    def column(self) -> int:
        """1-indexed column number."""
        return self.range.start.character + 1

    def to_dict(self) -> Dict[str, Any]:
        return {"uri": self.uri, "range": self.range.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(uri=data["uri"], range=Range.from_dict(data["range"]))


@dataclass
class Diagnostic:
    """LSP Diagnostic."""
    range: Range
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None
    source: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return self.severity == DiagnosticSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == DiagnosticSeverity.WARNING

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagnostic":
        return cls(
            range=Range.from_dict(data["range"]),
            message=data.get("message", ""),
            severity=DiagnosticSeverity(data.get("severity", 1)),
            code=str(data.get("code")) if data.get("code") else None,
            source=data.get("source"),
        )


@dataclass
class DocumentSymbol:
    """LSP Document Symbol."""
    name: str
    kind: SymbolKind
    range: Range
    selection_range: Range
    detail: Optional[str] = None
    children: List["DocumentSymbol"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSymbol":
        children = [cls.from_dict(c) for c in data.get("children", [])]
        return cls(
            name=data["name"],
            kind=SymbolKind(data.get("kind", 1)),
            range=Range.from_dict(data["range"]),
            selection_range=Range.from_dict(
                data.get("selectionRange", data["range"])
            ),
            detail=data.get("detail"),
            children=children,
        )


@dataclass
class HoverInfo:
    """LSP Hover information."""
    contents: str
    range: Optional[Range] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoverInfo":
        contents = data.get("contents", "")
        if isinstance(contents, dict):
            contents = contents.get("value", str(contents))
        elif isinstance(contents, list):
            contents = "\n".join(
                c.get("value", str(c)) if isinstance(c, dict) else str(c)
                for c in contents
            )

        range_data = data.get("range")
        return cls(
            contents=contents,
            range=Range.from_dict(range_data) if range_data else None,
        )


@dataclass
class CompletionItem:
    """LSP Completion item."""
    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletionItem":
        doc = data.get("documentation", "")
        if isinstance(doc, dict):
            doc = doc.get("value", "")

        return cls(
            label=data["label"],
            kind=data.get("kind"),
            detail=data.get("detail"),
            documentation=doc,
            insert_text=data.get("insertText"),
        )
