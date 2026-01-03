"""Vertice CLI Utilities Module.

This module provides reusable utility classes for common operations across
the CLI and agent system. All utilities follow SOLID principles and are
designed for testability and maintainability.

Semantic Organization:
    - markdown: Code block extraction from markdown/LLM responses
    - parsing: JSON extraction with multi-strategy fallback
    - streaming: Buffer management for streaming responses
    - error_handler: Unified error handling patterns

Example:
    >>> from vertice_cli.utils import MarkdownExtractor, JSONExtractor
    >>> extractor = MarkdownExtractor()
    >>> code_blocks = extractor.extract_code_blocks(response, language="python")
    >>> json_data = JSONExtractor.extract(response)
"""

from .markdown import (
    MarkdownExtractor,
    CodeBlock,
    extract_code_blocks,
    extract_first_code_block,
)
from .parsing import (
    JSONExtractor,
    JSONExtractionStrategy,
    extract_json,
    extract_json_safe,
)
from .streaming import (
    StreamBuffer,
    BufferConfig,
    collect_stream,
)

__all__ = [
    # Markdown extraction
    "MarkdownExtractor",
    "CodeBlock",
    "extract_code_blocks",
    "extract_first_code_block",
    # JSON parsing
    "JSONExtractor",
    "JSONExtractionStrategy",
    "extract_json",
    "extract_json_safe",
    # Streaming
    "StreamBuffer",
    "BufferConfig",
    "collect_stream",
]
