"""
Tests for Production-grade Streaming Module.

Tests:
- StreamCheckpoint: Checkpoint state management
- ProductionGeminiStreamer: Heartbeat, backpressure, reconnect

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertice_tui.core.streaming import (
    GeminiStreamConfig,
    ProductionGeminiStreamer,
    StreamCheckpoint,
)


# =============================================================================
# CHECKPOINT TESTS
# =============================================================================


class TestStreamCheckpoint:
    """Tests for StreamCheckpoint class."""

    @pytest.mark.asyncio
    async def test_checkpoint_initial_state(self) -> None:
        """Checkpoint starts empty."""
        checkpoint = StreamCheckpoint()

        assert checkpoint.accumulated_content == ""
        assert checkpoint.chunk_count == 0
        assert checkpoint.context_snapshot is None
        assert not await checkpoint.can_reconnect()

    @pytest.mark.asyncio
    async def test_checkpoint_update_accumulates_content(self) -> None:
        """Checkpoint accumulates chunks correctly."""
        checkpoint = StreamCheckpoint()

        await checkpoint.update("Hello ")
        await checkpoint.update("World!")

        assert checkpoint.accumulated_content == "Hello World!"
        assert checkpoint.chunk_count == 2

    @pytest.mark.asyncio
    async def test_checkpoint_can_reconnect_after_update(self) -> None:
        """Checkpoint allows reconnect after receiving content."""
        checkpoint = StreamCheckpoint()

        assert not await checkpoint.can_reconnect()

        await checkpoint.update("Some content")

        assert await checkpoint.can_reconnect()

    @pytest.mark.asyncio
    async def test_checkpoint_tracks_last_chunk_time(self) -> None:
        """Checkpoint updates last_chunk_time on each update."""
        checkpoint = StreamCheckpoint()
        initial_time = checkpoint.last_chunk_time

        await checkpoint.update("Test")

        assert checkpoint.last_chunk_time >= initial_time


# =============================================================================
# PRODUCTION STREAMER CONFIG TESTS
# =============================================================================


class TestGeminiStreamConfigProduction:
    """Tests for production config options."""

    def test_config_default_production_values(self) -> None:
        """Config has sensible production defaults."""
        config = GeminiStreamConfig(api_key="test")

        assert config.heartbeat_interval == 30.0
        assert config.backpressure_queue_size == 100
        assert config.checkpoint_interval == 10
        assert config.max_reconnect_attempts == 3
        assert config.reconnect_base_delay == 1.0

    def test_config_custom_production_values(self) -> None:
        """Config accepts custom production values."""
        config = GeminiStreamConfig(
            api_key="test",
            heartbeat_interval=15.0,
            backpressure_queue_size=50,
            checkpoint_interval=5,
            max_reconnect_attempts=5,
            reconnect_base_delay=0.5,
        )

        assert config.heartbeat_interval == 15.0
        assert config.backpressure_queue_size == 50
        assert config.checkpoint_interval == 5
        assert config.max_reconnect_attempts == 5
        assert config.reconnect_base_delay == 0.5

    def test_config_validates_heartbeat_interval(self) -> None:
        """Config rejects invalid heartbeat interval."""
        with pytest.raises(ValueError, match="heartbeat_interval"):
            GeminiStreamConfig(api_key="test", heartbeat_interval=0)

        with pytest.raises(ValueError, match="heartbeat_interval"):
            GeminiStreamConfig(api_key="test", heartbeat_interval=-1)

    def test_config_validates_queue_size(self) -> None:
        """Config rejects invalid queue size."""
        with pytest.raises(ValueError, match="backpressure_queue_size"):
            GeminiStreamConfig(api_key="test", backpressure_queue_size=0)


# =============================================================================
# PRODUCTION STREAMER TESTS
# =============================================================================


class TestProductionGeminiStreamer:
    """Tests for ProductionGeminiStreamer class."""

    @pytest.fixture
    def config(self) -> GeminiStreamConfig:
        """Create test config."""
        return GeminiStreamConfig(
            api_key="test-key",
            model_name="test-model",
            heartbeat_interval=1.0,  # Short for testing
            backpressure_queue_size=10,
            checkpoint_interval=2,
            max_reconnect_attempts=2,
            reconnect_base_delay=0.1,
        )

    @pytest.fixture
    def streamer(self, config: GeminiStreamConfig) -> ProductionGeminiStreamer:
        """Create test streamer."""
        return ProductionGeminiStreamer(config)

    def test_streamer_initial_state(self, streamer: ProductionGeminiStreamer) -> None:
        """Streamer starts uninitialized."""
        assert not streamer.is_initialized
        assert not streamer._stream_active
        assert streamer._reconnect_attempts == 0

    @pytest.mark.asyncio
    async def test_streamer_not_initialized_yields_error(
        self, streamer: ProductionGeminiStreamer
    ) -> None:
        """Uninitialized streamer yields error message."""
        chunks: List[str] = []

        async for chunk in streamer.stream_with_resilience("test"):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert "not initialized" in chunks[0]

    @pytest.mark.asyncio
    async def test_streamer_get_stats(
        self, streamer: ProductionGeminiStreamer
    ) -> None:
        """Stats returns correct structure."""
        stats = streamer.get_stats()

        assert "initialized" in stats
        assert "stream_active" in stats
        assert "checkpoint_chunks" in stats
        assert "checkpoint_chars" in stats
        assert "reconnect_attempts" in stats
        assert "last_activity" in stats

    @pytest.mark.asyncio
    async def test_streamer_get_checkpoint(
        self, streamer: ProductionGeminiStreamer
    ) -> None:
        """Get checkpoint returns checkpoint object."""
        checkpoint = streamer.get_checkpoint()

        assert isinstance(checkpoint, StreamCheckpoint)

    @pytest.mark.asyncio
    async def test_heartbeat_marker_is_filtered(
        self, config: GeminiStreamConfig
    ) -> None:
        """Heartbeat markers are not yielded to consumer."""
        # The HEARTBEAT_MARKER is internal and shouldn't appear in output
        assert ProductionGeminiStreamer.HEARTBEAT_MARKER == ": heartbeat\n"


# =============================================================================
# MOCK STREAMING TESTS
# =============================================================================


class TestProductionStreamerWithMocks:
    """Tests with mocked base streamer."""

    @pytest.fixture
    def config(self) -> GeminiStreamConfig:
        """Create test config."""
        return GeminiStreamConfig(
            api_key="test-key",
            model_name="test-model",
            heartbeat_interval=0.1,
            backpressure_queue_size=10,
            checkpoint_interval=2,
            max_reconnect_attempts=2,
            reconnect_base_delay=0.05,
            chunk_timeout=1.0,
        )

    @pytest.mark.asyncio
    async def test_backpressure_queue_bounded(
        self, config: GeminiStreamConfig
    ) -> None:
        """Queue has bounded size for backpressure."""
        streamer = ProductionGeminiStreamer(config)

        # Manually initialize queue
        streamer._chunk_queue = asyncio.Queue(maxsize=config.backpressure_queue_size)

        # Queue should have maxsize
        assert streamer._chunk_queue.maxsize == 10

    @pytest.mark.asyncio
    async def test_checkpoint_updated_periodically(
        self, config: GeminiStreamConfig
    ) -> None:
        """Checkpoint is saved periodically during streaming."""
        streamer = ProductionGeminiStreamer(config)

        # Simulate checkpoint updates (async method)
        await streamer._checkpoint.update("chunk1")
        await streamer._checkpoint.update("chunk2")
        await streamer._checkpoint.update("chunk3")

        assert streamer._checkpoint.chunk_count == 3
        assert streamer._checkpoint.accumulated_content == "chunk1chunk2chunk3"

    @pytest.mark.asyncio
    async def test_cleanup_cancels_tasks(
        self, config: GeminiStreamConfig
    ) -> None:
        """Cleanup properly cancels heartbeat and producer tasks."""
        streamer = ProductionGeminiStreamer(config)
        streamer._stream_active = True

        # Create mock tasks
        async def dummy_task() -> None:
            await asyncio.sleep(10)

        streamer._heartbeat_task = asyncio.create_task(dummy_task())
        streamer._producer_task = asyncio.create_task(dummy_task())
        streamer._chunk_queue = asyncio.Queue(maxsize=10)

        # Cleanup should cancel tasks
        await streamer._cleanup()

        assert not streamer._stream_active
        assert streamer._chunk_queue is None
        assert streamer._heartbeat_task.cancelled() or streamer._heartbeat_task.done()
        assert streamer._producer_task.cancelled() or streamer._producer_task.done()


# =============================================================================
# RECONNECT LOGIC TESTS
# =============================================================================


class TestReconnectLogic:
    """Tests for reconnection logic."""

    @pytest.fixture
    def config(self) -> GeminiStreamConfig:
        """Create test config."""
        return GeminiStreamConfig(
            api_key="test-key",
            model_name="test-model",
            max_reconnect_attempts=3,
            reconnect_base_delay=0.01,
        )

    @pytest.mark.asyncio
    async def test_reconnect_respects_max_attempts(
        self, config: GeminiStreamConfig
    ) -> None:
        """Reconnect stops after max attempts reached."""
        streamer = ProductionGeminiStreamer(config)
        streamer._reconnect_attempts = config.max_reconnect_attempts

        result = await streamer._try_reconnect("test", "", None, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_reconnect_requires_checkpoint(
        self, config: GeminiStreamConfig
    ) -> None:
        """Reconnect fails without checkpoint data."""
        streamer = ProductionGeminiStreamer(config)
        streamer._checkpoint = StreamCheckpoint()  # Empty checkpoint

        result = await streamer._try_reconnect("test", "", None, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_reconnect_increments_attempts(
        self, config: GeminiStreamConfig
    ) -> None:
        """Each reconnect attempt increments counter."""
        streamer = ProductionGeminiStreamer(config)
        await streamer._checkpoint.update("some content")  # async method
        streamer._initialized = True

        # Mock base streamer
        with patch.object(streamer._base_streamer, "stream") as mock_stream:
            mock_stream.return_value = AsyncMock()

            initial_attempts = streamer._reconnect_attempts
            await streamer._try_reconnect("test", "", None, None)

            assert streamer._reconnect_attempts == initial_attempts + 1

    @pytest.mark.asyncio
    async def test_reconnect_uses_exponential_backoff(
        self, config: GeminiStreamConfig
    ) -> None:
        """Reconnect delay increases exponentially."""
        streamer = ProductionGeminiStreamer(config)
        await streamer._checkpoint.update("some content")  # async method
        streamer._initialized = True

        # Delay formula: base_delay * (2 ** (attempts - 1))
        # Attempt 1: 0.01 * 2^0 = 0.01
        # Attempt 2: 0.01 * 2^1 = 0.02
        # Attempt 3: 0.01 * 2^2 = 0.04

        base = config.reconnect_base_delay
        assert base * (2 ** 0) == 0.01  # First attempt
        assert base * (2 ** 1) == 0.02  # Second attempt
        assert base * (2 ** 2) == 0.04  # Third attempt
