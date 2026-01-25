"""
Language Configurations - Tree-sitter Grammars and Settings.

Defines language-specific settings for AST parsing.
"""

import logging
from typing import Any, Dict, List, Set

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
        function_node_types={
            "function_declaration",
            "arrow_function",
            "method_definition",
        },
        class_node_types={"class_declaration", "class"},
        import_node_types={"import_statement"},
    ),
    "typescript": LanguageConfig(
        name="typescript",
        extensions=[".ts", ".tsx"],
        string_node_types={"string", "template_string", "string_fragment"},
        comment_node_types={"comment", "line_comment", "block_comment"},
        function_node_types={
            "function_declaration",
            "arrow_function",
            "method_definition",
        },
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
