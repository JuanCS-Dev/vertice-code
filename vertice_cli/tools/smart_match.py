"""
Smart Match - Robust String Matching for Code Editing
======================================================

Implements layered matching strategy inspired by:
- Aider: https://aider.chat/docs/more/edit-formats.html
- RooCode: Middle-out fuzzy matching
- Anthropic Claude Code: Precise edit application

Layers (in priority order):
1. Exact match
2. Whitespace-normalized match
3. Indentation-flexible match
4. Line-by-line fuzzy match
5. Substring similarity match

Author: Vertice Team
Date: 2026-01-03
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import logging

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Type of match found."""

    EXACT = "exact"
    WHITESPACE_NORMALIZED = "whitespace_normalized"
    INDENTATION_FLEXIBLE = "indentation_flexible"
    FUZZY_LINE = "fuzzy_line"
    FUZZY_BLOCK = "fuzzy_block"
    NOT_FOUND = "not_found"


@dataclass
class MatchResult:
    """Result of a smart match operation."""

    found: bool
    match_type: MatchType
    start: int = 0
    end: int = 0
    matched_text: str = ""
    confidence: float = 1.0
    suggestion: str = ""


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving structure.

    - Converts tabs to spaces
    - Normalizes line endings to \n
    - Strips trailing whitespace from lines
    - Preserves leading indentation
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = []
    for line in lines:
        # Convert tabs to 4 spaces (Python standard)
        line = line.replace("\t", "    ")
        # Strip trailing whitespace only
        line = line.rstrip()
        normalized.append(line)
    return "\n".join(normalized)


def strip_common_indent(text: str) -> Tuple[str, int]:
    """Strip common leading indentation from all lines.

    Returns:
        Tuple of (stripped_text, indent_amount)
    """
    lines = text.split("\n")
    non_empty_lines = [l for l in lines if l.strip()]

    if not non_empty_lines:
        return text, 0

    # Find minimum indentation
    min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines)

    # Strip that amount from all lines
    stripped_lines = []
    for line in lines:
        if line.strip():
            stripped_lines.append(line[min_indent:])
        else:
            stripped_lines.append("")

    return "\n".join(stripped_lines), min_indent


def find_with_any_indent(search: str, content: str) -> Optional[Tuple[int, int, str]]:
    """Find search text with any indentation level.

    Returns:
        Tuple of (start, end, matched_text) or None
    """
    stripped_search, _ = strip_common_indent(search)
    search_lines = stripped_search.split("\n")
    content_lines = content.split("\n")

    # Try to find the pattern with any indentation
    for i in range(len(content_lines) - len(search_lines) + 1):
        match = True
        matched_lines = []

        for j, search_line in enumerate(search_lines):
            content_line = content_lines[i + j]

            # Compare stripped content
            if search_line.strip() != content_line.strip():
                match = False
                break
            matched_lines.append(content_line)

        if match:
            # Calculate position in original content
            start = sum(len(l) + 1 for l in content_lines[:i])
            matched_text = "\n".join(matched_lines)
            end = start + len(matched_text)
            return (start, end, matched_text)

    return None


def find_fuzzy_lines(
    search: str, content: str, threshold: float = 0.8
) -> Optional[Tuple[int, int, str, float]]:
    """Find search using line-by-line fuzzy matching.

    Uses difflib to find similar line sequences.

    Returns:
        Tuple of (start, end, matched_text, confidence) or None
    """
    search_lines = search.split("\n")
    content_lines = content.split("\n")

    if len(search_lines) > len(content_lines):
        return None

    best_match = None
    best_ratio = threshold

    # Slide window over content
    for i in range(len(content_lines) - len(search_lines) + 1):
        window = content_lines[i : i + len(search_lines)]

        # Calculate similarity ratio
        matcher = difflib.SequenceMatcher(None, "\n".join(search_lines), "\n".join(window))
        ratio = matcher.ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            start = sum(len(l) + 1 for l in content_lines[:i])
            matched_text = "\n".join(window)
            end = start + len(matched_text)
            best_match = (start, end, matched_text, ratio)

    return best_match


def find_closest_matches(search: str, content: str, n: int = 3) -> List[str]:
    """Find the n closest matching blocks in content.

    Useful for error messages suggesting what the user might have meant.
    """
    search_lines = search.split("\n")
    content_lines = content.split("\n")
    search_len = len(search_lines)

    candidates = []

    # Create sliding windows of similar size
    for i in range(len(content_lines) - search_len + 1):
        window = "\n".join(content_lines[i : i + search_len])
        matcher = difflib.SequenceMatcher(None, search, window)
        ratio = matcher.ratio()
        candidates.append((ratio, window, i + 1))  # i+1 for 1-indexed line number

    # Sort by similarity and return top n
    candidates.sort(reverse=True, key=lambda x: x[0])

    results = []
    for ratio, text, line_num in candidates[:n]:
        if ratio > 0.3:  # Minimum similarity threshold
            preview = text[:200] + ("..." if len(text) > 200 else "")
            results.append(f"Line {line_num} ({ratio:.0%} similar):\n{preview}")

    return results


