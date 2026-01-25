"""JSON Extraction Utilities with Multi-Strategy Fallback.

This module provides robust JSON extraction from LLM responses, which often
contain JSON embedded in markdown, prose, or malformed structures.

Extraction Strategies (in order of attempt):
    1. STRICT: Direct json.loads() on the input
    2. BRACE_EXTRACTION: Find outermost {...} or [...] and parse
    3. MARKDOWN_BLOCK: Extract from ```json ... ``` blocks
    4. REPAIR: Attempt to fix common JSON errors (trailing commas, etc.)
    5. FALLBACK: Return empty dict/list or default value

Design Principles:
    - Never raise exceptions for malformed input (graceful degradation)
    - Comprehensive type hints for IDE support
    - Stateless functions for thread safety
    - Configurable strategies for different use cases

Example:
    >>> json_data = JSONExtractor.extract(llm_response)
    >>> json_data = extract_json(response, default={"error": "parse_failed"})
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, TypeVar, Union, overload


T = TypeVar("T")
JsonValue = Union[dict[str, Any], list[Any], str, int, float, bool, None]


class JSONExtractionStrategy(Enum):
    """Strategy for JSON extraction."""

    STRICT = auto()  # Direct json.loads only
    BRACE_EXTRACTION = auto()  # Find {...} or [...] and parse
    MARKDOWN_BLOCK = auto()  # Extract from ```json...```
    REPAIR = auto()  # Attempt to fix malformed JSON
    ALL = auto()  # Try all strategies in order


@dataclass(frozen=True)
class ExtractionResult:
    """Result of JSON extraction attempt.

    Attributes:
        success: Whether extraction succeeded.
        data: Extracted JSON data (or default on failure).
        strategy: Strategy that succeeded (or None on failure).
        error: Error message if extraction failed.
    """

    success: bool
    data: JsonValue
    strategy: JSONExtractionStrategy | None = None
    error: str = ""


# Compiled regex patterns
_PATTERNS = {
    # JSON code block: ```json ... ```
    "json_block": re.compile(r"```json\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE),
    # Generic code block that might contain JSON
    "generic_block": re.compile(r"```\s*\n?(\{.*?\}|\[.*?\])\n?```", re.DOTALL),
    # Trailing comma before closing brace/bracket
    "trailing_comma": re.compile(r",\s*([}\]])"),
    # Single quotes that should be double quotes
    "single_quotes": re.compile(r"'([^']*)'"),
    # Unquoted keys
    "unquoted_keys": re.compile(r"(\{|,)\s*(\w+)\s*:"),
}


class JSONExtractor:
    """Extract JSON from text with multi-strategy fallback.

    This class provides configurable JSON extraction with support for
    various input formats commonly seen in LLM responses.

    Example:
        >>> extractor = JSONExtractor(strategy=JSONExtractionStrategy.ALL)
        >>> result = extractor.extract_with_info(response)
        >>> if result.success:
        ...     print(f"Extracted via {result.strategy.name}")
    """

    def __init__(
        self,
        strategy: JSONExtractionStrategy = JSONExtractionStrategy.ALL,
    ) -> None:
        """Initialize extractor with given strategy.

        Args:
            strategy: Extraction strategy to use.
        """
        self.strategy = strategy

    @overload
    def extract(self, text: str) -> dict[str, Any]:
        ...

    @overload
    def extract(self, text: str, default: T) -> dict[str, Any] | T:
        ...

    def extract(
        self,
        text: str,
        default: T | None = None,
    ) -> dict[str, Any] | T:
        """Extract JSON object from text.

        Args:
            text: Input text potentially containing JSON.
            default: Default value if extraction fails.

        Returns:
            Extracted dict or default value.
        """
        result = self.extract_with_info(text)
        if result.success and isinstance(result.data, dict):
            return result.data
        return default if default is not None else {}

    def extract_list(
        self,
        text: str,
        default: list[Any] | None = None,
    ) -> list[Any]:
        """Extract JSON array from text.

        Args:
            text: Input text potentially containing JSON array.
            default: Default value if extraction fails.

        Returns:
            Extracted list or default value.
        """
        result = self.extract_with_info(text)
        if result.success and isinstance(result.data, list):
            return result.data
        return default if default is not None else []

    def extract_with_info(self, text: str) -> ExtractionResult:
        """Extract JSON with detailed result information.

        Args:
            text: Input text potentially containing JSON.

        Returns:
            ExtractionResult with success status, data, and metadata.
        """
        if not text or not text.strip():
            return ExtractionResult(
                success=False,
                data={},
                error="Empty input",
            )

        strategies = self._get_strategies()

        for strategy in strategies:
            result = self._try_strategy(text, strategy)
            if result.success:
                return result

        return ExtractionResult(
            success=False,
            data={},
            error="All extraction strategies failed",
        )

    def _get_strategies(self) -> list[JSONExtractionStrategy]:
        """Get ordered list of strategies to try."""
        if self.strategy == JSONExtractionStrategy.ALL:
            return [
                JSONExtractionStrategy.STRICT,
                JSONExtractionStrategy.MARKDOWN_BLOCK,
                JSONExtractionStrategy.BRACE_EXTRACTION,
                JSONExtractionStrategy.REPAIR,
            ]
        return [self.strategy]

    def _try_strategy(
        self,
        text: str,
        strategy: JSONExtractionStrategy,
    ) -> ExtractionResult:
        """Try a single extraction strategy."""
        try:
            if strategy == JSONExtractionStrategy.STRICT:
                return self._try_strict(text)
            elif strategy == JSONExtractionStrategy.MARKDOWN_BLOCK:
                return self._try_markdown_block(text)
            elif strategy == JSONExtractionStrategy.BRACE_EXTRACTION:
                return self._try_brace_extraction(text)
            elif strategy == JSONExtractionStrategy.REPAIR:
                return self._try_repair(text)
        except Exception as e:
            return ExtractionResult(
                success=False,
                data={},
                error=str(e),
            )

        return ExtractionResult(success=False, data={}, error="Unknown strategy")

    def _try_strict(self, text: str) -> ExtractionResult:
        """Try direct JSON parsing."""
        try:
            data = json.loads(text.strip())
            return ExtractionResult(
                success=True,
                data=data,
                strategy=JSONExtractionStrategy.STRICT,
            )
        except json.JSONDecodeError as e:
            return ExtractionResult(
                success=False,
                data={},
                error=str(e),
            )

    def _try_markdown_block(self, text: str) -> ExtractionResult:
        """Try extracting from ```json ... ``` blocks."""
        # Try explicit JSON blocks first
        match = _PATTERNS["json_block"].search(text)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                return ExtractionResult(
                    success=True,
                    data=data,
                    strategy=JSONExtractionStrategy.MARKDOWN_BLOCK,
                )
            except json.JSONDecodeError:
                pass

        # Try generic code blocks
        match = _PATTERNS["generic_block"].search(text)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                return ExtractionResult(
                    success=True,
                    data=data,
                    strategy=JSONExtractionStrategy.MARKDOWN_BLOCK,
                )
            except json.JSONDecodeError:
                pass

        return ExtractionResult(
            success=False,
            data={},
            error="No valid JSON in markdown blocks",
        )

    def _try_brace_extraction(self, text: str) -> ExtractionResult:
        """Try finding outermost {...} or [...] and parsing."""
        # Try object extraction
        obj_result = self._extract_balanced(text, "{", "}")
        if obj_result:
            try:
                data = json.loads(obj_result)
                return ExtractionResult(
                    success=True,
                    data=data,
                    strategy=JSONExtractionStrategy.BRACE_EXTRACTION,
                )
            except json.JSONDecodeError:
                pass

        # Try array extraction
        arr_result = self._extract_balanced(text, "[", "]")
        if arr_result:
            try:
                data = json.loads(arr_result)
                return ExtractionResult(
                    success=True,
                    data=data,
                    strategy=JSONExtractionStrategy.BRACE_EXTRACTION,
                )
            except json.JSONDecodeError:
                pass

        return ExtractionResult(
            success=False,
            data={},
            error="No valid JSON found in braces",
        )

    def _try_repair(self, text: str) -> ExtractionResult:
        """Try repairing common JSON errors."""
        # Extract potential JSON first
        candidate = self._extract_balanced(text, "{", "}") or text

        repaired = candidate

        # Fix trailing commas
        repaired = _PATTERNS["trailing_comma"].sub(r"\1", repaired)

        # Try parsing the repaired version
        try:
            data = json.loads(repaired)
            return ExtractionResult(
                success=True,
                data=data,
                strategy=JSONExtractionStrategy.REPAIR,
            )
        except json.JSONDecodeError as e:
            return ExtractionResult(
                success=False,
                data={},
                error=f"Repair failed: {e}",
            )

    def _extract_balanced(
        self,
        text: str,
        open_char: str,
        close_char: str,
    ) -> str | None:
        """Extract balanced substring between open and close characters."""
        start = text.find(open_char)
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

        return None


# Convenience functions


def extract_json(
    text: str,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract JSON object from text with all strategies.

    This is a convenience function for simple use cases.

    Args:
        text: Input text potentially containing JSON.
        default: Default value if extraction fails.

    Returns:
        Extracted dict or default value.
    """
    return JSONExtractor().extract(text, default or {})


def extract_json_safe(text: str) -> ExtractionResult:
    """Extract JSON with detailed result information.

    Args:
        text: Input text potentially containing JSON.

    Returns:
        ExtractionResult with success status and metadata.
    """
    return JSONExtractor().extract_with_info(text)
