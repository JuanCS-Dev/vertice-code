"""
ResultFormatter Protocol - Interface for agent result formatters.

All formatters must implement this protocol to be used in the
FORMATTERS registry.
"""

from typing import Any, AsyncIterator, Protocol


class ResultFormatter(Protocol):
    """
    Protocol defining the interface for agent result formatters.

    All formatters must implement this protocol to be used in the FORMATTERS
    registry. The protocol uses static methods to allow stateless formatting.
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """
        Check if this formatter can handle the given data.

        Args:
            data: The data portion of an AgentResponse (result.data)

        Returns:
            True if this formatter can handle the data structure
        """
        ...

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """
        Format the data into markdown chunks.

        Args:
            data: The data to format (from AgentResponse.data)
            reasoning: The reasoning string (from AgentResponse.reasoning)

        Yields:
            Markdown-formatted string chunks for streaming display
        """
        ...
