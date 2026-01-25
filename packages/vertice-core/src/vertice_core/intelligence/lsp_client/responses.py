"""
LSP Client Responses - Response data structures for LSP operations.

HoverInfo, CompletionItem, SignatureHelp, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import Position, Range


@dataclass
class HoverInfo:
    """Hover information."""

    contents: str
    range: Optional[Range] = None

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "HoverInfo":
        """Parse from LSP hover response."""
        contents = data.get("contents", "")

        # Handle different content formats
        if isinstance(contents, dict):
            if "value" in contents:
                contents = contents["value"]
            elif "kind" in contents:
                contents = contents.get("value", "")
        elif isinstance(contents, list):
            contents = "\n".join(
                item["value"] if isinstance(item, dict) else str(item) for item in contents
            )

        range_data = data.get("range")
        range_obj = None
        if range_data:
            range_obj = Range(
                start=Position(
                    line=range_data["start"]["line"], character=range_data["start"]["character"]
                ),
                end=Position(
                    line=range_data["end"]["line"], character=range_data["end"]["character"]
                ),
            )

        return cls(contents=contents, range=range_obj)


@dataclass
class CompletionItem:
    """Code completion item."""

    label: str
    kind: int  # 1=Text, 2=Method, 3=Function, 4=Constructor, etc.
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    sort_text: Optional[str] = None

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "CompletionItem":
        """Parse from LSP completion item."""
        documentation = data.get("documentation")
        if isinstance(documentation, dict):
            documentation = documentation.get("value", "")

        return cls(
            label=data["label"],
            kind=data.get("kind", 1),
            detail=data.get("detail"),
            documentation=documentation,
            insert_text=data.get("insertText", data["label"]),
            sort_text=data.get("sortText"),
        )

    @property
    def kind_name(self) -> str:
        """Human-readable kind."""
        kinds = {
            1: "Text",
            2: "Method",
            3: "Function",
            4: "Constructor",
            5: "Field",
            6: "Variable",
            7: "Class",
            8: "Interface",
            9: "Module",
            10: "Property",
            11: "Unit",
            12: "Value",
            13: "Enum",
            14: "Keyword",
            15: "Snippet",
            16: "Color",
            17: "File",
            18: "Reference",
            19: "Folder",
            20: "EnumMember",
            21: "Constant",
            22: "Struct",
            23: "Event",
            24: "Operator",
            25: "TypeParameter",
        }
        return kinds.get(self.kind, "Unknown")


@dataclass
class ParameterInformation:
    """Function parameter information."""

    label: str
    documentation: Optional[str] = None

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "ParameterInformation":
        """Parse from LSP parameter."""
        label = data["label"]
        if isinstance(label, list):
            label = str(label)

        documentation = data.get("documentation")
        if isinstance(documentation, dict):
            documentation = documentation.get("value", "")

        return cls(label=label, documentation=documentation)


@dataclass
class SignatureInformation:
    """Function signature information."""

    label: str
    documentation: Optional[str] = None
    parameters: List[ParameterInformation] = field(default_factory=list)
    active_parameter: Optional[int] = None

    @classmethod
    def from_lsp(
        cls, data: Dict[str, Any], active_param: Optional[int] = None
    ) -> "SignatureInformation":
        """Parse from LSP signature."""
        documentation = data.get("documentation")
        if isinstance(documentation, dict):
            documentation = documentation.get("value", "")

        parameters = [ParameterInformation.from_lsp(p) for p in data.get("parameters", [])]

        return cls(
            label=data["label"],
            documentation=documentation,
            parameters=parameters,
            active_parameter=active_param,
        )


@dataclass
class SignatureHelp:
    """Signature help response."""

    signatures: List[SignatureInformation]
    active_signature: int = 0
    active_parameter: int = 0

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "SignatureHelp":
        """Parse from LSP signature help."""
        active_sig = data.get("activeSignature", 0)
        active_param = data.get("activeParameter", 0)

        signatures = [
            SignatureInformation.from_lsp(sig, active_param) for sig in data.get("signatures", [])
        ]

        return cls(
            signatures=signatures, active_signature=active_sig, active_parameter=active_param
        )


__all__ = [
    "HoverInfo",
    "CompletionItem",
    "ParameterInformation",
    "SignatureInformation",
    "SignatureHelp",
]
