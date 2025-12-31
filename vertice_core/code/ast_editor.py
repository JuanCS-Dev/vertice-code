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
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

logger = logging.getLogger(__name__)

# Try to import tree-sitter
try:
    import tree_sitter
    from tree_sitter import Language, Node, Parser, Tree

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None
    Language = None
    Node = None
    Parser = None
    Tree = None
    logger.warning("tree-sitter not available, using fallback parsing")


# Try to import language grammars
LANGUAGE_GRAMMARS: Dict[str, Any] = {}

try:
    import tree_sitter_python
    LANGUAGE_GRAMMARS["python"] = tree_sitter_python.language()
except ImportError:
    pass

try:
    import tree_sitter_javascript
    LANGUAGE_GRAMMARS["javascript"] = tree_sitter_javascript.language()
except ImportError:
    pass

try:
    import tree_sitter_typescript
    LANGUAGE_GRAMMARS["typescript"] = tree_sitter_typescript.language_typescript()
    LANGUAGE_GRAMMARS["tsx"] = tree_sitter_typescript.language_tsx()
except ImportError:
    pass

try:
    import tree_sitter_go
    LANGUAGE_GRAMMARS["go"] = tree_sitter_go.language()
except ImportError:
    pass

try:
    import tree_sitter_rust
    LANGUAGE_GRAMMARS["rust"] = tree_sitter_rust.language()
except ImportError:
    pass


class NodeContext(str, Enum):
    """Context where a node appears in code."""

    CODE = "code"  # Regular code
    STRING = "string"  # Inside string literal
    COMMENT = "comment"  # Inside comment
    DOCSTRING = "docstring"  # Docstring
    IMPORT = "import"  # Import statement
    DECORATOR = "decorator"  # Decorator


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


class LanguageConfig:
    """Configuration for a programming language."""

    def __init__(
        self,
        name: str,
        extensions: List[str],
        string_node_types: Set[str],
        comment_node_types: Set[str],
        function_node_types: Set[str],
        class_node_types: Set[str],
        import_node_types: Set[str],
    ):
        self.name = name
        self.extensions = extensions
        self.string_node_types = string_node_types
        self.comment_node_types = comment_node_types
        self.function_node_types = function_node_types
        self.class_node_types = class_node_types
        self.import_node_types = import_node_types


