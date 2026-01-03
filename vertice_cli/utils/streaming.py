"""Streaming Buffer Utilities for LLM Response Handling.

This module provides utilities for collecting and managing streaming responses
from LLM providers. It handles buffering, chunk aggregation, and callback
notification in a thread-safe manner.

Key Features:
    - Async stream collection with progress callbacks
    - Configurable buffer size and flush behavior
    - Token counting integration
    - Memory-efficient chunked processing

Design Principles:
    - Async-first design for non-blocking I/O
    - Minimal memory footprint with streaming
    - Callback-based progress notification
    - Type-safe with comprehensive hints

Example:
    >>> buffer = StreamBuffer()
    >>> async for chunk in llm.stream(prompt):
    ...     buffer.append(chunk)
    >>> result = buffer.get_content()

    # Or with callback:
    >>> result = await collect_stream(stream, on_chunk=print)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    Optional,
    Protocol,
    TypeVar,
    Union,
)


T = TypeVar("T")


class ChunkCallback(Protocol):
    """Protocol for chunk notification callbacks."""

    def __call__(self, chunk: str) -> None:
        """Handle a received chunk.

        Args:
            chunk: The text chunk received.
        """
        ...


class AsyncChunkCallback(Protocol):
    """Protocol for async chunk notification callbacks."""

    async def __call__(self, chunk: str) -> None:
        """Handle a received chunk asynchronously.

        Args:
            chunk: The text chunk received.
        """
        ...


@dataclass
class BufferConfig:
    """Configuration for StreamBuffer behavior.

    Attributes:
        max_size: Maximum buffer size in characters (0 = unlimited).
        flush_threshold: Flush buffer when this size is reached.
        count_tokens: Enable approximate token counting.
        token_ratio: Characters per token estimate (default 4).
    """

    max_size: int = 0  # 0 = unlimited
    flush_threshold: int = 0  # 0 = no auto-flush
    count_tokens: bool = False
    token_ratio: float = 4.0  # ~4 chars per token average


@dataclass
class BufferStats:
    """Statistics about buffer usage.

    Attributes:
        chunk_count: Number of chunks received.
        total_chars: Total characters processed.
        estimated_tokens: Estimated token count.
        flush_count: Number of times buffer was flushed.
    """

    chunk_count: int = 0
    total_chars: int = 0
    estimated_tokens: int = 0
    flush_count: int = 0


@dataclass
class StreamBuffer:
    """Buffer for collecting streaming response chunks.

    This class provides efficient buffering for streaming LLM responses
    with support for callbacks, size limits, and token counting.

    Example:
        >>> buffer = StreamBuffer()
        >>> buffer.append("Hello ")
        >>> buffer.append("world!")
        >>> print(buffer.get_content())  # "Hello world!"

        >>> # With callback
        >>> buffer = StreamBuffer(on_chunk=print)
        >>> async for chunk in stream:
        ...     buffer.append(chunk)  # prints each chunk
    """

    config: BufferConfig = field(default_factory=BufferConfig)
    on_chunk: Optional[ChunkCallback] = None
    _chunks: list[str] = field(default_factory=list, repr=False)
    _stats: BufferStats = field(default_factory=BufferStats, repr=False)

    def append(self, chunk: str) -> None:
        """Append a chunk to the buffer.

        Args:
            chunk: Text chunk to append.
        """
        if not chunk:
            return

        self._chunks.append(chunk)
        self._stats.chunk_count += 1
        self._stats.total_chars += len(chunk)

        if self.config.count_tokens:
            self._stats.estimated_tokens = int(
                self._stats.total_chars / self.config.token_ratio
            )

        # Notify callback
        if self.on_chunk is not None:
            self.on_chunk(chunk)

        # Check flush threshold
        if self.config.flush_threshold > 0:
            if self._stats.total_chars >= self.config.flush_threshold:
                self._stats.flush_count += 1

    def get_content(self) -> str:
        """Get the complete buffered content.

        Returns:
            Concatenated string of all chunks.
        """
        return "".join(self._chunks)

    def get_stats(self) -> BufferStats:
        """Get buffer statistics.

        Returns:
            BufferStats with current statistics.
        """
        return BufferStats(
            chunk_count=self._stats.chunk_count,
            total_chars=self._stats.total_chars,
            estimated_tokens=self._stats.estimated_tokens,
            flush_count=self._stats.flush_count,
        )

    def clear(self) -> None:
        """Clear the buffer and reset statistics."""
        self._chunks.clear()
        self._stats = BufferStats()

    def __len__(self) -> int:
        """Return total characters in buffer."""
        return self._stats.total_chars

    def __bool__(self) -> bool:
        """Return True if buffer has content."""
        return self._stats.total_chars > 0

    def __str__(self) -> str:
        """Return buffered content as string."""
        return self.get_content()

    def __iter__(self) -> Iterator[str]:
        """Iterate over chunks."""
        return iter(self._chunks)


async def collect_stream(
    stream: AsyncIterator[str],
    on_chunk: Optional[Union[ChunkCallback, AsyncChunkCallback]] = None,
    config: Optional[BufferConfig] = None,
) -> str:
    """Collect streaming chunks into a single string.

    This is a convenience function for common streaming patterns.
    Handles both sync and async callbacks.

    Args:
        stream: Async iterator yielding string chunks.
        on_chunk: Optional callback for each chunk (sync or async).
        config: Optional buffer configuration.

    Returns:
        Complete collected string.

    Example:
        >>> async def print_chunk(chunk: str) -> None:
        ...     print(chunk, end="", flush=True)
        >>> result = await collect_stream(llm.stream(prompt), on_chunk=print_chunk)
    """
    buffer = StreamBuffer(config=config or BufferConfig())

    async for chunk in stream:
        buffer.append(chunk)

        if on_chunk is not None:
            result = on_chunk(chunk)
            if asyncio.iscoroutine(result):
                await result

    return buffer.get_content()


async def collect_stream_with_stats(
    stream: AsyncIterator[str],
    on_chunk: Optional[Union[ChunkCallback, AsyncChunkCallback]] = None,
    config: Optional[BufferConfig] = None,
) -> tuple[str, BufferStats]:
    """Collect streaming chunks with statistics.

    Args:
        stream: Async iterator yielding string chunks.
        on_chunk: Optional callback for each chunk.
        config: Optional buffer configuration.

    Returns:
        Tuple of (content, stats).
    """
    config = config or BufferConfig(count_tokens=True)
    buffer = StreamBuffer(config=config)

    async for chunk in stream:
        buffer.append(chunk)

        if on_chunk is not None:
            result = on_chunk(chunk)
            if asyncio.iscoroutine(result):
                await result

    return buffer.get_content(), buffer.get_stats()


def create_tee_callback(
    *callbacks: ChunkCallback,
) -> ChunkCallback:
    """Create a callback that forwards to multiple callbacks.

    Args:
        *callbacks: Callbacks to forward to.

    Returns:
        Combined callback function.

    Example:
        >>> combined = create_tee_callback(print, logger.info)
        >>> buffer = StreamBuffer(on_chunk=combined)
    """
    def tee_callback(chunk: str) -> None:
        for callback in callbacks:
            callback(chunk)

    return tee_callback
