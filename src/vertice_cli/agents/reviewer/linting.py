"""
Linting Module - External linting tool integration.

Provides integration with ruff, mypy, and other static analysis tools.
Converts tool output to CodeIssue objects for unified review pipeline.
"""

import json
import logging
from typing import Any, Callable, Coroutine, List

from .types import CodeIssue, IssueCategory, IssueSeverity

logger = logging.getLogger(__name__)


async def run_linting_tools(
    file_path: str,
    content: str,
    execute_tool: Callable[[str, dict], Coroutine[Any, Any, dict]],
) -> List[CodeIssue]:
    """Run linting tools (ruff, mypy) and convert results to CodeIssue objects.

    Args:
        file_path: Path to file to lint
        content: File content (unused, for future inline linting)
        execute_tool: Tool execution function from agent

    Returns:
        List of CodeIssue objects from linting results
    """
    issues: List[CodeIssue] = []

    # Run ruff
    issues.extend(await _run_ruff(file_path, execute_tool))

    # Run mypy
    issues.extend(await _run_mypy(file_path, execute_tool))

    return issues


async def _run_ruff(
    file_path: str,
    execute_tool: Callable[[str, dict], Coroutine[Any, Any, dict]],
) -> List[CodeIssue]:
    """Run ruff linter and parse results."""
    issues: List[CodeIssue] = []

    try:
        ruff_result = await execute_tool(
            "bash_command",
            {
                "command": f"cd /media/juan/DATA/Vertice-Code && python -m ruff check {file_path} --output-format json",
                "timeout": 30,
            },
        )

        if ruff_result.get("success"):
            try:
                ruff_output = json.loads(ruff_result.get("data", "[]"))
                for violation in ruff_output:
                    issues.append(
                        CodeIssue(
                            file=file_path,
                            line=violation.get("location", {}).get("row", 1),
                            severity=(
                                IssueSeverity.MEDIUM
                                if violation.get("code", "").startswith("E")
                                else IssueSeverity.LOW
                            ),
                            category=IssueCategory.MAINTAINABILITY,
                            message=f"Ruff: {violation.get('message', 'Unknown issue')}",
                            explanation=f"Rule: {violation.get('code', 'unknown')}",
                            fix_suggestion=violation.get("fix", {}).get(
                                "message", "Fix code style issue"
                            ),
                            confidence=0.9,
                        )
                    )
            except json.JSONDecodeError:
                pass

    except Exception as e:
        logger.debug(f"Ruff analysis failed for {file_path}: {e}")

    return issues


async def _run_mypy(
    file_path: str,
    execute_tool: Callable[[str, dict], Coroutine[Any, Any, dict]],
) -> List[CodeIssue]:
    """Run mypy type checker and parse results."""
    issues: List[CodeIssue] = []

    try:
        mypy_result = await execute_tool(
            "bash_command",
            {
                "command": f"cd /media/juan/DATA/Vertice-Code && python -m mypy {file_path} --ignore-missing-imports --no-error-summary",
                "timeout": 60,
            },
        )

        if not mypy_result.get("success") and mypy_result.get("error"):
            error_output = mypy_result.get("error", "")
            for line in error_output.split("\n"):
                if ":" in line and file_path in line:
                    try:
                        parts = line.split(":")
                        if len(parts) >= 3:
                            line_num = int(parts[1])
                            message = ":".join(parts[2:]).strip()
                            issues.append(
                                CodeIssue(
                                    file=file_path,
                                    line=line_num,
                                    severity=IssueSeverity.HIGH,
                                    category=IssueCategory.MAINTAINABILITY,
                                    message=f"MyPy: {message}",
                                    explanation="Type checking error detected by MyPy",
                                    fix_suggestion="Fix type annotations or type-related issues",
                                    confidence=0.95,
                                )
                            )
                    except (ValueError, IndexError):
                        continue

    except Exception as e:
        logger.debug(f"MyPy analysis failed for {file_path}: {e}")

    return issues


__all__ = ["run_linting_tools"]
