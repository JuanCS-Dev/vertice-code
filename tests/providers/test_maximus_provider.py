"""
Tests for MAXIMUS Provider Integration.

Scientific tests for MAXIMUS backend connection with resilience.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jdev_cli.core.providers.maximus_provider import MaximusProvider
from jdev_cli.core.providers.maximus_config import MaximusConfig, TransportMode


class TestMaximusProviderInit:
    """Test MaximusProvider initialization."""

    def test_provider_creation_with_defaults(self) -> None:
        """HYPOTHESIS: Provider initializes with default config."""
        provider: MaximusProvider = MaximusProvider()
        assert provider.config is not None
        assert provider.config.enable_tribunal is True
        assert provider.config.enable_memory is True
        assert provider.config.enable_factory is True

    def test_provider_creation_with_custom_config(self) -> None:
        """HYPOTHESIS: Provider accepts custom config."""
        config: MaximusConfig = MaximusConfig(
            base_url="http://custom:8200",
            enable_tribunal=False,
            timeout=60.0,
        )
        provider: MaximusProvider = MaximusProvider(config=config)
        assert provider.config.base_url == "http://custom:8200"
        assert provider.config.enable_tribunal is False
        assert provider.config.timeout == 60.0

    def test_provider_not_initialized_before_use(self) -> None:
        """HYPOTHESIS: Provider is lazy-initialized."""
        provider: MaximusProvider = MaximusProvider()
        assert provider._initialized is False
        assert provider._client is None

    def test_provider_has_circuit_breaker(self) -> None:
        """HYPOTHESIS: Provider has circuit breaker initialized."""
        provider: MaximusProvider = MaximusProvider()
        assert provider._breaker is not None
        assert not provider._breaker.is_open()


class TestMaximusProviderHealth:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_is_available_when_healthy(self) -> None:
        """HYPOTHESIS: is_available returns True when healthy."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._health_status = {"status": "ok"}

        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_when_unhealthy(self) -> None:
        """HYPOTHESIS: is_available returns False when unhealthy."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._health_status = {"status": "error"}

        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_when_not_initialized(self) -> None:
        """HYPOTHESIS: is_available returns False when not initialized."""
        provider: MaximusProvider = MaximusProvider()
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_when_circuit_open(self) -> None:
        """HYPOTHESIS: is_available returns False when circuit is open."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._health_status = {"status": "ok"}
        # Simulate circuit open by recording many failures
        for _ in range(10):
            provider._breaker.record_failure()

        assert provider.is_available() is False


class TestMaximusProviderTribunal:
    """Test Tribunal integration."""

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_success(self) -> None:
        """HYPOTHESIS: tribunal_evaluate calls correct endpoint."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "decision": "PASS",
            "consensus_score": 0.85,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_evaluate("test log")

            assert result["decision"] == "PASS"
            assert result["consensus_score"] == 0.85

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_with_context(self) -> None:
        """HYPOTHESIS: tribunal_evaluate accepts optional context."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "decision": "PASS",
            "consensus_score": 0.9,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_evaluate(
                "test log",
                context={"user_id": "123", "session": "abc"}
            )

            assert result["decision"] == "PASS"
            # Verify context was passed in the request
            call_args = mock_client.request.call_args
            assert "context" in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_tribunal_health_success(self) -> None:
        """HYPOTHESIS: tribunal_health returns status."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_health()

            assert result["status"] == "healthy"


class TestMaximusProviderMemory:
    """Test Memory integration."""

    @pytest.mark.asyncio
    async def test_memory_store_success(self) -> None:
        """HYPOTHESIS: memory_store saves memory."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "id": "mem_123",
            "content": "Test memory",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.memory_store(
                content="Test memory",
                memory_type="episodic",
                importance=0.8,
            )

            assert result["id"] == "mem_123"

    @pytest.mark.asyncio
    async def test_memory_search_success(self) -> None:
        """HYPOTHESIS: memory_search finds memories."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "memories": [
                {"id": "mem_1", "content": "First"},
                {"id": "mem_2", "content": "Second"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result = await provider.memory_search("test query")

            assert len(result) == 2
            assert result[0]["id"] == "mem_1"

    @pytest.mark.asyncio
    async def test_memory_search_with_type_filter(self) -> None:
        """HYPOTHESIS: memory_search accepts memory_type filter."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "memories": [{"id": "mem_1", "type": "episodic"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result = await provider.memory_search(
                "test query",
                memory_type="episodic",
                limit=5
            )

            assert len(result) == 1
            # Verify request was called with memory_type param
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["memory_type"] == "episodic"


