"""Tests for VerticeClient unified LLM client.

Tests cover:
- Provider priority and fallback
- Circuit breaker behavior
- Rate limit handling
- Configuration options

Follows CODE_CONSTITUTION: comprehensive tests for all public methods.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch
from typing import AsyncIterator, Dict, List

from vertice_core.clients.vertice_coreent import (
    VerticeClient,
    VerticeClientConfig,
    AllProvidersExhaustedError,
    DEFAULT_PRIORITY,
)


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(
        self,
        name: str = "mock",
        available: bool = True,
        fail_with: Exception | None = None,
        response: str = "Hello from mock!",
    ):
        self.name = name
        self._available = available
        self._fail_with = fail_with
        self._response = response
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs,
    ) -> AsyncIterator[str]:
        self.call_count += 1
        if self._fail_with:
            raise self._fail_with
        for word in self._response.split():
            yield word + " "

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs,
    ) -> str:
        self.call_count += 1
        if self._fail_with:
            raise self._fail_with
        return self._response


class TestVerticeClientConfig:
    """Tests for VerticeClientConfig."""

    def test_default_config(self):
        """Default config has correct values."""
        config = VerticeClientConfig()
        assert config.priority == DEFAULT_PRIORITY
        assert config.max_retries == 2
        assert config.circuit_breaker_threshold == 5
        assert config.default_max_tokens == 8192
        assert config.default_temperature == 1.0

    def test_custom_priority(self):
        """Custom priority is preserved."""
        config = VerticeClientConfig(priority=["azure", "gemini"])
        assert config.priority == ["azure", "gemini"]


class TestVerticeClientBasic:
    """Basic VerticeClient tests."""

    def test_init_default(self):
        """Client initializes with default config."""
        client = VerticeClient()
        assert client.config.priority == DEFAULT_PRIORITY
        assert client.current_provider is None

    def test_init_custom_config(self):
        """Client accepts custom config."""
        config = VerticeClientConfig(priority=["azure"])
        client = VerticeClient(config=config)
        assert client.config.priority == ["azure"]

    def test_init_with_providers(self):
        """Client accepts pre-built providers."""
        mock = MockProvider()
        client = VerticeClient(providers={"mock": mock})
        assert "mock" in client._providers


class TestVerticeClientStreaming:
    """Tests for stream_chat method."""

    @pytest.mark.asyncio
    async def test_stream_success(self):
        """Successful streaming from first provider."""
        mock = MockProvider(response="Hello world")
        config = VerticeClientConfig(priority=["mock"])
        client = VerticeClient(config=config, providers={"mock": mock})

        # Mock _has_api_key to return True for mock
        with patch.object(client, "_has_api_key", return_value=True):
            chunks = []
            async for chunk in client.stream_chat([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)

            assert "".join(chunks).strip() == "Hello world"
            assert mock.call_count == 1
            assert client.current_provider == "mock"

    @pytest.mark.asyncio
    async def test_stream_fallback_on_failure(self):
        """Falls back to next provider on failure."""
        mock1 = MockProvider(name="first", fail_with=Exception("Fail"))
        mock2 = MockProvider(name="second", response="Fallback worked")
        config = VerticeClientConfig(priority=["first", "second"])
        client = VerticeClient(config=config, providers={"first": mock1, "second": mock2})

        with patch.object(client, "_has_api_key", return_value=True):
            chunks = []
            async for chunk in client.stream_chat([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)

            assert "Fallback worked" in "".join(chunks)
            assert mock1.call_count == 1
            assert mock2.call_count == 1

    @pytest.mark.asyncio
    async def test_stream_rate_limit_fallback(self):
        """Falls back on rate limit (429) error."""
        mock1 = MockProvider(name="first", fail_with=Exception("429 rate limit"))
        mock2 = MockProvider(name="second", response="Success")
        config = VerticeClientConfig(priority=["first", "second"])
        client = VerticeClient(config=config, providers={"first": mock1, "second": mock2})

        with patch.object(client, "_has_api_key", return_value=True):
            chunks = []
            async for chunk in client.stream_chat([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)

            assert "Success" in "".join(chunks)

    @pytest.mark.asyncio
    async def test_all_providers_exhausted(self):
        """Raises AllProvidersExhaustedError when all fail."""
        mock1 = MockProvider(name="first", fail_with=Exception("Fail 1"))
        mock2 = MockProvider(name="second", fail_with=Exception("Fail 2"))
        config = VerticeClientConfig(priority=["first", "second"])
        client = VerticeClient(config=config, providers={"first": mock1, "second": mock2})

        with patch.object(client, "_has_api_key", return_value=True):
            with pytest.raises(AllProvidersExhaustedError) as exc_info:
                chunks = []
                async for chunk in client.stream_chat([{"role": "user", "content": "Hi"}]):
                    chunks.append(chunk)

            assert "first" in exc_info.value.tried_providers
            assert "second" in exc_info.value.tried_providers

    @pytest.mark.asyncio
    async def test_system_prompt_prepended(self):
        """System prompt is prepended to messages."""
        mock = MockProvider()
        config = VerticeClientConfig(priority=["mock"])
        client = VerticeClient(config=config, providers={"mock": mock})

        with patch.object(client, "_has_api_key", return_value=True):
            # Capture the messages passed to provider
            original_stream = mock.stream_chat
            captured_messages = []

            async def capture_stream(messages, **kwargs):
                captured_messages.extend(messages)
                async for chunk in original_stream(messages, **kwargs):
                    yield chunk

            mock.stream_chat = capture_stream

            async for _ in client.stream_chat(
                [{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful",
            ):
                pass

            assert len(captured_messages) == 2
            assert captured_messages[0]["role"] == "system"
            assert captured_messages[0]["content"] == "You are helpful"


class TestVerticeClientCircuitBreaker:
    """Tests for circuit breaker behavior."""

    def test_circuit_breaker_opens(self):
        """Circuit breaker opens after threshold failures."""
        config = VerticeClientConfig(circuit_breaker_threshold=3)
        client = VerticeClient(config=config)

        # Record failures
        for _ in range(3):
            client._record_failure("test", Exception("fail"))

        assert not client._can_use("test")

    def test_circuit_breaker_resets_on_success(self):
        """Circuit breaker resets on success."""
        config = VerticeClientConfig(circuit_breaker_threshold=3)
        client = VerticeClient(config=config)

        # Record failures
        for _ in range(2):
            client._record_failure("test", Exception("fail"))

        assert client._can_use("test")  # Still under threshold

        # Record success
        client._record_success("test")

        assert client._failures.get("test", 0) == 0

    def test_reset_circuit_breaker_single(self):
        """Reset single provider circuit breaker."""
        client = VerticeClient()
        client._failures["test"] = 10
        client._errors["test"] = "error"

        client.reset_circuit_breaker("test")

        assert "test" not in client._failures
        assert "test" not in client._errors

    def test_reset_circuit_breaker_all(self):
        """Reset all circuit breakers."""
        client = VerticeClient()
        client._failures["a"] = 5
        client._failures["b"] = 3
        client._errors["a"] = "error"

        client.reset_circuit_breaker()

        assert len(client._failures) == 0
        assert len(client._errors) == 0


class TestVerticeClientGenerate:
    """Tests for generate method."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Generate returns complete response."""
        mock = MockProvider(response="Complete response")
        config = VerticeClientConfig(priority=["mock"])
        client = VerticeClient(config=config, providers={"mock": mock})

        with patch.object(client, "_has_api_key", return_value=True):
            result = await client.generate([{"role": "user", "content": "Hi"}])
            assert "Complete response" in result


