"""
Helper functions shared by formatters.

Utility functions for severity mapping, list formatting,
and dictionary item yielding.
"""

from typing import Any, AsyncIterator, Dict, List, Optional


def get_severity_emoji(severity: str) -> str:
    """
    Map issue severity level to a colored emoji indicator.

    Args:
        severity: Severity level string (CRITICAL, HIGH, MEDIUM, LOW, INFO)

    Returns:
        Emoji string representing the severity level
    """
    return {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "INFO": "ℹ️"
    }.get(severity, "⚪")


def format_list_items(items: List[Any], prefix: str = "- ") -> str:
    """
    Format a list of items as markdown bullet points.

    Args:
        items: List of items to format (will be converted to str)
        prefix: String prefix for each item (default: "- " for bullets)

    Returns:
        Concatenated string with each item on a new line with prefix
    """
    return "".join(f"{prefix}{item}\n" for item in items)


async def yield_dict_items(
    data: Dict[str, Any],
    keys: List[str],
    headers: Optional[Dict[str, str]] = None
) -> AsyncIterator[str]:
    """
    Async generator that yields formatted dictionary items as markdown.

    Args:
        data: Source dictionary containing the data
        keys: List of keys to extract and format (in order)
        headers: Optional mapping of key -> custom header text

    Yields:
        Markdown-formatted strings for each non-empty value
    """
    headers = headers or {}
    for key in keys:
        value = data.get(key)
        if not value:
            continue
        header = headers.get(key, f"**{key.title()}:**")
        if isinstance(value, list):
            yield f"\n{header}\n"
            for item in value:
                yield f"- {item}\n"
        else:
            yield f"{header} {value}\n"
