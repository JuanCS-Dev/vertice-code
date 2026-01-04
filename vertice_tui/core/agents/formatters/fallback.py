"""
Fallback Formatters - Markdown, String, and generic fallback.

Catch-all formatters for passthrough and unrecognized data structures.
"""

from typing import Any, AsyncIterator


class MarkdownFormatter:
    """
    Format pre-formatted markdown content passthrough.

    Expected data structure:
        {
            "formatted_markdown": str  # or
            "markdown": str
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains pre-formatted markdown content."""
        if not isinstance(data, dict):
            return False
        return "formatted_markdown" in data or "markdown" in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Pass through pre-formatted markdown content."""
        if "formatted_markdown" in data:
            yield data["formatted_markdown"]
        elif "markdown" in data:
            yield data["markdown"]


class StringFormatter:
    """
    Format plain string data passthrough.

    Handles the simplest case where agent result data is already a string.
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data is a plain string."""
        return isinstance(data, str)

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Pass through string data as-is."""
        yield data


class FallbackFormatter:
    """
    Fallback formatter for unrecognized data structures.

    This formatter ALWAYS matches and must be LAST in the FORMATTERS registry.
    Provides generic formatting for any dict-like structure.
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Always returns True - this is the catch-all formatter."""
        return True

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format arbitrary data structures generically."""
        if isinstance(data, dict) and data:
            yield "## Result\n\n"
            for key, value in data.items():
                if isinstance(value, list):
                    yield f"**{key}:**\n"
                    for item in value[:10]:
                        yield f"- {item}\n"
                else:
                    yield f"**{key}:** {value}\n"

            if "infrastructure" in data:
                infra = data["infrastructure"]
                if isinstance(infra, dict) and not any(
                    k in str(infra) for k in ["Deployment Plan", "DevOps"]
                ):
                    yield "\n**Infrastructure details:**\n"
                    for k, v in infra.items():
                        yield f"- {k}: {v}\n"

            if "configuration" in data:
                yield "\n**Configuration details:**\n"
                for k, v in data["configuration"].items():
                    yield f"- {k}: {v}\n"

        elif reasoning and reasoning != "None":
            yield f"{reasoning}\n"
