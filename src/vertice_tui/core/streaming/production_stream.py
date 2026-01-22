"""
Production Streaming Module - Enterprise-grade resilience for LLM streaming.
=============================================================================

Provides production-grade streaming features:
- SSE Heartbeat (30s) - Prevents connection reset on long responses
- Backpressure Queue - Bounded queue prevents memory exhaustion
- Reconnect Mid-Stream - Checkpoint + retry on network failure

Based on 2025 best practices:
- SSE Best Practices: https://procedure.tech/blogs/sse-streaming-2025
- Asyncio Backpressure: https://softwarepatternslexicon.com/patterns-python/9/4/
- Claude Code Streaming: Production-grade patterns

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from .gemini import GeminiStreamConfig, GeminiStreamer

logger = logging.getLogger(__name__)


# =============================================================================
# STREAMING CHECKPOINT FOR RECONNECT
# =============================================================================


@dataclass
class StreamCheckpoint:
    """Checkpoint for mid-stream recovery.

    Stores accumulated content and context to allow reconnection
    after network failures without losing progress.

    Attributes:
        accumulated_content: All text received so far
        chunk_count: Number of chunks processed
        last_chunk_time: Timestamp of last chunk
        context_snapshot: Conversation context for reconnect
    """

    accumulated_content: str = ""
    chunk_count: int = 0
    last_chunk_time: float = field(default_factory=time.time)
    context_snapshot: Optional[List[Dict[str, str]]] = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def update(self, chunk: str) -> None:
        """Update checkpoint with new chunk (thread-safe).

        Args:
            chunk: New text chunk to add
        """
        async with self._lock:
            self.accumulated_content += chunk
            self.chunk_count += 1
            self.last_chunk_time = time.time()

    async def can_reconnect(self) -> bool:
        """Check if we have enough context to reconnect (thread-safe).

        Returns:
            True if checkpoint has enough data for reconnection
        """
        async with self._lock:
            return self.chunk_count > 0 and len(self.accumulated_content) > 0


# =============================================================================
# PRODUCTION STREAMER WITH HEARTBEAT, BACKPRESSURE & RECONNECT
# =============================================================================


class ProductionGeminiStreamer:
    """Production-grade Gemini streamer with enterprise reliability.

    Features:
        1. SSE Heartbeat (30s) - Prevents connection reset on long responses
        2. Backpressure Queue - Bounded queue prevents memory exhaustion
        3. Reconnect Mid-Stream - Checkpoint + retry on network failure

    Example:
        >>> config = GeminiStreamConfig(api_key="...", model_name="gemini-3-pro")
        >>> streamer = GeminiStreamer(config)
        >>> await streamer.initialize()
        >>> async for chunk in streamer.stream_with_resilience("Hello!"):
        ...     print(chunk, end="", flush=True)
    """

    # Heartbeat marker (RFC 6797 compliant SSE comment)
    HEARTBEAT_MARKER = ": heartbeat\n"

    def __init__(self, config: GeminiStreamConfig) -> None:
        """Initialize production streamer.

        Args:
            config: Streaming configuration with resilience settings
        """
        self.config = config
        self._base_streamer = GeminiStreamer(config)
        self._initialized = False

        # Heartbeat state
        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._stream_active = False
        self._last_activity_time = time.time()

        # Backpressure queue
        self._chunk_queue: Optional[asyncio.Queue[Optional[str]]] = None
        self._producer_task: Optional[asyncio.Task[None]] = None
        self._producer_exception: Optional[Exception] = None

        # Checkpoint for reconnect
        self._checkpoint = StreamCheckpoint()
        self._reconnect_attempts = 0

    async def initialize(self) -> bool:
        """Initialize the production streamer.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        success = await self._base_streamer.initialize()
        if success:
            self._initialized = True
            logger.info(
                f"ProductionGeminiStreamer initialized: "
                f"heartbeat={self.config.heartbeat_interval}s, "
                f"queue_size={self.config.backpressure_queue_size}, "
                f"max_reconnect={self.config.max_reconnect_attempts}"
            )
        return success

    @property
    def is_initialized(self) -> bool:
        """Check if streamer is initialized."""
        return self._initialized and self._base_streamer.is_initialized

    async def _heartbeat_loop(self) -> None:
        """Emit heartbeat markers to keep connection alive.

        RFC 6797 compliant: SSE comments starting with ':'
        are ignored by clients but keep the connection alive.
        """
        while self._stream_active:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                if self._stream_active:
                    time_since_activity = time.time() - self._last_activity_time
                    if time_since_activity >= self.config.heartbeat_interval * 0.9:
                        if self._chunk_queue and not self._chunk_queue.full():
                            await self._chunk_queue.put(self.HEARTBEAT_MARKER)
                            logger.debug("Heartbeat sent")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")

    async def _producer_loop(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[List[Dict[str, str]]],
        tools: Optional[List[Any]],
    ) -> None:
        """Produce chunks from base streamer into queue.

        Uses backpressure - waits if queue is full.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation history
            tools: Available tools
        """
        try:
            async for chunk in self._base_streamer.stream(prompt, system_prompt, context, tools):
                if not self._stream_active:
                    break

                self._last_activity_time = time.time()
                await self._chunk_queue.put(chunk)

                await self._checkpoint.update(chunk)
                if self._checkpoint.chunk_count % self.config.checkpoint_interval == 0:
                    self._checkpoint.context_snapshot = context
                    logger.debug(
                        f"Checkpoint: {self._checkpoint.chunk_count} chunks, "
                        f"{len(self._checkpoint.accumulated_content)} chars"
                    )

        except Exception as e:
            self._producer_exception = e
            logger.error(f"Producer error: {e}")
        finally:
            if self._chunk_queue:
                await self._chunk_queue.put(None)

    async def _consumer_loop(self) -> AsyncIterator[str]:
        """Consume chunks from queue with 60fps throttle.

        Filters heartbeat markers before yielding.

        Yields:
            Response chunks (excluding heartbeats)
        """
        last_yield_time = time.time()
        min_interval = 0.016  # 60fps = 16.67ms

        while self._stream_active:
            try:
                try:
                    chunk = await asyncio.wait_for(
                        self._chunk_queue.get(), timeout=self.config.chunk_timeout
                    )
                except asyncio.TimeoutError:
                    if self._producer_exception:
                        raise self._producer_exception
                    continue

                if chunk is None:
                    break

                if chunk == self.HEARTBEAT_MARKER:
                    continue

                current_time = time.time()
                time_since_last = current_time - last_yield_time

                # OPTIMIZATION: Instant yield for first chunk or if interval passed
                if last_yield_time > 0 and time_since_last < min_interval:
                    await asyncio.sleep(min_interval - time_since_last)

                last_yield_time = time.time()
                yield chunk

            except asyncio.CancelledError:
                break

    async def _try_reconnect(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[List[Dict[str, str]]],
        tools: Optional[List[Any]],
    ) -> Optional[AsyncIterator[str]]:
        """Attempt to reconnect after network failure.

        Uses checkpoint to continue from where we left off.

        Args:
            prompt: Original user prompt
            system_prompt: System instructions
            context: Conversation history
            tools: Available tools

        Returns:
            New stream iterator or None if reconnect failed
        """
        if self._reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.warning(f"Max reconnect attempts ({self.config.max_reconnect_attempts}) reached")
            return None

        if not await self._checkpoint.can_reconnect():
            logger.warning("No checkpoint available for reconnect")
            return None

        self._reconnect_attempts += 1
        delay = self.config.reconnect_base_delay * (2 ** (self._reconnect_attempts - 1))

        logger.info(
            f"Reconnect attempt {self._reconnect_attempts}/"
            f"{self.config.max_reconnect_attempts} after {delay:.1f}s"
        )

        await asyncio.sleep(delay)

        continuation_prompt = (
            f"Continue from where you left off. Original: {prompt}\n\n"
            f"Partial response:\n{self._checkpoint.accumulated_content}\n\n"
            "Continue without repeating:"
        )

        if not self.is_initialized:
            await self.initialize()

        try:
            return self._base_streamer.stream(continuation_prompt, system_prompt, context, tools)
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            return None

    async def stream_with_resilience(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream with production-grade resilience features.

        Includes heartbeat, backpressure queue, and auto-reconnect.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation history
            tools: Available tools

        Yields:
            Response chunks
        """
        if not self.is_initialized:
            yield "❌ Streamer not initialized"
            return

        self._stream_active = True
        self._checkpoint = StreamCheckpoint()
        self._reconnect_attempts = 0
        self._producer_exception = None
        self._last_activity_time = time.time()

        self._chunk_queue = asyncio.Queue(maxsize=self.config.backpressure_queue_size)

        try:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._heartbeat_task.add_done_callback(self._handle_task_exception)
            self._producer_task = asyncio.create_task(
                self._producer_loop(prompt, system_prompt, context, tools)
            )
            self._producer_task.add_done_callback(self._handle_task_exception)

            async for chunk in self._consumer_loop():
                yield chunk

            if self._producer_exception:
                error = self._producer_exception
                logger.warning(f"Stream error, attempting reconnect: {error}")

                reconnect_stream = await self._try_reconnect(prompt, system_prompt, context, tools)
                if reconnect_stream:
                    async for chunk in reconnect_stream:
                        yield chunk
                else:
                    yield f"\n⚠️ Stream interrupted: {str(error)[:100]}"

        except asyncio.CancelledError:
            logger.info("Stream cancelled by user")
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"\n❌ Error: {str(e)[:100]}"
        finally:
            await self._cleanup()

    def _handle_task_exception(self, task: asyncio.Task) -> None:
        """Handle exceptions from background tasks.

        Args:
            task: The completed task to check for exceptions
        """
        if task.cancelled():
            return
        try:
            exc = task.exception()
            if exc:
                logger.error(f"Background task '{task.get_name()}' failed: {exc}", exc_info=exc)
        except asyncio.InvalidStateError:
            pass  # Task not done yet

    async def _cleanup(self) -> None:
        """Clean up resources after streaming."""
        self._stream_active = False

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except (asyncio.CancelledError, Exception) as e:
                if not isinstance(e, asyncio.CancelledError):
                    logger.debug(f"Heartbeat cleanup exception: {e}")

        if self._producer_task and not self._producer_task.done():
            self._producer_task.cancel()
            try:
                await self._producer_task
            except (asyncio.CancelledError, Exception) as e:
                if not isinstance(e, asyncio.CancelledError):
                    logger.debug(f"Producer cleanup exception: {e}")

        self._chunk_queue = None

    def get_checkpoint(self) -> StreamCheckpoint:
        """Get current checkpoint for external monitoring.

        Returns:
            Current checkpoint state
        """
        return self._checkpoint

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics.

        Returns:
            Dictionary with streaming stats
        """
        return {
            "initialized": self._initialized,
            "stream_active": self._stream_active,
            "checkpoint_chunks": self._checkpoint.chunk_count,
            "checkpoint_chars": len(self._checkpoint.accumulated_content),
            "reconnect_attempts": self._reconnect_attempts,
            "last_activity": self._last_activity_time,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "StreamCheckpoint",
    "ProductionGeminiStreamer",
]