class TestVerticeClientStatus:
    """Tests for status and availability methods."""

    def test_get_available_providers(self):
        """Returns available and healthy providers."""
        client = VerticeClient()

        with patch.object(client, "_has_api_key", side_effect=lambda n: n == "groq"):
            available = client.get_available_providers()
            assert "groq" in available
            assert "cerebras" not in available

    def test_get_provider_status(self):
        """Returns detailed provider status."""
        client = VerticeClient()
        client._failures["groq"] = 2
        client._errors["groq"] = "test error"

        status = client.get_provider_status()

        assert "priority" in status
        assert "providers" in status
        assert status["providers"]["groq"]["failures"] == 2
        assert status["providers"]["groq"]["last_error"] == "test error"


class TestVerticeClientRateLimitDetection:
    """Tests for rate limit detection."""

    def test_detects_429_error(self):
        """Detects 429 in error message."""
        client = VerticeClient()
        assert client._is_rate_limit(Exception("Error 429: Too many requests"))

    def test_detects_rate_limit_text(self):
        """Detects 'rate limit' in error message."""
        client = VerticeClient()
        assert client._is_rate_limit(Exception("Rate limit exceeded"))

    def test_non_rate_limit_error(self):
        """Non-rate-limit errors return False."""
        client = VerticeClient()
        assert not client._is_rate_limit(Exception("Connection timeout"))


class TestVerticeClientFactory:
    """Tests for get_client factory function."""

    def test_get_client_singleton(self):
        """get_client returns singleton by default."""
        from vertice_core.clients.vertice_coreent import get_client

        client1 = get_client()
        client2 = get_client()
        assert client1 is client2

    def test_get_client_force_new(self):
        """get_client with force_new creates new instance."""
        from vertice_core.clients.vertice_coreent import get_client

        client1 = get_client()
        client2 = get_client(force_new=True)
        assert client1 is not client2

    def test_get_client_custom_config(self):
        """get_client with config creates new instance."""
        from vertice_core.clients.vertice_coreent import get_client

        config = VerticeClientConfig(priority=["azure"])
        client = get_client(config=config)
        assert client.config.priority == ["azure"]
