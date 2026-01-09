"""Vertice CLI Utilities Module.

This module provides reusable utility classes for common operations across
the CLI and agent system. All utilities follow SOLID principles and are
designed for testability and maintainability.

Semantic Organization:
    - markdown: Code block extraction from markdown/LLM responses
    - parsing: JSON extraction with multi-strategy fallback
    - streaming: Buffer management for streaming responses
    - prompts: Unified system prompt building for agents

Example:
    >>> from vertice_cli.utils import MarkdownExtractor, JSONExtractor
    >>> extractor = MarkdownExtractor()
    >>> code_blocks = extractor.extract_code_blocks(response, language="python")
    >>> json_data = JSONExtractor.extract(response)

    >>> from vertice_cli.utils import PromptBuilder
    >>> builder = PromptBuilder("Architect")
    >>> builder.add_role("Feasibility Analyst", ["READ_ONLY"])
    >>> prompt = builder.build()
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
from .prompts import (
    XMLPromptBuilder,
    PromptBuilder,  # Alias for XMLPromptBuilder
    Example,
    ToolSpec,
    OutputFormat,
    AgenticMode,
    build_agent_prompt,
    create_reviewer_prompt,
    create_architect_prompt,
    create_coder_prompt,
    REVIEWER_PROMPT,
    ARCHITECT_PROMPT,
    CODER_PROMPT,
)
from .error_handler import (
    # Enums
    ErrorCategory,
    CircuitState,
    # Core classes
    ErrorContext,
    RetryPolicy,
    CircuitBreaker,
    ErrorClassifier,
    FallbackChain,
    ErrorAggregator,
    # Pre-configured policies
    AGGRESSIVE_RETRY,
    CONSERVATIVE_RETRY,
    API_RETRY,
    # Functions
    retry_with_backoff,
    retry_sync_with_backoff,
    with_retry,
    # Context managers
    error_boundary,
    sync_error_boundary,
    # Exceptions
    CircuitOpenError,
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
    # Prompts
    "XMLPromptBuilder",
    "PromptBuilder",
    "Example",
    "ToolSpec",
    "OutputFormat",
    "AgenticMode",
    "build_agent_prompt",
    "create_reviewer_prompt",
    "create_architect_prompt",
    "create_coder_prompt",
    "REVIEWER_PROMPT",
    "ARCHITECT_PROMPT",
    "CODER_PROMPT",
    # Error handling
    "ErrorCategory",
    "CircuitState",
    "ErrorContext",
    "RetryPolicy",
    "CircuitBreaker",
    "ErrorClassifier",
    "FallbackChain",
    "ErrorAggregator",
    "AGGRESSIVE_RETRY",
    "CONSERVATIVE_RETRY",
    "API_RETRY",
    "retry_with_backoff",
    "retry_sync_with_backoff",
    "with_retry",
    "error_boundary",
    "sync_error_boundary",
    "CircuitOpenError",
]
