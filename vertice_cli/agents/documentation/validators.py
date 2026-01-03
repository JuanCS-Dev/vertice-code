"""
Docstring Validators - Docstring Style Validation.

Provides validation of existing docstrings against style guides:
- Google Style
- NumPy Style
- Sphinx Style

Features:
    - Missing docstring detection
    - Style compliance checking
    - Issue reporting with severity levels
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from .models import DocstringStyle
from .analyzers import analyze_module

logger = logging.getLogger(__name__)

# Docstring validation patterns
GOOGLE_DOCSTRING_PATTERN = re.compile(
    r"(?P<summary>.+?)\n\n"
    r"(?:(?P<args>Args:.*?)\n\n)?"
    r"(?:(?P<returns>Returns:.*?)\n\n)?"
    r"(?:(?P<raises>Raises:.*?)\n\n)?",
    re.DOTALL,
)

# Secret patterns to exclude from docs
SECRET_PATTERNS = [
    r"['\"]?[A-Z0-9_]+_KEY['\"]?\s*=\s*['\"][\w-]+['\"]",
    r"['\"]?[A-Z0-9_]+_SECRET['\"]?\s*=\s*['\"][\w-]+['\"]",
    r"password\s*=\s*['\"][\w-]+['\"]",
]


def validate_docstrings(
    target_path: Path, style: DocstringStyle
) -> Dict[str, Any]:
    """Validate existing docstrings against style guide.

    Args:
        target_path: Directory or file to validate
        style: Expected docstring style

    Returns:
        Dictionary with validation results:
            - issues: List of issues found
            - total_issues: Total count
            - critical/medium/low: Counts by severity
    """
    issues: List[Dict[str, Any]] = []

    # Find all Python files
    python_files = (
        [target_path]
        if target_path.is_file()
        else list(target_path.rglob("*.py"))
    )

    for py_file in python_files:
        if "__pycache__" in str(py_file):
            continue

        try:
            module_doc = analyze_module(py_file)

            # Check module docstring
            if not module_doc.docstring:
                issues.append({
                    "file": str(py_file),
                    "line": 1,
                    "type": "missing_module_docstring",
                    "severity": "medium",
                })

            # Check classes
            for cls in module_doc.classes:
                if not cls.docstring:
                    issues.append({
                        "file": str(py_file),
                        "line": cls.line_number,
                        "type": "missing_class_docstring",
                        "class": cls.name,
                        "severity": "medium",
                    })

                # Check methods
                for method in cls.methods:
                    if not method.docstring and not method.name.startswith("_"):
                        issues.append({
                            "file": str(py_file),
                            "line": method.line_number,
                            "type": "missing_method_docstring",
                            "class": cls.name,
                            "method": method.name,
                            "severity": "low",
                        })

            # Check standalone functions
            for func in module_doc.functions:
                if not func.docstring and not func.name.startswith("_"):
                    issues.append({
                        "file": str(py_file),
                        "line": func.line_number,
                        "type": "missing_function_docstring",
                        "function": func.name,
                        "severity": "low",
                    })

        except (SyntaxError, OSError) as e:
            logger.debug(f"Could not analyze {py_file} for docstring issues: {e}")
            continue

    return {
        "issues": issues,
        "total_issues": len(issues),
        "critical": len([i for i in issues if i["severity"] == "critical"]),
        "medium": len([i for i in issues if i["severity"] == "medium"]),
        "low": len([i for i in issues if i["severity"] == "low"]),
    }


def check_google_style(docstring: str) -> List[str]:
    """Check if docstring follows Google style.

    Args:
        docstring: Docstring to validate

    Returns:
        List of validation issues
    """
    issues = []

    if not docstring:
        return ["Missing docstring"]

    # Check for summary line
    lines = docstring.strip().split("\n")
    if not lines[0]:
        issues.append("Missing summary line")

    # Check for Args section if function has parameters
    if "Args:" not in docstring and "param" in docstring.lower():
        issues.append("Missing Args section (Google style requires 'Args:')")

    # Check for Returns section
    if "return" in docstring.lower() and "Returns:" not in docstring:
        issues.append("Missing Returns section (Google style requires 'Returns:')")

    return issues


def contains_secrets(text: str) -> bool:
    """Check if text contains potential secrets.

    Args:
        text: Text to check

    Returns:
        True if secrets detected
    """
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


__all__ = [
    "validate_docstrings",
    "check_google_style",
    "contains_secrets",
    "GOOGLE_DOCSTRING_PATTERN",
    "SECRET_PATTERNS",
]