# Language configurations
LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        name="python",
        extensions=[".py", ".pyi"],
        string_node_types={"string", "string_content", "interpolation"},
        comment_node_types={"comment"},
        function_node_types={"function_definition", "async_function_definition"},
        class_node_types={"class_definition"},
        import_node_types={"import_statement", "import_from_statement"},
    ),
    "javascript": LanguageConfig(
        name="javascript",
        extensions=[".js", ".jsx", ".mjs"],
        string_node_types={"string", "template_string", "string_fragment"},
        comment_node_types={"comment", "line_comment", "block_comment"},
        function_node_types={"function_declaration", "arrow_function", "method_definition"},
        class_node_types={"class_declaration", "class"},
        import_node_types={"import_statement"},
    ),
    "typescript": LanguageConfig(
        name="typescript",
        extensions=[".ts", ".tsx"],
        string_node_types={"string", "template_string", "string_fragment"},
        comment_node_types={"comment", "line_comment", "block_comment"},
        function_node_types={"function_declaration", "arrow_function", "method_definition"},
        class_node_types={"class_declaration", "class"},
        import_node_types={"import_statement"},
    ),
    "go": LanguageConfig(
        name="go",
        extensions=[".go"],
        string_node_types={"interpreted_string_literal", "raw_string_literal"},
        comment_node_types={"comment"},
        function_node_types={"function_declaration", "method_declaration"},
        class_node_types={"type_declaration"},
        import_node_types={"import_declaration"},
    ),
    "rust": LanguageConfig(
        name="rust",
        extensions=[".rs"],
        string_node_types={"string_literal", "raw_string_literal"},
        comment_node_types={"line_comment", "block_comment"},
        function_node_types={"function_item"},
        class_node_types={"struct_item", "enum_item", "impl_item"},
        import_node_types={"use_declaration"},
    ),
}


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
        self._trees: Dict[str, Tree] = {}  # Cache parsed trees

        # Initialize parsers for available languages
        if TREE_SITTER_AVAILABLE:
            for lang, grammar in LANGUAGE_GRAMMARS.items():
                parser = Parser()
                parser.language = Language(grammar)
                self._parsers[lang] = parser

    def _get_language(self, filepath_or_lang: str) -> Optional[str]:
        """Detect language from filepath or direct language name."""
        # Direct language name
        if filepath_or_lang in LANGUAGE_CONFIGS:
            return filepath_or_lang

        # From extension
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

    def _get_node_context(self, node: Node, language: str) -> NodeContext:
        """Determine the context of a node."""
        config = LANGUAGE_CONFIGS.get(language)
        if not config:
            return NodeContext.CODE

        # Check node type
        node_type = node.type

        if node_type in config.string_node_types:
            return NodeContext.STRING

        if node_type in config.comment_node_types:
            return NodeContext.COMMENT

        if node_type in config.import_node_types:
            return NodeContext.IMPORT

        # Check if inside string or comment (walk up parents)
        current = node.parent
        while current:
            if current.type in config.string_node_types:
                # Check for docstring (first string in function/class)
                parent = current.parent
                if parent and parent.type in (
                    config.function_node_types | config.class_node_types
                ):
                    # Check if it's the first statement
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

    def _walk_tree(self, node: Node) -> Iterator[Node]:
        """Walk all nodes in the tree."""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)

    def _get_text(self, node: Node, content: bytes) -> str:
        """Get text of a node."""
        return content[node.start_byte:node.end_byte].decode("utf-8")

    def _node_to_location(self, node: Node) -> CodeLocation:
        """Convert node to CodeLocation."""
        return CodeLocation(
            line=node.start_point[0] + 1,
            column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )

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
        """
        Find text occurrences only in actual code.

        Args:
            content: Source code content
            search: Text to search for
            language: Programming language
            include_strings: Include matches in strings
            include_comments: Include matches in comments
            case_sensitive: Case-sensitive search

        Returns:
            List of matches with context information
        """
        matches: List[CodeMatch] = []
        lines = content.split("\n")

        # Try tree-sitter first
        tree = self._parse(content, language)

        if tree:
            content_bytes = content.encode("utf-8")

            for node in self._walk_tree(tree.root_node):
                node_text = self._get_text(node, content_bytes)

                # Check if search term is in this node
                if case_sensitive:
                    if search not in node_text:
                        continue
                else:
                    if search.lower() not in node_text.lower():
                        continue

                # Determine context
                context = self._get_node_context(node, language)

                # Filter based on context
                if context == NodeContext.STRING and not include_strings:
                    continue
                if context == NodeContext.COMMENT and not include_comments:
                    continue

                # Only leaf nodes or nodes that contain the exact search
                if node.child_count == 0 or node_text == search:
                    location = self._node_to_location(node)
                    line_text = lines[location.line - 1] if location.line <= len(lines) else ""

                    matches.append(CodeMatch(
                        text=node_text,
                        location=location,
                        context=context,
                        node_type=node.type,
                        parent_type=node.parent.type if node.parent else "",
                        full_line=line_text,
                    ))

        else:
            # Fallback: regex-based search with heuristic context detection
            matches = self._fallback_find(
                content, search, language, include_strings, include_comments, case_sensitive
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

                # Heuristic context detection
                context = self._detect_context_heuristic(line, col, language)

                if context == NodeContext.STRING and not include_strings:
                    continue
                if context == NodeContext.COMMENT and not include_comments:
                    continue

                matches.append(CodeMatch(
                    text=match.group(),
                    location=CodeLocation(line_num, col, line_num, col + len(search)),
                    context=context,
                    node_type="unknown",
                    parent_type="",
                    full_line=line,
                ))

        return matches

    def _detect_context_heuristic(
        self,
        line: str,
        column: int,
        language: str,
    ) -> NodeContext:
        """Detect context using heuristics (fallback)."""
        prefix = line[:column - 1]

        # Check for comment
        config = LANGUAGE_CONFIGS.get(language)
        if config and config.name == "python":
            if "#" in prefix:
                return NodeContext.COMMENT
        elif config and config.name in ("javascript", "typescript", "go", "rust"):
            if "//" in prefix:
                return NodeContext.COMMENT

        # Check for string (simple heuristic)
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
        """
        Replace text only in actual code (not strings/comments).

        Args:
            content: Source code content
            old_text: Text to replace
            new_text: Replacement text
            language: Programming language
            include_strings: Replace in strings too
            include_comments: Replace in comments too
            max_replacements: Maximum replacements (0 = unlimited)

        Returns:
            EditResult with new content
        """
        if old_text == new_text:
            return EditResult(success=True, content=content, changes_made=0)

        # Find all matches
        matches = self.find_in_code(
            content, old_text, language, include_strings, include_comments
        )

        if not matches:
            return EditResult(
                success=True,
                content=content,
                changes_made=0,
            )

        # Sort by position (reverse order for safe replacement)
        matches.sort(
            key=lambda m: (m.location.line, m.location.column),
            reverse=True,
        )

        # Limit replacements if specified
        if max_replacements > 0:
            matches = matches[:max_replacements]

        # Apply replacements
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

    def get_symbols(
        self,
        content: str,
        language: str,
    ) -> List[CodeSymbol]:
        """
        Extract all symbols (functions, classes, etc.) from code.

        Args:
            content: Source code content
            language: Programming language

        Returns:
            List of code symbols
        """
        symbols: List[CodeSymbol] = []
        config = LANGUAGE_CONFIGS.get(language)

        if not config:
            return symbols

        tree = self._parse(content, language)

        if not tree:
            # Fallback: regex-based extraction
            return self._fallback_get_symbols(content, language)

        content_bytes = content.encode("utf-8")

        def extract_symbols(node: Node, parent_name: Optional[str] = None):
            node_type = node.type

            if node_type in config.function_node_types:
                symbol = self._extract_function_symbol(
                    node, content_bytes, language, parent_name
                )
                if symbol:
                    symbols.append(symbol)

            elif node_type in config.class_node_types:
                symbol = self._extract_class_symbol(
                    node, content_bytes, language, parent_name
                )
                if symbol:
                    symbols.append(symbol)
                    # Extract methods inside class
                    for child in node.children:
                        extract_symbols(child, symbol.name)
                    return  # Don't recurse further for class

            for child in node.children:
                extract_symbols(child, parent_name)

        extract_symbols(tree.root_node)

        return symbols

    def _extract_function_symbol(
        self,
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
                name = self._get_text(child, content_bytes)
            elif child.type == "parameters":
                signature = self._get_text(child, content_bytes)

        if not name:
            return None

        symbol_type = "method" if parent_name else "function"

        return CodeSymbol(
            name=name,
            symbol_type=symbol_type,
            location=self._node_to_location(node),
            signature=f"{name}{signature}",
            parent=parent_name,
        )

    def _extract_class_symbol(
        self,
        node: Node,
        content_bytes: bytes,
        language: str,
        parent_name: Optional[str],
    ) -> Optional[CodeSymbol]:
        """Extract class symbol from node."""
        name = None

        for child in node.children:
            if child.type == "identifier" or child.type == "name":
                name = self._get_text(child, content_bytes)
                break

        if not name:
            return None

        return CodeSymbol(
            name=name,
            symbol_type="class",
            location=self._node_to_location(node),
            signature=f"class {name}",
            parent=parent_name,
        )

    def _fallback_get_symbols(
        self,
        content: str,
        language: str,
    ) -> List[CodeSymbol]:
        """Fallback symbol extraction using regex."""
        symbols: List[CodeSymbol] = []
        lines = content.split("\n")

        # Python patterns
        if language == "python":
            func_pattern = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\)")
            class_pattern = re.compile(r"^\s*class\s+(\w+)")

            for line_num, line in enumerate(lines, 1):
                func_match = func_pattern.match(line)
                if func_match:
                    symbols.append(CodeSymbol(
                        name=func_match.group(1),
                        symbol_type="function",
                        location=CodeLocation(line_num, 1),
                        signature=f"{func_match.group(1)}({func_match.group(2)})",
                    ))

                class_match = class_pattern.match(line)
                if class_match:
                    symbols.append(CodeSymbol(
                        name=class_match.group(1),
                        symbol_type="class",
                        location=CodeLocation(line_num, 1),
                        signature=f"class {class_match.group(1)}",
                    ))

        return symbols

    def find_symbol(
        self,
        content: str,
        symbol_name: str,
        language: str,
        symbol_type: Optional[str] = None,
    ) -> Optional[CodeSymbol]:
        """
        Find a specific symbol by name.

        Args:
            content: Source code content
            symbol_name: Name of symbol to find
            language: Programming language
            symbol_type: Optional type filter (function, class, method)

        Returns:
            CodeSymbol if found, None otherwise
        """
        symbols = self.get_symbols(content, language)

        for symbol in symbols:
            if symbol.name == symbol_name:
                if symbol_type is None or symbol.symbol_type == symbol_type:
                    return symbol

        return None

    # =========================================================================
    # Public API - Validation
    # =========================================================================

    def is_valid_syntax(self, content: str, language: str) -> Tuple[bool, Optional[str]]:
        """
        Check if content has valid syntax.

        Args:
            content: Source code content
            language: Programming language

        Returns:
            Tuple of (is_valid, error_message)
        """
        tree = self._parse(content, language)

        if tree is None:
            # No parser available, try Python's compile for Python
            if language == "python":
                try:
                    compile(content, "<string>", "exec")
                    return True, None
                except SyntaxError as e:
                    return False, f"Line {e.lineno}: {e.msg}"
            return True, None  # Can't validate, assume valid

        # Check for ERROR nodes
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
        self,
        content: str,
        line: int,
        column: int,
        language: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get AST node information at position.

        Args:
            content: Source code content
            line: 1-indexed line number
            column: 1-indexed column number
            language: Programming language

        Returns:
            Node information dict or None
        """
        tree = self._parse(content, language)
        if not tree:
            return None

        content_bytes = content.encode("utf-8")

        # Find node at position
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


# Singleton instance
_ast_editor: Optional[ASTEditor] = None


def get_ast_editor() -> ASTEditor:
    """Get singleton AST editor instance."""
    global _ast_editor
    if _ast_editor is None:
        _ast_editor = ASTEditor()
    return _ast_editor


__all__ = [
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
]
