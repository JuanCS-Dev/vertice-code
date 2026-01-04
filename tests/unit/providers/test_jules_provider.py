"""
Unit tests for JulesClient.

Tests API client functionality including:
- Session management
- Activity streaming
- Error handling
- Circuit breaker
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertice_cli.core.providers.jules_provider import (
    JulesClient,
    JulesClientError,
    JulesAuthError,
    JulesRateLimitError,
    JulesSessionError,
    get_jules_client,
)
from vertice_core.types.jules_types import (
    JulesConfig,
    JulesSession,
    JulesSessionState,
    JulesActivity,
    JulesActivityType,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def jules_config() -> JulesConfig:
    """Create test config."""
    return JulesConfig(
        api_key="test-api-key",
        base_url="https://jules.test.api/v1alpha",
        poll_interval=0.1,
        max_poll_attempts=5,
        timeout=5.0,
    )


@pytest.fixture
def jules_client(jules_config: JulesConfig) -> JulesClient:
    """Create test client."""
    return JulesClient(config=jules_config)


@pytest.fixture
def mock_session_data() -> Dict[str, Any]:
    """Mock session API response."""
    return {
        "name": "sessions/test-123",
        "state": "PLANNING",
        "title": "Test Session",
        "prompt": "Test prompt",
        "createTime": "2026-01-04T10:00:00Z",
        "updateTime": "2026-01-04T10:05:00Z",
        "plan": {
            "id": "plan-456",
            "steps": [
                {"id": "step-1", "description": "Analyze codebase", "action": "analyze"},
                {"id": "step-2", "description": "Implement feature", "action": "code"},
            ],
            "filesToModify": ["src/app.py"],
            "filesToCreate": ["src/new_feature.py"],
        },
    }


@pytest.fixture
def mock_activity_data() -> Dict[str, Any]:
    """Mock activity API response."""
    return {
        "name": "activities/act-789",
        "type": "progressUpdated",
        "createTime": "2026-01-04T10:05:00Z",
        "message": "Analyzing codebase structure...",
        "data": {"progress": 50},
    }


# =============================================================================
# TESTS - CONFIGURATION
# =============================================================================


class TestJulesClientConfig:
    """Test client configuration."""

    def test_default_config_from_env(self) -> None:
        """Client uses env vars when no config provided."""
        with patch.dict("os.environ", {"JULES_API_KEY": "env-key"}):
            client = JulesClient()
            assert client.config.api_key == "env-key"

    def test_custom_config(self, jules_config: JulesConfig) -> None:
        """Client uses provided config."""
        client = JulesClient(config=jules_config)
        assert client.config.api_key == "test-api-key"
        assert client.config.poll_interval == 0.1

    def test_is_available_with_key(self, jules_client: JulesClient) -> None:
        """Client is available when configured."""
        assert jules_client.is_available is True

    def test_is_available_without_key(self) -> None:
        """Client unavailable without API key."""
        client = JulesClient(config=JulesConfig(api_key=""))
        assert client.is_available is False


# =============================================================================
# TESTS - SESSION MANAGEMENT
# =============================================================================


class TestSessionManagement:
    """Test session CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_session(
        self, jules_client: JulesClient, mock_session_data: Dict[str, Any]
    ) -> None:
        """Create session returns parsed JulesSession."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_session_data

            session = await jules_client.create_session(
                prompt="Test prompt",
                source_context={"source": "sources/github/org/repo"},
                title="Test Session",
            )

            assert isinstance(session, JulesSession)
            assert session.session_id == "sessions/test-123"
            assert session.state == JulesSessionState.PLANNING
            assert session.title == "Test Session"
            assert session.plan is not None
            assert len(session.plan.steps) == 2

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/sessions"

    @pytest.mark.asyncio
    async def test_get_session(
        self, jules_client: JulesClient, mock_session_data: Dict[str, Any]
    ) -> None:
        """Get session returns parsed data."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_session_data["state"] = "IN_PROGRESS"
            mock_request.return_value = mock_session_data

            session = await jules_client.get_session("sessions/test-123")

            assert session.state == JulesSessionState.IN_PROGRESS
            mock_request.assert_called_with("GET", "/sessions/sessions/test-123")

    @pytest.mark.asyncio
    async def test_list_sessions(
        self, jules_client: JulesClient, mock_session_data: Dict[str, Any]
    ) -> None:
        """List sessions returns parsed list."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"sessions": [mock_session_data]}

            sessions = await jules_client.list_sessions(page_size=10)

            assert len(sessions) == 1
            assert sessions[0].session_id == "sessions/test-123"

    @pytest.mark.asyncio
    async def test_approve_plan(
        self, jules_client: JulesClient, mock_session_data: Dict[str, Any]
    ) -> None:
        """Approve plan updates session state."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_session_data["state"] = "IN_PROGRESS"
            mock_request.return_value = mock_session_data

            session = await jules_client.approve_plan("sessions/test-123")

            assert session.state == JulesSessionState.IN_PROGRESS
            mock_request.assert_called_with(
                "POST", "/sessions/sessions/test-123:approvePlan", {}
            )

    @pytest.mark.asyncio
    async def test_send_message(
        self, jules_client: JulesClient, mock_session_data: Dict[str, Any]
    ) -> None:
        """Send message returns updated session."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_session_data

            session = await jules_client.send_message(
                "sessions/test-123", "Continue with implementation"
            )

            assert session is not None
            mock_request.assert_called_with(
                "POST",
                "/sessions/sessions/test-123:sendMessage",
                {"message": "Continue with implementation"},
            )


# =============================================================================
# TESTS - ACTIVITY STREAMING
# =============================================================================


class TestActivityStreaming:
    """Test activity polling and streaming."""

    @pytest.mark.asyncio
    async def test_get_activities(
        self, jules_client: JulesClient, mock_activity_data: Dict[str, Any]
    ) -> None:
        """Get activities returns parsed list."""
        with patch.object(
            jules_client, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"activities": [mock_activity_data]}

            activities = await jules_client.get_activities("sessions/test-123")

            assert len(activities) == 1
            assert activities[0].type == JulesActivityType.PROGRESS_UPDATED
            assert "Analyzing" in activities[0].message

    @pytest.mark.asyncio
    async def test_stream_activities_deduplicates(
        self, jules_client: JulesClient
    ) -> None:
        """Stream activities deduplicates by activity_id."""
        # Test that seen activities are tracked
        activity = JulesActivity(
            activity_id="act-1",
            type=JulesActivityType.SESSION_COMPLETED,
            timestamp=datetime.now(),
            message="Done",
        )

        async def mock_get_activities(session_id: str, page_size: int = 50):
            return [activity]

        async def mock_get_session(session_id: str):
            return JulesSession(
                session_id="test-123",
                state=JulesSessionState.COMPLETED,
                title="Test",
                prompt="Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        with patch.object(jules_client, "get_activities", side_effect=mock_get_activities):
            with patch.object(jules_client, "get_session", side_effect=mock_get_session):
                collected: List[JulesActivity] = []
                async for act in jules_client.stream_activities("test-123"):
                    collected.append(act)

                # Should have exactly 1 activity (completed)
                assert len(collected) == 1
                assert collected[0].activity_id == "act-1"
                assert collected[0].type == JulesActivityType.SESSION_COMPLETED


# =============================================================================
# TESTS - ERROR HANDLING
# =============================================================================


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_auth_error_401(self, jules_client: JulesClient) -> None:
        """401 raises JulesAuthError."""
        # Create a mock context manager for the response
        mock_response = MagicMock()
        mock_response.status = 401

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None

        # Mock the session
        mock_session = MagicMock()
        mock_session.request.return_value = mock_context
        mock_session.closed = False

        jules_client._session = mock_session

        with pytest.raises(JulesAuthError):
            await jules_client._request("GET", "/sessions")

    @pytest.mark.asyncio
    async def test_rate_limit_429(self, jules_client: JulesClient) -> None:
        """429 raises JulesRateLimitError with retry_after."""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "60"}

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.request.return_value = mock_context
        mock_session.closed = False

        jules_client._session = mock_session

        with pytest.raises(JulesRateLimitError) as exc_info:
            await jules_client._request("GET", "/sessions")

        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, jules_client: JulesClient) -> None:
        """Circuit breaker opens after consecutive failures."""
        import aiohttp

        mock_session = MagicMock()
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
        mock_session.closed = False

        jules_client._session = mock_session

        # Trigger 5+ failures (need more because of retries)
        for _ in range(10):
            try:
                await jules_client._request("GET", "/sessions")
            except JulesClientError:
                pass

        # Circuit should be open
        assert jules_client._circuit_open is True
        assert jules_client.is_available is False

    def test_reset_circuit_breaker(self, jules_client: JulesClient) -> None:
        """Reset circuit breaker restores availability."""
        jules_client._circuit_open = True
        jules_client._failure_count = 5

        jules_client.reset_circuit_breaker()

        assert jules_client._circuit_open is False
        assert jules_client._failure_count == 0
        assert jules_client.is_available is True


# =============================================================================
# TESTS - FACTORY
# =============================================================================


class TestFactory:
    """Test factory function."""

    def test_get_jules_client_singleton(self) -> None:
        """get_jules_client returns singleton."""
        # Clear singleton
        import vertice_cli.core.providers.jules_provider as module

        module._default_client = None

        with patch.dict("os.environ", {"JULES_API_KEY": "test-key"}):
            client1 = get_jules_client()
            client2 = get_jules_client()

            assert client1 is client2

    def test_get_jules_client_with_config(self) -> None:
        """get_jules_client with config creates new instance."""
        config = JulesConfig(api_key="custom-key")

        client = get_jules_client(config)

        assert client.config.api_key == "custom-key"
