"""Documentation Audit Tool."""

import ast
import logging
from pathlib import Path

from vertice_core.tools.base import Tool, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class AuditDocsTool(Tool):
    """Checks for docstring coverage and style."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.EXECUTION
        self.description = "Audit Python code for missing documentation."
        self.parameters = {
            "path": {"type": "string", "description": "File path", "required": True},
            "min_coverage": {
                "type": "integer",
                "description": "Minimum percentage coverage required",
                "default": 100,
            },
        }

    async def _execute_validated(self, path: str, min_coverage: int = 100) -> ToolResult:
        """Analyze docstring coverage."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")

            content = file_path.read_text()
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return ToolResult(success=False, error=f"Syntax error parsing file: {e}")

            missing = []
            total = 0

            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    # Skip private members (starting with _)
                    if (
                        hasattr(node, "name")
                        and node.name.startswith("_")
                        and node.name != "__init__"
                    ):
                        continue

                    # Skip __init__ if class has docstring? No, Google style requires both often.
                    # But let's skip __init__ if it's standard.

                    total += 1
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        name = getattr(node, "name", "module")
                        line = getattr(node, "lineno", 1)
                        missing.append(f"{name} (line {line})")
                    else:
                        # Basic Style Check (Google Style)
                        if (
                            "Args:" not in docstring
                            and "Returns:" not in docstring
                            and len(docstring.split("\n")) > 1
                        ):
                            # Weak check, just a warning maybe?
                            pass

            coverage = ((total - len(missing)) / total * 100) if total > 0 else 100
            success = coverage >= min_coverage

            result_data = {
                "coverage": round(coverage, 1),
                "missing": missing,
                "total_public_symbols": total,
            }

            error_msg = None
            if not success:
                error_msg = (
                    f"Documentation coverage {coverage:.1f}% is below threshold {min_coverage}%. "
                    f"Missing docs for: {', '.join(missing[:5])}"
                )
                if len(missing) > 5:
                    error_msg += f" and {len(missing)-5} more."

            return ToolResult(success=success, data=result_data, error=error_msg)

        except Exception as e:
            logger.error(f"AuditDocs failed: {e}")
            return ToolResult(success=False, error=str(e))
