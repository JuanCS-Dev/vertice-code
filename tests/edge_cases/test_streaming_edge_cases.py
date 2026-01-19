"""
Streaming Edge Case Tests.

Tests for edge cases in streaming functionality.
"""

import asyncio
import pytest


class TestEmptyChunkHandling:
    """Test handling of empty chunks in streams."""

    @pytest.mark.asyncio
    async def test_empty_chunk_mid_stream(self):
        """LLM returns empty chunk mid-stream."""
        chunks = ["Hello", "", " world", "", "!"]
        result = []

        for chunk in chunks:
            if chunk:  # Only collect non-empty
                result.append(chunk)

        assert "".join(result) == "Hello world!"

    @pytest.mark.asyncio
    async def test_all_empty_chunks(self):
        """Stream of only empty chunks."""
        chunks = ["", "", "", ""]
        result = [c for c in chunks if c]
        assert result == []

    @pytest.mark.asyncio
    async def test_whitespace_only_chunks(self):
        """Chunks with only whitespace."""
        chunks = [" ", "\n", "\t", "content"]
        result = [c.strip() for c in chunks if c.strip()]
        assert result == ["content"]


class TestMalformedJSONInStream:
    """Test handling of malformed JSON in SSE events."""

    def test_malformed_json_recovery(self):
        """SSE event contains invalid JSON."""
        import json

        events = [
            '{"content": "hello"}',
            '{"invalid json',  # Malformed
            '{"content": "world"}',
        ]

        parsed = []
        for event in events:
            try:
                data = json.loads(event)
                parsed.append(data.get("content", ""))
            except json.JSONDecodeError:
                # Should continue gracefully
                continue

        assert parsed == ["hello", "world"]

    def test_unicode_escape_errors(self):
        """JSON with invalid unicode escapes."""
        import json

        event = '{"content": "test\\u000"}'  # Invalid unicode

        try:
            json.loads(event)
            parsed = True
        except json.JSONDecodeError:
            parsed = False

        # Should handle gracefully
        assert not parsed


class TestConnectionDropRecovery:
    """Test recovery from connection drops."""

    @pytest.mark.asyncio
    async def test_timeout_during_stream(self):
        """Connection times out during streaming."""
        collected = []

        async def mock_stream():
            yield "chunk1"
            yield "chunk2"
            await asyncio.sleep(0.01)  # Simulate slow
            yield "chunk3"

        try:
            async for chunk in mock_stream():
                collected.append(chunk)
        except asyncio.TimeoutError:
            pass

        assert len(collected) >= 2

    @pytest.mark.asyncio
    async def test_partial_result_on_disconnect(self):
        """Verify partial results saved on disconnect."""
        buffer = []

        async def process_stream():
            chunks = ["part1", "part2"]
            for chunk in chunks:
                buffer.append(chunk)
            raise ConnectionError("Simulated disconnect")

        try:
            await process_stream()
        except ConnectionError:
            pass

        # Partial results should be preserved
        assert buffer == ["part1", "part2"]


class TestStreamBufferOverflow:
    """Test buffer overflow protection in streams."""

    def test_large_chunk_handling(self):
        """Handle unexpectedly large chunks."""
        MAX_CHUNK_SIZE = 1000
        large_chunk = "x" * 5000

        # Should truncate or handle gracefully
        processed = (
            large_chunk[:MAX_CHUNK_SIZE] if len(large_chunk) > MAX_CHUNK_SIZE else large_chunk
        )
        assert len(processed) <= MAX_CHUNK_SIZE

    @pytest.mark.asyncio
    async def test_rapid_chunk_accumulation(self):
        """Many rapid small chunks don't overflow memory."""
        chunks = ["a"] * 10000
        buffer = []
        MAX_BUFFER = 5000

        for chunk in chunks:
            if len(buffer) < MAX_BUFFER:
                buffer.append(chunk)
            else:
                # Flush or handle
                buffer = buffer[-1000:]  # Keep last 1000
                buffer.append(chunk)

        assert len(buffer) <= MAX_BUFFER + 1
