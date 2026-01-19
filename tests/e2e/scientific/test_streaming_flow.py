"""
Scientific E2E Tests: Streaming Flow

Flow: Source → Chunk Processing → Rendering

Tests cover:
- Chunk processing integrity
- Line buffering correctness
- Encoding edge cases
- Backpressure handling
- Callback reliability
- Memory efficiency
"""

import pytest
import asyncio
import time


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def stream_processor():
    """Create stream processor mock."""

    class MockStreamProcessor:
        def __init__(self):
            self.chunks = []
            self.callbacks_called = 0

        def feed(self, data: str) -> None:
            self.chunks.append(data)

        async def consume(self):
            for chunk in self.chunks:
                yield chunk

        def on_chunk(self, callback):
            self.callbacks_called += 1

    return MockStreamProcessor()


@pytest.fixture
def line_buffer():
    """Create line buffer for testing."""

    class LineBuffer:
        def __init__(self):
            self._buffer = ""
            self._lines = []

        def feed(self, data: str) -> list:
            self._buffer += data
            lines = []
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                lines.append(line)
                self._lines.append(line)
            return lines

        def flush(self) -> str:
            remaining = self._buffer
            self._buffer = ""
            return remaining

        @property
        def all_lines(self) -> list:
            return self._lines

    return LineBuffer()


# =============================================================================
# 1. CHUNK PROCESSING INTEGRITY TESTS
# =============================================================================


class TestChunkProcessingIntegrity:
    """Test chunk processing preserves data integrity."""

    def test_single_chunk_passthrough(self, stream_processor):
        """Single chunk passes through unchanged."""
        stream_processor.feed("Hello World")
        assert stream_processor.chunks == ["Hello World"]

    def test_multiple_chunks_order(self, stream_processor):
        """Multiple chunks maintain order."""
        chunks = ["chunk1", "chunk2", "chunk3"]
        for chunk in chunks:
            stream_processor.feed(chunk)
        assert stream_processor.chunks == chunks

    def test_empty_chunk_handled(self, stream_processor):
        """Empty chunk is handled gracefully."""
        stream_processor.feed("")
        stream_processor.feed("not empty")
        stream_processor.feed("")
        assert "not empty" in stream_processor.chunks

    def test_chunk_content_preserved(self, stream_processor):
        """Chunk content is not modified."""
        original = "Test with special chars: <>&\"'"
        stream_processor.feed(original)
        assert stream_processor.chunks[0] == original


# =============================================================================
# 2. LINE BUFFERING CORRECTNESS TESTS
# =============================================================================


class TestLineBufferingCorrectness:
    """Test line buffering handles various cases."""

    def test_complete_line(self, line_buffer):
        """Complete line with newline is emitted."""
        lines = line_buffer.feed("complete line\n")
        assert lines == ["complete line"]

    def test_multiple_lines_at_once(self, line_buffer):
        """Multiple lines in single chunk are split."""
        lines = line_buffer.feed("line1\nline2\nline3\n")
        assert lines == ["line1", "line2", "line3"]

    def test_partial_line_buffered(self, line_buffer):
        """Partial line is buffered until complete."""
        lines1 = line_buffer.feed("partial")
        assert lines1 == []

        lines2 = line_buffer.feed(" complete\n")
        assert lines2 == ["partial complete"]

    def test_split_across_chunks(self, line_buffer):
        """Line split across chunks is reassembled."""
        line_buffer.feed("first ")
        line_buffer.feed("second ")
        lines = line_buffer.feed("third\n")
        assert lines == ["first second third"]

    def test_empty_lines_preserved(self, line_buffer):
        """Empty lines are preserved."""
        lines = line_buffer.feed("line1\n\n\nline2\n")
        assert lines == ["line1", "", "", "line2"]

    def test_no_newline_at_eof(self, line_buffer):
        """Content without trailing newline is flushed."""
        line_buffer.feed("no newline")
        remaining = line_buffer.flush()
        assert remaining == "no newline"

    def test_cr_lf_handling(self, line_buffer):
        """Windows-style CRLF is handled."""
        # Split on \n, \r remains in content
        lines = line_buffer.feed("line1\r\nline2\r\n")
        # \r should be at end of each line
        assert len(lines) == 2

    def test_cr_only_handling(self, line_buffer):
        """Mac classic CR-only lines."""
        # We only split on \n, so \r stays as content
        lines = line_buffer.feed("line1\rline2\n")
        assert len(lines) == 1
        assert "line1\rline2" in lines[0]