def smart_find(search: str, content: str, strict: bool = False) -> MatchResult:
    """
    Find search string in content using layered matching strategy.

    Layers:
    1. Exact match - search string exists verbatim
    2. Whitespace normalized - same content, different whitespace
    3. Indentation flexible - same content, different indentation
    4. Fuzzy line match - similar lines (80%+ similarity)
    5. Fuzzy block match - similar blocks (70%+ similarity)

    Args:
        search: Text to find
        content: Content to search in
        strict: If True, only use exact and whitespace-normalized matching

    Returns:
        MatchResult with match details and suggestions
    """
    # Layer 1: Exact match
    if search in content:
        start = content.index(search)
        return MatchResult(
            found=True,
            match_type=MatchType.EXACT,
            start=start,
            end=start + len(search),
            matched_text=search,
            confidence=1.0,
        )

    # Layer 2: Whitespace-normalized match
    norm_search = normalize_whitespace(search)
    norm_content = normalize_whitespace(content)

    if norm_search in norm_content:
        # Find position in original content
        norm_start = norm_content.index(norm_search)

        # Map back to original position (approximate)
        # Count newlines to find line number
        line_num = norm_content[:norm_start].count("\n")
        original_lines = content.split("\n")

        if line_num < len(original_lines):
            start = sum(len(l) + 1 for l in original_lines[:line_num])
            search_line_count = norm_search.count("\n") + 1
            matched_text = "\n".join(original_lines[line_num : line_num + search_line_count])

            return MatchResult(
                found=True,
                match_type=MatchType.WHITESPACE_NORMALIZED,
                start=start,
                end=start + len(matched_text),
                matched_text=matched_text,
                confidence=0.95,
                suggestion="Whitespace differences were normalized",
            )

    if strict:
        # In strict mode, don't use fuzzy matching
        closest = find_closest_matches(search, content)
        return MatchResult(
            found=False,
            match_type=MatchType.NOT_FOUND,
            confidence=0.0,
            suggestion=_format_not_found_message(search, closest),
        )

    # Layer 3: Indentation-flexible match
    indent_match = find_with_any_indent(search, content)
    if indent_match:
        start, end, matched_text = indent_match
        return MatchResult(
            found=True,
            match_type=MatchType.INDENTATION_FLEXIBLE,
            start=start,
            end=end,
            matched_text=matched_text,
            confidence=0.9,
            suggestion="Indentation was adjusted to match file",
        )

    # Layer 4: Fuzzy line match (80% threshold)
    fuzzy_match = find_fuzzy_lines(search, content, threshold=0.8)
    if fuzzy_match:
        start, end, matched_text, ratio = fuzzy_match
        return MatchResult(
            found=True,
            match_type=MatchType.FUZZY_LINE,
            start=start,
            end=end,
            matched_text=matched_text,
            confidence=ratio,
            suggestion=f"Fuzzy match found ({ratio:.0%} similar). Review the change carefully.",
        )

    # Layer 5: Lower threshold fuzzy (70%) - last resort
    fuzzy_match_low = find_fuzzy_lines(search, content, threshold=0.7)
    if fuzzy_match_low:
        start, end, matched_text, ratio = fuzzy_match_low
        return MatchResult(
            found=True,
            match_type=MatchType.FUZZY_BLOCK,
            start=start,
            end=end,
            matched_text=matched_text,
            confidence=ratio,
            suggestion=f"Low-confidence match ({ratio:.0%}). Manual verification recommended.",
        )

    # Not found - provide helpful suggestions
    closest = find_closest_matches(search, content)
    return MatchResult(
        found=False,
        match_type=MatchType.NOT_FOUND,
        confidence=0.0,
        suggestion=_format_not_found_message(search, closest),
    )


def _format_not_found_message(search: str, closest: List[str]) -> str:
    """Format a helpful not-found error message."""
    search_preview = search[:150] + ("..." if len(search) > 150 else "")

    msg = f"""Search string not found in file.

SEARCHED FOR:
```
{search_preview}
```

"""

    if closest:
        msg += "CLOSEST MATCHES IN FILE:\n"
        for i, match in enumerate(closest, 1):
            msg += f"\n{i}. {match}\n"
        msg += "\nHINT: Copy the EXACT text from the file using read_file first.\n"
    else:
        msg += "No similar content found. The file might not contain this text.\n"
        msg += "HINT: Use read_file to see the current file content.\n"

    return msg


def apply_replacement(content: str, match: MatchResult, replacement: str) -> str:
    """Apply a replacement using a match result.

    Args:
        content: Original content
        match: MatchResult from smart_find
        replacement: Text to replace with

    Returns:
        Modified content
    """
    if not match.found:
        raise ValueError("Cannot apply replacement: no match found")

    # Use the matched_text for replacement to handle fuzzy matches correctly
    return content[: match.start] + replacement + content[match.end :]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MatchType",
    "MatchResult",
    "smart_find",
    "apply_replacement",
    "normalize_whitespace",
    "find_closest_matches",
]
