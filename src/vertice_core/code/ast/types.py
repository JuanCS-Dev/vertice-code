"""
AST Editor Types - Enums and Data Classes.

Core types for context-aware code editing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeContext(str, Enum):
    """Context where a node appears in code."""

    CODE = "code"
    STRING = "string"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    IMPORT = "import"
    DECORATOR = "decorator"


@dataclass
class CodeLocation:
    """A location in source code."""

    line: int  # 1-indexed
    column: int  # 1-indexed
    end_line: int = 0
    end_column: int = 0

    def __post_init__(self):
        if self.end_line == 0:
            self.end_line = self.line
        if self.end_column == 0:
            self.end_column = self.column

    @property
    def is_single_line(self) -> bool:
        return self.line == self.end_line


@dataclass
class CodeMatch:
    """A match found in code."""

    text: str
    location: CodeLocation
    context: NodeContext
    node_type: str = ""
    parent_type: str = ""
    full_line: str = ""

    @property
    def is_code(self) -> bool:
        return self.context == NodeContext.CODE

    @property
    def is_in_string_or_comment(self) -> bool:
        return self.context in (NodeContext.STRING, NodeContext.COMMENT)


@dataclass
class CodeSymbol:
    """A symbol (function, class, variable) in code."""

    name: str
    symbol_type: str  # function, class, method, variable, etc.
    location: CodeLocation
    signature: str = ""
    docstring: str = ""
    parent: Optional[str] = None
    children: List["CodeSymbol"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.symbol_type,
            "line": self.location.line,
            "signature": self.signature,
            "parent": self.parent,
        }


@dataclass
class EditResult:
    """Result of an edit operation."""

    success: bool
    content: str = ""
    changes_made: int = 0
    error: Optional[str] = None
    locations_changed: List[CodeLocation] = field(default_factory=list)