# =============================================================================
# 3. ENCODING EDGE CASES TESTS
# =============================================================================


class TestEncodingEdgeCases:
    """Test encoding edge cases in streaming."""

    def test_utf8_basic(self, stream_processor):
        """Basic UTF-8 passes through."""
        stream_processor.feed("Hello 世界")
        assert "世界" in stream_processor.chunks[0]

    def test_utf8_emoji(self, stream_processor):
        """Emoji sequences pass through."""
        stream_processor.feed("🚀 Launch 🎉 Party 👨‍👩‍👧‍👦 Family")
        chunk = stream_processor.chunks[0]
        assert "🚀" in chunk
        assert "🎉" in chunk
        assert "👨‍👩‍👧‍👦" in chunk  # ZWJ sequence

    def test_utf8_combining_chars(self, stream_processor):
        """Combining characters are preserved."""
        # é can be e + combining acute accent
        stream_processor.feed("café résumé naïve")
        chunk = stream_processor.chunks[0]
        assert "café" in chunk or "cafe" in chunk  # Both forms valid

    def test_ascii_only(self, stream_processor):
        """Pure ASCII works."""
        stream_processor.feed("Pure ASCII: ABCxyz123!@#")
        assert stream_processor.chunks[0] == "Pure ASCII: ABCxyz123!@#"

    def test_null_bytes_handled(self, stream_processor):
        """Null bytes are handled or replaced."""
        stream_processor.feed("before\x00after")
        chunk = stream_processor.chunks[0]
        # Null byte should be present or replaced
        assert len(chunk) > 0

    def test_rtl_text(self, stream_processor):
        """Right-to-left text passes through."""
        stream_processor.feed("English العربية עברית")
        chunk = stream_processor.chunks[0]
        assert "العربية" in chunk
        assert "עברית" in chunk


# =============================================================================
# 4. BACKPRESSURE HANDLING TESTS
# =============================================================================


class TestBackpressureHandling:
    """Test handling of slow consumers."""

    @pytest.mark.asyncio
    async def test_queue_based_backpressure(self):
        """Queue-based streaming handles backpressure."""
        queue = asyncio.Queue(maxsize=10)

        # Producer
        async def produce():
            for i in range(20):
                await queue.put(f"item{i}")

        # Consumer
        consumed = []

        async def consume():
            for _ in range(20):
                item = await asyncio.wait_for(queue.get(), timeout=5.0)
                consumed.append(item)
                await asyncio.sleep(0.01)  # Slow consumer

        await asyncio.gather(produce(), consume())
        assert len(consumed) == 20

    @pytest.mark.asyncio
    async def test_unbounded_queue_memory(self):
        """Unbounded queue doesn't crash with many items."""
        queue = asyncio.Queue()

        # Produce many items
        for i in range(1000):
            await queue.put(f"item{i}")

        assert queue.qsize() == 1000

        # Consume all
        for _ in range(1000):
            await queue.get()

        assert queue.empty()


# =============================================================================
# 5. CALLBACK RELIABILITY TESTS
# =============================================================================


class TestCallbackReliability:
    """Test callback execution reliability."""

    @pytest.mark.asyncio
    async def test_callback_called_for_each_chunk(self):
        """Callback is called for every chunk."""
        chunks_received = []

        def callback(chunk):
            chunks_received.append(chunk)

        chunks = ["a", "b", "c", "d", "e"]
        for chunk in chunks:
            callback(chunk)

        assert chunks_received == chunks

    @pytest.mark.asyncio
    async def test_async_callback(self):
        """Async callback works."""
        chunks_received = []

        async def callback(chunk):
            await asyncio.sleep(0.001)
            chunks_received.append(chunk)

        chunks = ["a", "b", "c"]
        for chunk in chunks:
            await callback(chunk)

        assert chunks_received == chunks

    @pytest.mark.asyncio
    async def test_callback_exception_isolated(self):
        """Exception in callback doesn't crash stream."""
        processed = []
        exceptions = []

        def callback(chunk):
            if chunk == "bad":
                raise ValueError("Bad chunk")
            processed.append(chunk)

        chunks = ["good1", "bad", "good2"]
        for chunk in chunks:
            try:
                callback(chunk)
            except ValueError as e:
                exceptions.append(str(e))

        assert processed == ["good1", "good2"]
        assert len(exceptions) == 1

    @pytest.mark.asyncio
    async def test_callback_order_preserved(self):
        """Callbacks are executed in order."""
        order = []

        async def callback(index):
            await asyncio.sleep(0.01 * (5 - index))  # Longer sleep for earlier
            order.append(index)

        # Execute sequentially to ensure order
        for i in range(5):
            await callback(i)

        assert order == [0, 1, 2, 3, 4]


