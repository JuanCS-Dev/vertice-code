"""Markdown Code Block Extraction Utilities.

This module provides utilities for extracting code blocks from markdown text,
particularly useful for parsing LLM responses that contain code snippets.

The extractor supports multiple formats:
    - Fenced code blocks (```python ... ```)
    - Generic code blocks (``` ... ```)
    - Indented code blocks (4 spaces or tab)
    - Inline code patterns (def, class, import statements)

Design Principles:
    - Pure functions where possible (no side effects)
    - Comprehensive type hints for IDE support
    - Regex patterns compiled once for performance
    - Graceful degradation on malformed input

Example:
    >>> extractor = MarkdownExtractor()
    >>> blocks = extractor.extract_code_blocks(response, language="python")
    >>> for block in blocks:
    ...     print(f"Language: {block.language}, Lines: {len(block.content.splitlines())}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional


class ExtractionMode(Enum):
    """Extraction mode for code blocks."""

    FENCED_ONLY = "fenced_only"  # Only ```...``` blocks
    INDENTED_ONLY = "indented_only"  # Only indented blocks
    INLINE_ONLY = "inline_only"  # Only inline patterns
    ALL = "all"  # All patterns (default)


@dataclass(frozen=True)
class CodeBlock:
    """Immutable representation of an extracted code block.

    Attributes:
        content: The extracted code content (without fence markers).
        language: Programming language hint (e.g., "python", "javascript").
        start_line: Line number where block starts in original text.
        end_line: Line number where block ends in original text.
        source: Extraction method used ("fenced", "indented", "inline").
    """

    content: str
    language: str = ""
    start_line: int = 0
    end_line: int = 0
    source: str = "fenced"

    def __len__(self) -> int:
        """Return number of lines in the code block."""
        return len(self.content.splitlines())

    def __bool__(self) -> bool:
        """Return True if block has content."""
        return bool(self.content.strip())


# Compiled regex patterns for performance
_PATTERNS = {
    # Fenced with language: ```python\n...\n```
    "fenced_lang": re.compile(
        r"```(\w+)\s*\n(.*?)```",
        re.DOTALL
    ),
    # Fenced generic: ```\n...\n```
    "fenced_generic": re.compile(
        r"```\s*\n?(.*?)```",
        re.DOTALL
    ),
    # Indented blocks (4 spaces or tab at start of line)
    "indented": re.compile(
        r"(?:^|\n)((?:[ ]{4}|\t).*(?:\n(?:[ ]{4}|\t).*)*)",
        re.MULTILINE
    ),
    # Inline Python patterns (def, class, import, etc.)
    "inline_python": re.compile(
        r"(?:^|\n)((?:def |class |import |from |async def |@).+(?:\n(?:    |\t).+)*)",
        re.MULTILINE
    ),
}


@dataclass
class MarkdownExtractor:
    """Extract code blocks from markdown text.

    This class provides configurable extraction of code blocks from markdown,
    supporting multiple extraction modes and language filtering.

    Attributes:
        mode: Extraction mode (fenced, indented, inline, or all).
        deduplicate: Remove duplicate code blocks.
        min_lines: Minimum lines required for a valid block.

    Example:
        >>> extractor = MarkdownExtractor(mode=ExtractionMode.FENCED_ONLY)
        >>> blocks = extractor.extract_code_blocks(text, language="python")
    """

    mode: ExtractionMode = ExtractionMode.ALL
    deduplicate: bool = True
    min_lines: int = 1
    _seen_hashes: set[int] = field(default_factory=set, repr=False)

    def extract_code_blocks(
        self,
        text: str,
        language: Optional[str] = None,
    ) -> list[CodeBlock]:
        """Extract all code blocks from markdown text.

        Args:
            text: Markdown text containing code blocks.
            language: Filter by language (None = all languages).

        Returns:
            List of CodeBlock objects, ordered by appearance.

        Example:
            >>> blocks = extractor.extract_code_blocks(response, language="python")
        """
        if not text or not text.strip():
            return []

        self._seen_hashes.clear()
        blocks: list[CodeBlock] = []

        # Extract based on mode
        if self.mode in (ExtractionMode.FENCED_ONLY, ExtractionMode.ALL):
            blocks.extend(self._extract_fenced(text, language))

        if self.mode in (ExtractionMode.INDENTED_ONLY, ExtractionMode.ALL):
            blocks.extend(self._extract_indented(text))

        if self.mode in (ExtractionMode.INLINE_ONLY, ExtractionMode.ALL):
            blocks.extend(self._extract_inline(text))

        # Filter by minimum lines
        blocks = [b for b in blocks if len(b) >= self.min_lines]

        # Deduplicate if enabled
        if self.deduplicate:
            blocks = self._deduplicate(blocks)

        return blocks

    def extract_first(
        self,
        text: str,
        language: Optional[str] = None,
    ) -> Optional[CodeBlock]:
        """Extract the first code block from markdown text.

        Args:
            text: Markdown text containing code blocks.
            language: Filter by language (None = any language).

        Returns:
            First matching CodeBlock, or None if not found.
        """
        blocks = self.extract_code_blocks(text, language)
        return blocks[0] if blocks else None

    def iter_blocks(
        self,
        text: str,
        language: Optional[str] = None,
    ) -> Iterator[CodeBlock]:
        """Iterate over code blocks lazily.

        Args:
            text: Markdown text containing code blocks.
            language: Filter by language.

        Yields:
            CodeBlock objects as they are found.
        """
        yield from self.extract_code_blocks(text, language)

    def _extract_fenced(
        self,
        text: str,
        language: Optional[str],
    ) -> list[CodeBlock]:
        """Extract fenced code blocks (```...```)."""
        blocks: list[CodeBlock] = []

        # Try language-specific fences first
        for match in _PATTERNS["fenced_lang"].finditer(text):
            lang = match.group(1).lower()
            content = match.group(2).strip()

            if language and lang != language.lower():
                continue

            if content:
                blocks.append(CodeBlock(
                    content=content,
                    language=lang,
                    source="fenced",
                ))

        # If no language filter, also try generic fences
        if not language:
            for match in _PATTERNS["fenced_generic"].finditer(text):
                content = match.group(1).strip()
                if content and not self._is_already_matched(content, blocks):
                    blocks.append(CodeBlock(
                        content=content,
                        language="",
                        source="fenced",
                    ))

        return blocks

    def _extract_indented(self, text: str) -> list[CodeBlock]:
        """Extract indented code blocks (4 spaces or tab)."""
        blocks: list[CodeBlock] = []

        for match in _PATTERNS["indented"].finditer(text):
            content = match.group(1)
            # Remove leading indentation
            lines = content.splitlines()
            dedented = "\n".join(
                line[4:] if line.startswith("    ") else line[1:] if line.startswith("\t") else line
                for line in lines
            )

            if dedented.strip():
                blocks.append(CodeBlock(
                    content=dedented.strip(),
                    language="",
                    source="indented",
                ))

        return blocks

    def _extract_inline(self, text: str) -> list[CodeBlock]:
        """Extract inline Python patterns (def, class, import, etc.)."""
        blocks: list[CodeBlock] = []

        for match in _PATTERNS["inline_python"].finditer(text):
            content = match.group(1).strip()
            if content:
                blocks.append(CodeBlock(
                    content=content,
                    language="python",
                    source="inline",
                ))

        return blocks

    def _is_already_matched(
        self,
        content: str,
        existing: list[CodeBlock],
    ) -> bool:
        """Check if content is already in existing blocks."""
        normalized = content.strip()
        return any(normalized in b.content or b.content in normalized for b in existing)

    def _deduplicate(self, blocks: list[CodeBlock]) -> list[CodeBlock]:
        """Remove duplicate blocks based on content hash."""
        unique: list[CodeBlock] = []

        for block in blocks:
            content_hash = hash(block.content.strip())
            if content_hash not in self._seen_hashes:
                self._seen_hashes.add(content_hash)
                unique.append(block)

        return unique


# Convenience functions for simple use cases

def extract_code_blocks(
    text: str,
    language: Optional[str] = None,
) -> list[CodeBlock]:
    """Extract all code blocks from markdown text.

    This is a convenience function that creates a default extractor.
    For repeated use, instantiate MarkdownExtractor directly.

    Args:
        text: Markdown text containing code blocks.
        language: Filter by language (None = all languages).

    Returns:
        List of CodeBlock objects.
    """
    return MarkdownExtractor().extract_code_blocks(text, language)


def extract_first_code_block(
    text: str,
    language: Optional[str] = None,
) -> Optional[str]:
    """Extract the first code block content from markdown text.

    Args:
        text: Markdown text containing code blocks.
        language: Filter by language (None = any language).

    Returns:
        Code content string, or None if not found.
    """
    block = MarkdownExtractor().extract_first(text, language)
    return block.content if block else None