class TestMaximusProviderFactory:
    """Test Factory integration."""

    @pytest.mark.asyncio
    async def test_factory_generate_success(self) -> None:
        """HYPOTHESIS: factory_generate creates tool."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "name": "test_tool",
            "code": "def test(): return 42",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.factory_generate(
                name="test_tool",
                description="A test tool",
                examples=[{"input": {}, "expected": 42}],
            )

            assert result["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_factory_list_success(self) -> None:
        """HYPOTHESIS: factory_list returns tools."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "tools": [
                {"name": "tool1"},
                {"name": "tool2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result = await provider.factory_list()

            assert len(result) == 2


class TestMaximusProviderInitialization:
    """Test initialization and health check."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_creates_client(self) -> None:
        """HYPOTHESIS: _ensure_initialized creates HTTP client."""
        provider: MaximusProvider = MaximusProvider()

        with patch(
            'jdev_cli.core.providers.maximus_provider.create_http_client'
        ) as mock_create:
            mock_client: AsyncMock = AsyncMock()
            mock_response: MagicMock = MagicMock()
            mock_response.json.return_value = {"status": "ok"}
            mock_client.get.return_value = mock_response
            mock_create.return_value = mock_client

            await provider._ensure_initialized()

            mock_create.assert_called_once()
            assert provider._initialized is True
            assert provider._client is not None

    @pytest.mark.asyncio
    async def test_ensure_initialized_only_once(self) -> None:
        """HYPOTHESIS: _ensure_initialized runs only once."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True

        with patch(
            'jdev_cli.core.providers.maximus_provider.create_http_client'
        ) as mock_create:
            await provider._ensure_initialized()

            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_health_success(self) -> None:
        """HYPOTHESIS: _check_health returns health status."""
        provider: MaximusProvider = MaximusProvider()
        mock_client: AsyncMock = AsyncMock()
        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"status": "ok", "mcp_enabled": True}
        mock_client.get.return_value = mock_response
        provider._client = mock_client

        result: Dict[str, Any] = await provider._check_health()

        assert result["status"] == "ok"
        assert provider._mcp_available is True

    @pytest.mark.asyncio
    async def test_check_health_handles_http_error(self) -> None:
        """HYPOTHESIS: _check_health handles HTTP errors."""
        import httpx
        provider: MaximusProvider = MaximusProvider()
        mock_client: AsyncMock = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        provider._client = mock_client

        result: Dict[str, Any] = await provider._check_health()

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_health_when_client_none(self) -> None:
        """HYPOTHESIS: _check_health returns not_initialized when no client."""
        provider: MaximusProvider = MaximusProvider()

        result: Dict[str, Any] = await provider._check_health()

        assert result["status"] == "not_initialized"


class TestMaximusProviderCircuitBreaker:
    """Test circuit breaker error handling."""

    @pytest.mark.asyncio
    async def test_request_returns_error_when_circuit_open(self) -> None:
        """HYPOTHESIS: _request returns error when circuit breaker is open."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        mock_client: AsyncMock = AsyncMock()
        provider._client = mock_client

        # Open the circuit
        for _ in range(10):
            provider._breaker.record_failure()

        result: Dict[str, Any] = await provider.tribunal_health()

        assert "error" in result
        assert "circuit open" in result["error"]

    @pytest.mark.asyncio
    async def test_request_handles_http_error(self) -> None:
        """HYPOTHESIS: _request handles HTTP errors gracefully."""
        import httpx
        provider: MaximusProvider = MaximusProvider()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.side_effect = httpx.HTTPError("Server error")
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_health()

            assert "error" in result


class TestMaximusProviderClose:
    """Test close functionality."""

    @pytest.mark.asyncio
    async def test_close_releases_client(self) -> None:
        """HYPOTHESIS: close() releases client and resets state."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        mock_client: AsyncMock = AsyncMock()
        provider._client = mock_client

        await provider.close()

        mock_client.aclose.assert_called_once()
        assert provider._client is None
        assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_close_handles_no_client(self) -> None:
        """HYPOTHESIS: close() handles None client gracefully."""
        provider: MaximusProvider = MaximusProvider()
        await provider.close()  # Should not raise
        assert provider._client is None


