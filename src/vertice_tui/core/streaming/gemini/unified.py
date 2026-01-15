"""
Unified Gemini Streamer - Automatic fallback with timeout protection.

Tries SDK first, falls back to HTTPX if unavailable.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from .config import GeminiStreamConfig
from .base import BaseStreamer
from .sdk import GeminiSDKStreamer
from .httpx_streamer import GeminiHTTPXStreamer

logger = logging.getLogger(__name__)


class GeminiStreamer:
    """
    Unified Gemini streamer with automatic fallback.

    Tries SDK first, falls back to HTTPX if SDK unavailable.
    Includes timeout protection and chunk stall detection.

    Example:
        >>> config = GeminiStreamConfig(api_key="...", model_name="gemini-2.5-pro")
        >>> streamer = GeminiStreamer(config)
        await streamer.initialize()

        async for chunk in streamer.stream("Hello!"):
            print(chunk, end="", flush=True)
    """

    def __init__(self, config: GeminiStreamConfig) -> None:
        """Initialize unified streamer.

        Args:
            config: Streaming configuration
        """
        self.config = config
        self._sdk_streamer = GeminiSDKStreamer(config)
        self._httpx_streamer = GeminiHTTPXStreamer(config)
        self._active_streamer: Optional[BaseStreamer] = None

    async def initialize(self) -> bool:
        """
        Initialize streamers with automatic fallback.

        Tries SDK first, falls back to HTTPX if unavailable.
        """
        try:
            # Apply timeout to initialization
            if await asyncio.wait_for(
                self._sdk_streamer.initialize(), timeout=self.config.init_timeout
            ):
                self._active_streamer = self._sdk_streamer
                logger.info("Using SDK streamer")
                return True
        except asyncio.TimeoutError:
            logger.warning("SDK initialization timed out")
        except Exception as e:
            logger.warning(f"SDK initialization failed: {e}")

        # Try HTTPX fallback
        try:
            if await asyncio.wait_for(
                self._httpx_streamer.initialize(), timeout=self.config.init_timeout
            ):
                self._active_streamer = self._httpx_streamer
                logger.info("Using HTTPX streamer (fallback)")
                return True
        except asyncio.TimeoutError:
            logger.warning("HTTPX initialization timed out")
        except Exception as e:
            logger.error(f"HTTPX initialization failed: {e}")

        return False

    @property
    def is_initialized(self) -> bool:
        """Check if any streamer is initialized."""
        return self._active_streamer is not None and self._active_streamer.is_initialized

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream response with timeout protection.

        Includes chunk stall detection - if no chunks received for
        chunk_timeout seconds, raises TimeoutError.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation context
            tools: Available tools

        Yields:
            Response chunks as strings
        """
        if not self._active_streamer:
            yield "❌ Streamer not initialized"
            return

        last_chunk_time = time.time()

        try:
            async for chunk in self._active_streamer.stream(prompt, system_prompt, context, tools):
                current_time = time.time()

                # Check for chunk timeout (stall detection)
                if current_time - last_chunk_time > self.config.chunk_timeout:
                    raise asyncio.TimeoutError(f"No response for {self.config.chunk_timeout}s")

                last_chunk_time = current_time
                yield chunk

        except asyncio.TimeoutError as e:
            yield f"\n⚠️ {str(e)}"
            raise
