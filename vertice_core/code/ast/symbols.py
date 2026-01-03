"""
Symbol Extraction - Extract Code Symbols from AST.

Extracts functions, classes, methods, and variables from source code.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Optional

from .types import CodeLocation, CodeSymbol
from .languages import LANGUAGE_CONFIGS, Node

if TYPE_CHECKING:
    from .editor import ASTEditor


def get_symbols(
    editor: "ASTEditor", content: str, language: str
) -> List[CodeSymbol]:
    """Extract all symbols (functions, classes, etc.) from code."""
    symbols: List[CodeSymbol] = []
    config = LANGUAGE_CONFIGS.get(language)

    if not config:
        return symbols

    tree = editor._parse(content, language)

    if not tree:
        return fallback_get_symbols(content, language)

    content_bytes = content.encode("utf-8")

    def extract_symbols(node: Node, parent_name: Optional[str] = None):
        node_type = node.type

        if node_type in config.function_node_types:
            symbol = extract_function_symbol(
                editor, node, content_bytes, language, parent_name
            )
            if symbol:
                symbols.append(symbol)

        elif node_type in config.class_node_types:
            symbol = extract_class_symbol(
                editor, node, content_bytes, language, parent_name
            )
            if symbol:
                symbols.append(symbol)
                for child in node.children:
                    extract_symbols(child, symbol.name)
                return

        for child in node.children:
            extract_symbols(child, parent_name)

    extract_symbols(tree.root_node)

    return symbols


def extract_function_symbol(
    editor: "ASTEditor",
    node: Node,
    content_bytes: bytes,
    language: str,
    parent_name: Optional[str],
) -> Optional[CodeSymbol]:
    """Extract function symbol from node."""
    name = None
    signature = ""

    for child in node.children:
        if child.type == "identifier" or child.type == "name":
            name = editor._get_text(child, content_bytes)
        elif child.type == "parameters":
            signature = editor._get_text(child, content_bytes)

    if not name:
        return None

    symbol_type = "method" if parent_name else "function"

    return CodeSymbol(
        name=name,
        symbol_type=symbol_type,
        location=editor._node_to_location(node),
        signature=f"{name}{signature}",
        parent=parent_name,
    )


def extract_class_symbol(
    editor: "ASTEditor",
    node: Node,
    content_bytes: bytes,
    language: str,
    parent_name: Optional[str],
) -> Optional[CodeSymbol]:
    """Extract class symbol from node."""
    name = None

    for child in node.children:
        if child.type == "identifier" or child.type == "name":
            name = editor._get_text(child, content_bytes)
            break

    if not name:
        return None

    return CodeSymbol(
        name=name,
        symbol_type="class",
        location=editor._node_to_location(node),
        signature=f"class {name}",
        parent=parent_name,
    )


def fallback_get_symbols(content: str, language: str) -> List[CodeSymbol]:
    """Fallback symbol extraction using regex."""
    symbols: List[CodeSymbol] = []
    lines = content.split("\n")

    if language == "python":
        func_pattern = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\)")
        class_pattern = re.compile(r"^\s*class\s+(\w+)")

        for line_num, line in enumerate(lines, 1):
            func_match = func_pattern.match(line)
            if func_match:
                symbols.append(
                    CodeSymbol(
                        name=func_match.group(1),
                        symbol_type="function",
                        location=CodeLocation(line_num, 1),
                        signature=f"{func_match.group(1)}({func_match.group(2)})",
                    )
                )

            class_match = class_pattern.match(line)
            if class_match:
                symbols.append(
                    CodeSymbol(
                        name=class_match.group(1),
                        symbol_type="class",
                        location=CodeLocation(line_num, 1),
                        signature=f"class {class_match.group(1)}",
                    )
                )

    return symbols


def find_symbol(
    editor: "ASTEditor",
    content: str,
    symbol_name: str,
    language: str,
    symbol_type: Optional[str] = None,
) -> Optional[CodeSymbol]:
    """Find a specific symbol by name."""
    symbols = get_symbols(editor, content, language)

    for symbol in symbols:
        if symbol.name == symbol_name:
            if symbol_type is None or symbol.symbol_type == symbol_type:
                return symbol

    return None
