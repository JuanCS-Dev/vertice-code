"""
Agent Result Formatters - Strategy pattern for agent output formatting.

This module provides a collection of specialized formatters for different agent
response types. Each formatter implements the ResultFormatter protocol.

Architecture:
    1. Each formatter has a `can_format(data)` method to check if it handles the data
    2. The `format(data, reasoning)` method yields markdown chunks
    3. The FORMATTERS registry determines evaluation order (most specific first)
    4. FallbackFormatter always matches as the last resort

Usage:
    from vertice_tui.core.agents.formatters import format_agent_result

    async for chunk in format_agent_result(agent_response):
        print(chunk, end='')
"""

from typing import Any, AsyncIterator, List

from .protocol import ResultFormatter
from .helpers import get_severity_emoji, format_list_items, yield_dict_items
from .architect import ArchitectFormatter
from .reviewer import ReviewerFormatter
from .explorer import ExplorerFormatter
from .devops import DevOpsFormatter, DevOpsResponseFormatter
from .code_agents import TestingFormatter, RefactorerFormatter, DocumentationFormatter
from .fallback import MarkdownFormatter, StringFormatter, FallbackFormatter


# Order matters - more specific formatters first, FallbackFormatter last
FORMATTERS: List[type] = [
    ArchitectFormatter,
    ReviewerFormatter,
    ExplorerFormatter,
    DevOpsFormatter,
    DevOpsResponseFormatter,
    TestingFormatter,
    RefactorerFormatter,
    DocumentationFormatter,
    MarkdownFormatter,
    StringFormatter,
    FallbackFormatter,
]


async def format_agent_result(result: Any) -> AsyncIterator[str]:
    """
    Format agent result using appropriate formatter.

    Main entry point for formatting agent responses.

    Args:
        result: AgentResponse or similar result object

    Yields:
        Formatted markdown chunks
    """
    # Extract data and reasoning from result
    if hasattr(result, "data") and hasattr(result, "reasoning"):
        data = result.data
        reasoning = result.reasoning or ""
    elif hasattr(result, "data"):
        data = result.data
        reasoning = ""
    elif hasattr(result, "result"):
        yield str(result.result)
        return
    else:
        yield str(result)
        return

    # Find matching formatter
    for formatter_class in FORMATTERS:
        if formatter_class.can_format(data):
            async for chunk in formatter_class.format(data, reasoning):
                yield chunk
            return

    # Should never reach here due to FallbackFormatter
    yield str(data)


__all__ = [
    # Main entry point
    "format_agent_result",
    # Protocol
    "ResultFormatter",
    # Helpers
    "get_severity_emoji",
    "format_list_items",
    "yield_dict_items",
    # Formatters
    "ArchitectFormatter",
    "ReviewerFormatter",
    "ExplorerFormatter",
    "DevOpsFormatter",
    "DevOpsResponseFormatter",
    "TestingFormatter",
    "RefactorerFormatter",
    "DocumentationFormatter",
    "MarkdownFormatter",
    "StringFormatter",
    "FallbackFormatter",
    # Registry
    "FORMATTERS",
]
