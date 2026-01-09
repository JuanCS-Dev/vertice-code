"""Individual validation check implementations."""

from __future__ import annotations
import logging
from typing import List, Optional
from .types import Check, CheckType, ValidationLevel
from ..lsp import DiagnosticSeverity, LSPConnectionError

logger = logging.getLogger(__name__)


async def check_syntax(
    content: str, language: Optional[str], ast_editor: Optional[object]
) -> Check:
    """Check syntax using AST parser."""
    if not language:
        return Check(CheckType.SYNTAX, True, "Unknown language, skipping syntax check")
    if not ast_editor:
        return Check(CheckType.SYNTAX, True, "AST editor not available")

    is_valid, error = ast_editor.is_valid_syntax(content, language)
    if is_valid:
        return Check(CheckType.SYNTAX, True, "Syntax OK")
    else:
        return Check(
            CheckType.SYNTAX, False, "Syntax error", details=[error or "Unknown syntax error"]
        )


async def check_lsp(
    filepath: str, content: str, level: ValidationLevel, lsp_client: Optional[object]
) -> Check:
    """Check using LSP diagnostics."""
    if not lsp_client:
        return Check(CheckType.LSP_ERRORS, True, "LSP not available")
    try:
        await lsp_client.notify_change(filepath, content)
        diagnostics = await lsp_client.diagnostics(filepath, wait_ms=500)
        if level == ValidationLevel.LSP_BASIC:
            diagnostics = [d for d in diagnostics if d.is_error]
        elif level == ValidationLevel.LSP_FULL:
            diagnostics = [d for d in diagnostics if d.severity <= DiagnosticSeverity.WARNING]
        if not diagnostics:
            return Check(CheckType.LSP_ERRORS, True, "No LSP errors")
        details = [
            f"Line {d.range.start.line + 1}: [{d.severity.name}] {d.message}" for d in diagnostics
        ]
        error_count = sum(1 for d in diagnostics if d.is_error)
        return Check(
            CheckType.LSP_ERRORS,
            error_count == 0,
            f"{len(diagnostics)} diagnostic(s) found",
            details=details,
            severity="error" if error_count > 0 else "warning",
        )
    except LSPConnectionError as e:
        return Check(CheckType.LSP_ERRORS, True, f"LSP unavailable: {e}")
    except Exception as e:
        logger.error(f"LSP check failed: {e}")
        return Check(CheckType.LSP_ERRORS, True, f"LSP check failed: {e}")


async def check_imports(content: str, module_exists_fn: callable) -> Check:
    """Check Python imports are valid."""
    import ast as python_ast

    try:
        tree = python_ast.parse(content)
    except SyntaxError:
        return Check(CheckType.IMPORTS, True, "Cannot parse, skipping import check")
    missing_imports: List[str] = []
    for node in python_ast.walk(tree):
        if isinstance(node, python_ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
                if not module_exists_fn(module_name):
                    missing_imports.append(module_name)
        elif isinstance(node, python_ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]
                if not module_exists_fn(module_name):
                    missing_imports.append(node.module)
    if missing_imports:
        return Check(
            CheckType.IMPORTS,
            False,
            f"{len(missing_imports)} missing import(s)",
            details=[f"Cannot find module: {m}" for m in missing_imports],
            severity="warning",
        )
    return Check(CheckType.IMPORTS, True, "All imports valid")
