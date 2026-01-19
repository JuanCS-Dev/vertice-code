"""
Tests for MAXIMUS Client (TUI Integration).

Scientific tests for MaximusClient streaming and operations.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from vertice_tui.core.maximus_client import MaximusClient, MaximusStreamConfig


class TestMaximusClientInit:
    """Test MaximusClient initialization."""

    def test_client_creation_with_defaults(self):
        """HYPOTHESIS: Client initializes with default config."""
        client = MaximusClient()
        assert client.config is not None
        assert client.config.enable_tribunal is True
        assert client.config.enable_memory is True
        assert client._initialized is False

    def test_client_creation_with_custom_config(self):
        """HYPOTHESIS: Client accepts custom config."""
        config = MaximusStreamConfig(
            enable_tribunal=False,
            temperature=0.5,
        )
        client = MaximusClient(config=config)
        assert client.config.enable_tribunal is False
        assert client.config.temperature == 0.5

    def test_client_with_tools(self):
        """HYPOTHESIS: Client accepts initial tools."""
        tools = [{"name": "test_tool", "description": "A test"}]
        client = MaximusClient(tools=tools)
        assert len(client._tools) == 1


class TestMaximusClientHealth:
    """Test health status functionality."""

    def test_get_health_status_not_initialized(self):
        """HYPOTHESIS: Health status shows not initialized."""
        client = MaximusClient()
        status = client.get_health_status()

        assert status["provider"] == "maximus"
        assert status["initialized"] is False
        assert status["total_requests"] == 0

    def test_get_health_status_initialized(self):
        """HYPOTHESIS: Health status shows initialized with metrics."""
        client = MaximusClient()
        client._initialized = True
        client._total_requests = 10
        client._avg_response_time = 1.5

        status = client.get_health_status()

        assert status["initialized"] is True
        assert status["total_requests"] == 10
        assert status["avg_response_time"] == 1.5


class TestMaximusClientTribunal:
    """Test Tribunal operations via client."""

    @pytest.mark.asyncio
    async def test_evaluate_in_tribunal(self):
        """HYPOTHESIS: evaluate_in_tribunal calls provider."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.tribunal_evaluate.return_value = {
            "decision": "PASS",
            "consensus_score": 0.9,
        }

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.evaluate_in_tribunal("test log")

            assert result["decision"] == "PASS"
            assert len(client._tribunal_verdicts) == 1

    @pytest.mark.asyncio
    async def test_get_tribunal_health(self):
        """HYPOTHESIS: get_tribunal_health returns status."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.tribunal_health.return_value = {"status": "healthy"}

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.get_tribunal_health()

            assert result["status"] == "healthy"


class TestMaximusClientMemory:
    """Test Memory operations via client."""

    @pytest.mark.asyncio
    async def test_store_memory(self):
        """HYPOTHESIS: store_memory saves to backend."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.memory_store.return_value = {"id": "mem_123"}

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.store_memory(
                content="Test",
                memory_type="episodic",
            )

            assert result["id"] == "mem_123"

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """HYPOTHESIS: search_memories finds memories."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.memory_search.return_value = [{"id": "mem_1"}]

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.search_memories("test query")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_consolidate_memories(self):
        """HYPOTHESIS: consolidate_memories moves to vault."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.memory_consolidate.return_value = {"episodic": 5}

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.consolidate_memories(threshold=0.9)

            assert result["episodic"] == 5


class TestMaximusClientFactory:
    """Test Factory operations via client."""

    @pytest.mark.asyncio
    async def test_generate_tool(self):
        """HYPOTHESIS: generate_tool creates new tool."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.factory_generate.return_value = {
            "name": "new_tool",
            "code": "def x(): pass",
        }

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.generate_tool(
                name="new_tool",
                description="A new tool",
                examples=[],
            )

            assert result["name"] == "new_tool"

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """HYPOTHESIS: list_tools returns tool list."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        mock_provider.factory_list.return_value = [
            {"name": "tool1"},
            {"name": "tool2"},
        ]

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            result = await client.list_tools()

            assert len(result) == 2


class TestMaximusClientStreaming:
    """Test streaming functionality."""

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        """HYPOTHESIS: stream yields response chunks."""
        client = MaximusClient()

        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "World"

        mock_provider = AsyncMock()
        mock_provider.stream = mock_stream

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            chunks = []
            async for chunk in client.stream("test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello ", "World"]

    @pytest.mark.asyncio
    async def test_stream_updates_metrics(self):
        """HYPOTHESIS: stream updates request count."""
        client = MaximusClient()

        async def mock_stream(*args, **kwargs):
            yield "Done"

        mock_provider = AsyncMock()
        mock_provider.stream = mock_stream

        with patch.object(client, "_ensure_provider", new_callable=AsyncMock):
            client._provider = mock_provider
            client._initialized = True

            async for _ in client.stream("test"):
                pass

            assert client._total_requests == 1


class TestMaximusClientClose:
    """Test cleanup functionality."""

    @pytest.mark.asyncio
    async def test_close_releases_resources(self):
        """HYPOTHESIS: close releases provider resources."""
        client = MaximusClient()

        mock_provider = AsyncMock()
        client._provider = mock_provider
        client._initialized = True

        await client.close()

        mock_provider.close.assert_called_once()
        assert client._provider is None
        assert client._initialized is False