class TestMaximusProviderTribunalStats:
    """Test Tribunal stats integration."""

    @pytest.mark.asyncio
    async def test_tribunal_stats_success(self) -> None:
        """HYPOTHESIS: tribunal_stats returns statistics."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "total_evaluations": 100,
            "pass_rate": 0.95,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_stats()

            assert result["total_evaluations"] == 100
            assert result["pass_rate"] == 0.95


class TestMaximusProviderMemoryContext:
    """Test Memory context integration."""

    @pytest.mark.asyncio
    async def test_memory_context_success(self) -> None:
        """HYPOTHESIS: memory_context returns context for task."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "core": [{"id": "mem_1"}],
            "episodic": [{"id": "mem_2"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.memory_context("test task")

            assert "core" in result
            assert "episodic" in result

    @pytest.mark.asyncio
    async def test_memory_consolidate_success(self) -> None:
        """HYPOTHESIS: memory_consolidate returns counts."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "episodic": 5,
            "semantic": 3,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result = await provider.memory_consolidate(threshold=0.8)

            assert result["episodic"] == 5
            assert result["semantic"] == 3

    @pytest.mark.asyncio
    async def test_memory_consolidate_returns_empty_on_error(self) -> None:
        """HYPOTHESIS: memory_consolidate returns empty dict on error."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"error": "Service unavailable"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result = await provider.memory_consolidate()

            assert result == {}


class TestMaximusProviderFactoryExecute:
    """Test Factory execute integration."""

    @pytest.mark.asyncio
    async def test_factory_execute_success(self) -> None:
        """HYPOTHESIS: factory_execute runs tool with params."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {
            "result": 42,
            "success": True,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.factory_execute(
                tool_name="test_tool",
                params={"input": "test"},
            )

            assert result["result"] == 42
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_factory_delete_success(self) -> None:
        """HYPOTHESIS: factory_delete removes tool."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: bool = await provider.factory_delete("test_tool")

            assert result is True

    @pytest.mark.asyncio
    async def test_factory_delete_returns_false_on_failure(self) -> None:
        """HYPOTHESIS: factory_delete returns False on failure."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: bool = await provider.factory_delete("nonexistent")

            assert result is False


class TestMaximusProviderErrorHandling:
    """Test error handling paths."""

    @pytest.mark.asyncio
    async def test_request_returns_error_when_client_none(self) -> None:
        """HYPOTHESIS: _request returns error when client not initialized."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._client = None

        result: Dict[str, Any] = await provider.tribunal_health()

        assert "error" in result

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_adds_error_decision_on_failure(self) -> None:
        """HYPOTHESIS: tribunal_evaluate sets decision=ERROR on failure."""
        provider: MaximusProvider = MaximusProvider()

        mock_response: MagicMock = MagicMock()
        mock_response.json.return_value = {"error": "Service unavailable"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            provider, '_ensure_initialized', new_callable=AsyncMock
        ):
            mock_client: AsyncMock = AsyncMock()
            mock_client.request.return_value = mock_response
            provider._client = mock_client
            provider._initialized = True

            result: Dict[str, Any] = await provider.tribunal_evaluate("test log")

            assert result["decision"] == "ERROR"


class TestMaximusProviderStatus:
    """Test status reporting."""

    def test_get_status_not_initialized(self) -> None:
        """HYPOTHESIS: get_status returns not initialized."""
        provider: MaximusProvider = MaximusProvider()
        status: Dict[str, Any] = provider.get_status()

        assert status["initialized"] is False

    def test_get_status_initialized(self) -> None:
        """HYPOTHESIS: get_status returns config when initialized."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._health_status = {"status": "ok"}

        status: Dict[str, Any] = provider.get_status()

        assert status["initialized"] is True
        assert "config" in status
        assert status["config"]["tribunal_enabled"] is True

    def test_get_status_includes_circuit_breaker(self) -> None:
        """HYPOTHESIS: get_status includes circuit breaker stats."""
        provider: MaximusProvider = MaximusProvider()
        status: Dict[str, Any] = provider.get_status()

        assert "circuit_breaker" in status
        assert status["circuit_breaker"]["state"] == "closed"


class TestMaximusProviderStream:
    """Test streaming functionality."""

    @pytest.mark.asyncio
    async def test_stream_yields_error_when_client_none_after_init(self) -> None:
        """HYPOTHESIS: stream yields error when client becomes None."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._client = None  # Simulate client becoming None

        chunks = []
        async for chunk in provider.stream("test prompt"):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert "not initialized" in chunks[0]

    @pytest.mark.asyncio
    async def test_stream_circuit_open_yields_error(self) -> None:
        """HYPOTHESIS: stream yields error when circuit is open."""
        provider: MaximusProvider = MaximusProvider()
        provider._initialized = True
        provider._client = AsyncMock()

        # Open the circuit
        for _ in range(10):
            provider._breaker.record_failure()

        chunks = []
        async for chunk in provider.stream("test prompt"):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert "circuit open" in chunks[0]


class TestMaximusProviderBackgroundTasks:
    """Test background task methods."""

    @pytest.mark.asyncio
    async def test_evaluate_in_tribunal_handles_exception(self) -> None:
        """HYPOTHESIS: _evaluate_in_tribunal catches exceptions."""
        provider: MaximusProvider = MaximusProvider()

        with patch.object(
            provider, 'tribunal_evaluate', new_callable=AsyncMock
        ) as mock_evaluate:
            mock_evaluate.side_effect = Exception("Test error")

            # Should not raise - best effort
            await provider._evaluate_in_tribunal("prompt", "response")

    @pytest.mark.asyncio
    async def test_store_interaction_handles_exception(self) -> None:
        """HYPOTHESIS: _store_interaction catches exceptions."""
        provider: MaximusProvider = MaximusProvider()

        with patch.object(
            provider, 'memory_store', new_callable=AsyncMock
        ) as mock_store:
            mock_store.side_effect = Exception("Test error")

            # Should not raise - best effort
            await provider._store_interaction("prompt", "response")


class TestMaximusConfigTransport:
    """Test MaximusConfig transport methods."""

    def test_transport_mode_auto(self) -> None:
        """HYPOTHESIS: AUTO mode enables both MCP and HTTP."""
        config: MaximusConfig = MaximusConfig(transport_mode=TransportMode.AUTO)
        assert config.should_use_mcp() is True
        assert config.should_fallback_to_http() is True

    def test_transport_mode_mcp_only(self) -> None:
        """HYPOTHESIS: MCP mode uses only MCP."""
        config: MaximusConfig = MaximusConfig(transport_mode=TransportMode.MCP)
        assert config.should_use_mcp() is True
        assert config.should_fallback_to_http() is False

    def test_transport_mode_http_only(self) -> None:
        """HYPOTHESIS: HTTP mode uses only HTTP."""
        config: MaximusConfig = MaximusConfig(transport_mode=TransportMode.HTTP)
        assert config.should_use_mcp() is False
        assert config.should_fallback_to_http() is True

    def test_effective_url_mcp(self) -> None:
        """HYPOTHESIS: get_effective_url returns MCP URL for MCP mode."""
        config: MaximusConfig = MaximusConfig(
            transport_mode=TransportMode.MCP,
            mcp_url="http://mcp:8100/mcp",
            base_url="http://http:8100",
        )
        assert config.get_effective_url() == "http://mcp:8100/mcp"

    def test_effective_url_http(self) -> None:
        """HYPOTHESIS: get_effective_url returns base URL for HTTP mode."""
        config: MaximusConfig = MaximusConfig(
            transport_mode=TransportMode.HTTP,
            mcp_url="http://mcp:8100/mcp",
            base_url="http://http:8100",
        )
        assert config.get_effective_url() == "http://http:8100"