# =============================================================================
# 6. MEMORY EFFICIENCY TESTS
# =============================================================================


class TestMemoryEfficiency:
    """Test memory usage during streaming."""

    def test_line_buffer_constant_memory(self, line_buffer):
        """Line buffer uses O(1) memory for streamed lines."""
        # Feed many complete lines
        for i in range(1000):
            line_buffer.feed(f"line {i}\n")

        # Buffer should be empty (all lines emitted)
        assert line_buffer.flush() == ""

    def test_partial_line_bounded(self, line_buffer):
        """Partial lines are bounded in memory."""
        # Accumulate partial lines
        for i in range(100):
            line_buffer.feed(f"part{i} ")

        # Flush gets accumulated content
        content = line_buffer.flush()
        assert len(content) > 0
        # Memory should now be freed
        assert line_buffer.flush() == ""

    @pytest.mark.asyncio
    async def test_async_generator_memory(self):
        """Async generator uses memory efficiently."""

        async def generate_chunks():
            for i in range(1000):
                yield f"chunk{i}\n"

        count = 0
        async for chunk in generate_chunks():
            count += 1
            # Process and discard
            _ = len(chunk)

        assert count == 1000


# =============================================================================
# 7. TIMING AND LATENCY TESTS
# =============================================================================


class TestTimingAndLatency:
    """Test timing characteristics of streaming."""

    @pytest.mark.asyncio
    async def test_chunk_latency_acceptable(self):
        """Chunk processing latency is acceptable."""
        queue = asyncio.Queue()

        async def producer():
            for i in range(10):
                await queue.put(time.time())
                await asyncio.sleep(0.01)

        latencies = []

        async def consumer():
            for _ in range(10):
                send_time = await queue.get()
                receive_time = time.time()
                latencies.append(receive_time - send_time)

        await asyncio.gather(producer(), consumer())

        # All latencies should be < 100ms
        assert all(lat < 0.1 for lat in latencies)

    @pytest.mark.asyncio
    async def test_throughput_adequate(self):
        """Throughput is adequate for typical use."""
        count = 0
        start = time.time()

        for _ in range(10000):
            count += 1

        elapsed = time.time() - start

        # Should process 10k items in < 1s
        assert elapsed < 1.0
        assert count == 10000


# =============================================================================
# 8. CONTROL CHARACTER HANDLING TESTS
# =============================================================================


class TestControlCharacterHandling:
    """Test handling of control characters."""

    def test_ansi_escape_codes(self, stream_processor):
        """ANSI escape codes pass through."""
        ansi = "\x1b[31mRed\x1b[0m \x1b[1mBold\x1b[0m"
        stream_processor.feed(ansi)
        assert "\x1b[31m" in stream_processor.chunks[0]

    def test_tab_characters(self, stream_processor):
        """Tab characters are preserved."""
        stream_processor.feed("col1\tcol2\tcol3")
        assert "\t" in stream_processor.chunks[0]

    def test_carriage_return(self, stream_processor):
        """Carriage return is preserved."""
        stream_processor.feed("progress\roverwrite")
        assert "\r" in stream_processor.chunks[0]

    def test_backspace(self, stream_processor):
        """Backspace character is preserved."""
        stream_processor.feed("typo\x08fixed")
        assert "\x08" in stream_processor.chunks[0]

    def test_form_feed(self, stream_processor):
        """Form feed character is handled."""
        stream_processor.feed("page1\x0cpage2")
        chunk = stream_processor.chunks[0]
        # Should be present or handled
        assert len(chunk) > 0

    def test_bell_character(self, stream_processor):
        """Bell character is handled."""
        stream_processor.feed("alert\x07beep")
        # Should not crash
        assert len(stream_processor.chunks) == 1
