"""
Base Streamer - Protocol for streaming implementations.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from .config import GeminiStreamConfig


class BaseStreamer:
    """Base class for streaming implementations."""

    def __init__(self, config: GeminiStreamConfig) -> None:
        """Initialize streamer with configuration.

        Args:
            config: Streaming configuration
        """
        self.config = config
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the streamer. Returns True if successful."""
        raise NotImplementedError

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream response chunks.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation context
            tools: Available tools

        Yields:
            Response chunks as strings
        """
        raise NotImplementedError
        yield  # Make this a generator

    @property
    def is_initialized(self) -> bool:
        """Check if streamer is initialized."""
        return self._initialized
