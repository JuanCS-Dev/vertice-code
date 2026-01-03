"""
planner/utils.py: Utility Functions.

Pure utility functions for JSON parsing and other common operations.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders

NOTE: This module now delegates to vertice_cli.utils for implementations.
      Functions here are kept for backward compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# Import from unified utils module (eliminates code duplication)
from vertice_cli.utils.parsing import extract_json


def robust_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Enterprise-grade JSON parsing with multiple fallback strategies.
    Handles all common LLM output formats.

    NOTE: Delegates to JSONExtractor from vertice_cli.utils.parsing.

    Args:
        text: Raw text that may contain JSON

    Returns:
        Parsed JSON as dict, or None if parsing fails
    """
    result = extract_json(text, default=None)
    return result if result else None


def extract_json_from_markdown(text: str) -> str:
    """
    Extract JSON content from markdown code blocks.

    NOTE: Delegates to MarkdownExtractor from vertice_cli.utils.markdown.

    Args:
        text: Text potentially containing markdown-wrapped JSON

    Returns:
        Extracted content without markdown formatting
    """
    from vertice_cli.utils.markdown import extract_first_code_block

    # Try to extract first code block (json or any)
    block = extract_first_code_block(text, language="json")
    if block:
        return block

    block = extract_first_code_block(text)
    if block:
        return block

    return text.strip()


__all__ = [
    "robust_json_parse",
    "extract_json_from_markdown",
]
