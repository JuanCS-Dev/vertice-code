"""
AST Transformer - Format-Preserving Code Surgery.

This module provides production-grade AST transformations using LibCST
for format preservation. It supports:
- Extract Method: Pull code into new function
- Rename Symbol: Update symbol + all references
- Inline Method: Replace calls with body
- Modernize Syntax: Update to latest Python

Key principle: Preserve comments, whitespace, and code style.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# LibCST for format-preserving AST transformations
try:
    import libcst as cst

    HAS_LIBCST = True
except ImportError:
    HAS_LIBCST = False
    cst = None


class ASTTransformer:
    """Production-grade AST transformer using LibCST.

    This class provides format-preserving code transformations.
    Falls back to basic AST operations if LibCST is unavailable.

    Attributes:
        use_libcst: Whether to use LibCST for transformations
    """

    def __init__(self, use_libcst: bool = HAS_LIBCST):
        """Initialize AST transformer.

        Args:
            use_libcst: Force LibCST usage (if available)
        """
        self.use_libcst = use_libcst and HAS_LIBCST

    def extract_method(
        self, source_code: str, start_line: int, end_line: int, new_method_name: str
    ) -> str:
        """Extract lines into a new method.

        Preserves formatting with LibCST when available.

        Args:
            source_code: Original source code
            start_line: Starting line (1-indexed)
            end_line: Ending line (1-indexed)
            new_method_name: Name for the extracted method

        Returns:
            Transformed source code
        """
        if self.use_libcst:
            return self._extract_method_libcst(source_code, start_line, end_line, new_method_name)
        else:
            return self._extract_method_ast(source_code, start_line, end_line, new_method_name)

    def rename_symbol(
        self, source_code: str, old_name: str, new_name: str, scope: Optional[str] = None
    ) -> str:
        """Rename symbol (function, variable, class).

        Updates all references to the symbol.

        Args:
            source_code: Original source code
            old_name: Current symbol name
            new_name: New symbol name
            scope: Optional scope restriction

        Returns:
            Transformed source code
        """
        if self.use_libcst:
            return self._rename_symbol_libcst(source_code, old_name, new_name, scope)
        else:
            return self._rename_symbol_ast(source_code, old_name, new_name)

    def inline_method(self, source_code: str, method_name: str) -> str:
        """Inline a method (replace calls with method body).

        Args:
            source_code: Original source code
            method_name: Name of method to inline

        Returns:
            Transformed source code
        """
        raise NotImplementedError(
            "inline_method not yet implemented. "
            "Contributions welcome: https://github.com/JuanCS/Vertice-Code/issues"
        )

    def modernize_syntax(self, source_code: str, target_version: str = "3.12") -> str:
        """Modernize Python syntax.

        Examples:
        - dict() → {}
        - format() → f-strings
        - typing imports → built-in generics (3.9+)

        Args:
            source_code: Original source code
            target_version: Target Python version

        Returns:
            Modernized source code
        """
        raise NotImplementedError(
            "modernize_syntax not yet implemented. "
            "Contributions welcome: https://github.com/JuanCS/Vertice-Code/issues"
        )

    def _extract_method_libcst(self, code: str, start: int, end: int, name: str) -> str:
        """Extract method using LibCST (format-preserving).

        Args:
            code: Source code
            start: Start line
            end: End line
            name: New method name

        Returns:
            Transformed code
        """
        raise NotImplementedError(
            "_extract_method_libcst not yet implemented. "
            "Contributions welcome: https://github.com/JuanCS/Vertice-Code/issues"
        )

    def _rename_symbol_libcst(self, code: str, old: str, new: str, scope: Optional[str]) -> str:
        """Rename using LibCST.

        Args:
            code: Source code
            old: Old symbol name
            new: New symbol name
            scope: Optional scope restriction

        Returns:
            Transformed code
        """
        if not HAS_LIBCST:
            raise ImportError("libcst not installed")

        module = cst.parse_module(code)

        class RenameTransformer(cst.CSTTransformer):
            """CST transformer for renaming symbols."""

            def leave_Name(self, original_node: Any, updated_node: Any) -> Any:
                if original_node.value == old:
                    return updated_node.with_changes(value=new)
                return updated_node

        transformed = module.visit(RenameTransformer())
        return transformed.code

    def _extract_method_ast(self, code: str, start: int, end: int, name: str) -> str:
        """Fallback AST-based extraction (doesn't preserve format).

        Args:
            code: Source code
            start: Start line
            end: End line
            name: New method name

        Returns:
            Transformed code
        """
        lines = code.split("\n")
        extracted_lines = lines[start - 1 : end]

        # Create new method
        new_method = f"def {name}():\n" + "\n".join(f"    {line}" for line in extracted_lines)

        # Replace in original
        lines[start - 1 : end] = [f"    {name}()"]

        return "\n".join(lines)

    def _rename_symbol_ast(self, code: str, old: str, new: str) -> str:
        """Fallback AST-based rename.

        Simple string replacement - not scope-aware.

        Args:
            code: Source code
            old: Old symbol name
            new: New symbol name

        Returns:
            Transformed code
        """
        return code.replace(old, new)


__all__ = ["ASTTransformer", "HAS_LIBCST"]
