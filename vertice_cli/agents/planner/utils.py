"""
planner/utils.py: Utility Functions.

Pure utility functions for JSON parsing and other common operations.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


def robust_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Enterprise-grade JSON parsing with multiple fallback strategies.
    Handles all common LLM output formats.

    Strategies:
    1. Strip markdown code blocks
    2. Direct parse
    3. Find JSON object with regex
    4. Fix common issues (trailing commas)
    5. Extract JSON array if present

    Args:
        text: Raw text that may contain JSON

    Returns:
        Parsed JSON as dict, or None if parsing fails
    """
    # Strategy 1: Strip markdown blocks
    clean_text = text.strip()

    # Remove markdown code blocks
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0]
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0]

    clean_text = clean_text.strip()

    # Strategy 2: Direct parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find JSON object with regex
    try:
        # Match outermost braces
        match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', clean_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass

    # Strategy 4: Fix common issues
    try:
        # Remove trailing commas
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', clean_text)
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        pass

    # Strategy 5: Extract JSON array if present
    try:
        match = re.search(r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]', clean_text, re.DOTALL)
        if match:
            arr = json.loads(match.group(0))
            return {"sops": arr}  # Wrap in expected structure
    except (json.JSONDecodeError, AttributeError):
        pass

    return None


def extract_json_from_markdown(text: str) -> str:
    """
    Extract JSON content from markdown code blocks.

    Args:
        text: Text potentially containing markdown-wrapped JSON

    Returns:
        Extracted content without markdown formatting
    """
    clean_text = text.strip()

    if "```json" in clean_text:
        return clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        return clean_text.split("```")[1].split("```")[0].strip()

    return clean_text


__all__ = [
    "robust_json_parse",
    "extract_json_from_markdown",
]
