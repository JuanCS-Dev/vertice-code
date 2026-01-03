"""
AST Editor - Context-Aware Code Editing with Tree-sitter.

Implements intelligent code editing that understands code structure:
- Avoids matching strings and comments
- Finds symbols by their AST node type
- Provides semantic search within code
- Supports incremental parsing for fast updates

References:
- Tree-sitter 0.25+ Python bindings
- Cursor AI AST-aware editing patterns
- Zed Editor syntax-aware editing

Phase 10: Sprint 3 - Code Intelligence

Soli Deo Gloria
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .types import (
    CodeLocation,
    CodeMatch,
    CodeSymbol,
    EditResult,
    NodeContext,
)
from .languages import (
    LANGUAGE_CONFIGS,
    LANGUAGE_GRAMMARS,
    TREE_SITTER_AVAILABLE,
    Language,
    Node,
    Parser,
    Tree,
)

logger = logging.getLogger(__name__)


class ASTEditor:
    """
    Context-aware code editor using Tree-sitter.

    Provides intelligent editing that understands code structure:
    - find_in_code: Find text only in actual code (not strings/comments)
    - replace_in_code: Replace only in actual code
    - find_symbol: Find function/class/variable definitions
    - get_symbols: Extract all symbols from file

    Usage:
        editor = ASTEditor()
        matches = editor.find_in_code(content, "my_function", "python")
        result = editor.replace_in_code(content, "old_name", "new_name", "python")
    """

    def __init__(self):
        """Initialize AST editor."""
        self._parsers: Dict[str, Parser] = {}
        self._trees: Dict[str, Tree] = {}

        if TREE_SITTER_AVAILABLE:
            for lang, grammar in LANGUAGE_GRAMMARS.items():
                parser = Parser()
                parser.language = Language(grammar)
                self._parsers[lang] = parser

    # =========================================================================
    # Internal Parsing Methods
    # =========================================================================

    def _get_language(self, filepath_or_lang: str) -> Optional[str]:
        """Detect language from filepath or direct language name."""
        if filepath_or_lang in LANGUAGE_CONFIGS:
            return filepath_or_lang

        ext = Path(filepath_or_lang).suffix.lower()
        for lang, config in LANGUAGE_CONFIGS.items():
            if ext in config.extensions:
                return lang

        return None

    def _parse(self, content: str, language: str) -> Optional[Tree]:
        """Parse content into AST."""
        if not TREE_SITTER_AVAILABLE:
            return None

        parser = self._parsers.get(language)
        if not parser:
            return None

        return parser.parse(content.encode("utf-8"))

    def _walk_tree(self, node: Node) -> Iterator[Node]:
        """Walk all nodes in the tree."""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)

    def _get_text(self, node: Node, content: bytes) -> str:
        """Get text of a node."""
        return content[node.start_byte : node.end_byte].decode("utf-8")

    def _node_to_location(self, node: Node) -> CodeLocation:
        """Convert node to CodeLocation."""
        return CodeLocation(
            line=node.start_point[0] + 1,
            column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )

    def _get_node_context(self, node: Node, language: str) -> NodeContext:
        """Determine the context of a node."""
        config = LANGUAGE_CONFIGS.get(language)
        if not config:
            return NodeContext.CODE

        node_type = node.type

        if node_type in config.string_node_types:
            return NodeContext.STRING

        if node_type in config.comment_node_types:
            return NodeContext.COMMENT

        if node_type in config.import_node_types:
            return NodeContext.IMPORT

        current = node.parent
        while current:
            if current.type in config.string_node_types:
                parent = current.parent
                if parent and parent.type in (
                    config.function_node_types | config.class_node_types
                ):
                    for child in parent.children:
                        if child.type == "expression_statement":
                            expr = child.children[0] if child.children else None
                            if expr and expr.type in config.string_node_types:
                                if expr.id == current.id:
                                    return NodeContext.DOCSTRING
                            break
                        elif child.type not in (":", "def", "class", "async"):
                            break
                return NodeContext.STRING

            if current.type in config.comment_node_types:
                return NodeContext.COMMENT

            current = current.parent

        return NodeContext.CODE

    # =========================================================================
    # Public API - Finding
    # =========================================================================

    def find_in_code(
        self,
        content: str,
        search: str,
        language: str,
        include_strings: bool = False,
        include_comments: bool = False,
        case_sensitive: bool = True,
    ) -> List[CodeMatch]:
        """Find text occurrences only in actual code."""
        matches: List[CodeMatch] = []
        lines = content.split("\n")

        tree = self._parse(content, language)

        if tree:
            content_bytes = content.encode("utf-8")

            for node in self._walk_tree(tree.root_node):
                node_text = self._get_text(node, content_bytes)

                if case_sensitive:
                    if search not in node_text:
                        continue
                else:
                    if search.lower() not in node_text.lower():
                        continue

                context = self._get_node_context(node, language)

                if context == NodeContext.STRING and not include_strings:
                    continue
                if context == NodeContext.COMMENT and not include_comments:
                    continue

                if node.child_count == 0 or node_text == search:
                    location = self._node_to_location(node)
                    line_text = (
                        lines[location.line - 1] if location.line <= len(lines) else ""
                    )

                    matches.append(
                        CodeMatch(
                            text=node_text,
                            location=location,
                            context=context,
                            node_type=node.type,
                            parent_type=node.parent.type if node.parent else "",
                            full_line=line_text,
                        )
                    )

        else:
            matches = self._fallback_find(
                content,
                search,
                language,
                include_strings,
                include_comments,
                case_sensitive,
            )

        return matches

    def _fallback_find(
        self,
        content: str,
        search: str,
        language: str,
        include_strings: bool,
        include_comments: bool,
        case_sensitive: bool,
    ) -> List[CodeMatch]:
        """Fallback search without tree-sitter."""
        matches: List[CodeMatch] = []
        lines = content.split("\n")

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(search)

        for line_num, line in enumerate(lines, 1):
            for match in re.finditer(pattern, line, flags):
                col = match.start() + 1
                context = self._detect_context_heuristic(line, col, language)

                if context == NodeContext.STRING and not include_strings:
                    continue
                if context == NodeContext.COMMENT and not include_comments:
                    continue

                matches.append(
                    CodeMatch(
                        text=match.group(),
                        location=CodeLocation(line_num, col, line_num, col + len(search)),
                        context=context,
                        node_type="unknown",
                        parent_type="",
                        full_line=line,
                    )
                )

        return matches

    def _detect_context_heuristic(
        self, line: str, column: int, language: str
    ) -> NodeContext:
        """Detect context using heuristics (fallback)."""
        prefix = line[: column - 1]

        config = LANGUAGE_CONFIGS.get(language)
        if config and config.name == "python":
            if "#" in prefix:
                return NodeContext.COMMENT
        elif config and config.name in ("javascript", "typescript", "go", "rust"):
            if "//" in prefix:
                return NodeContext.COMMENT

        quote_count = prefix.count('"') + prefix.count("'")
        if quote_count % 2 == 1:
            return NodeContext.STRING

        return NodeContext.CODE

    # =========================================================================
    # Public API - Replacing
    # =========================================================================

    def replace_in_code(
        self,
        content: str,
        old_text: str,
        new_text: str,
        language: str,
        include_strings: bool = False,
        include_comments: bool = False,
        max_replacements: int = 0,
    ) -> EditResult:
        """Replace text only in actual code (not strings/comments)."""
        if old_text == new_text:
            return EditResult(success=True, content=content, changes_made=0)

        matches = self.find_in_code(
            content, old_text, language, include_strings, include_comments
        )

        if not matches:
            return EditResult(success=True, content=content, changes_made=0)

        matches.sort(
            key=lambda m: (m.location.line, m.location.column),
            reverse=True,
        )

        if max_replacements > 0:
            matches = matches[:max_replacements]

        lines = content.split("\n")
        locations_changed: List[CodeLocation] = []

        for match in matches:
            line_idx = match.location.line - 1
            col_start = match.location.column - 1
            col_end = col_start + len(old_text)

            if 0 <= line_idx < len(lines):
                line = lines[line_idx]
                lines[line_idx] = line[:col_start] + new_text + line[col_end:]
                locations_changed.append(match.location)

        new_content = "\n".join(lines)

        return EditResult(
            success=True,
            content=new_content,
            changes_made=len(locations_changed),
            locations_changed=locations_changed,
        )

    # =========================================================================
    # Public API - Symbol Extraction
    # =========================================================================

    def get_symbols(self, content: str, language: str) -> List[CodeSymbol]:
        """Extract all symbols (functions, classes, etc.) from code."""
        from . import symbols as sym

        return sym.get_symbols(self, content, language)

    def find_symbol(
        self,
        content: str,
        symbol_name: str,
        language: str,
        symbol_type: Optional[str] = None,
    ) -> Optional[CodeSymbol]:
        """Find a specific symbol by name."""
        from . import symbols as sym

        return sym.find_symbol(self, content, symbol_name, language, symbol_type)

    # =========================================================================
    # Public API - Validation
    # =========================================================================

    def is_valid_syntax(
        self, content: str, language: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if content has valid syntax."""
        tree = self._parse(content, language)

        if tree is None:
            if language == "python":
                try:
                    compile(content, "<string>", "exec")
                    return True, None
                except SyntaxError as e:
                    return False, f"Line {e.lineno}: {e.msg}"
            return True, None

        def has_error(node: Node) -> Optional[str]:
            if node.type == "ERROR" or node.is_missing:
                line = node.start_point[0] + 1
                return f"Syntax error at line {line}"

            for child in node.children:
                error = has_error(child)
                if error:
                    return error

            return None

        error = has_error(tree.root_node)
        return error is None, error

    def get_node_at_position(
        self, content: str, line: int, column: int, language: str
    ) -> Optional[Dict[str, Any]]:
        """Get AST node information at position."""
        tree = self._parse(content, language)
        if not tree:
            return None

        content_bytes = content.encode("utf-8")

        point = (line - 1, column - 1)
        node = tree.root_node.descendant_for_point_range(point, point)

        if not node:
            return None

        context = self._get_node_context(node, language)

        return {
            "type": node.type,
            "text": self._get_text(node, content_bytes),
            "context": context.value,
            "location": self._node_to_location(node),
            "parent_type": node.parent.type if node.parent else None,
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def is_language_supported(self, language: str) -> bool:
        """Check if language has tree-sitter support."""
        return language in self._parsers

    def get_supported_languages(self) -> List[str]:
        """Get list of languages with tree-sitter support."""
        return list(self._parsers.keys())

    def get_available_languages(self) -> List[str]:
        """Get all configured languages (including fallback support)."""
        return list(LANGUAGE_CONFIGS.keys())
