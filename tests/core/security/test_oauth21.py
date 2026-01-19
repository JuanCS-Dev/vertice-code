"""
Tests for OAuth 2.1 Client Implementation.

Tests MCP 2025-11-25 OAuth requirements including PKCE and discovery.

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core.security.oauth21 import (
    OAuth21Client,
    OAuth21Config,
    TokenResponse,
    AuthorizationServerMetadata,
    ProtectedResourceMetadata,
)


# =============================================================================
# CONFIG TESTS
# =============================================================================


class TestOAuth21Config:
    """Tests for OAuth21Config."""

    def test_minimal_config(self) -> None:
        """Minimal config with just client_id."""
        config = OAuth21Config(client_id="https://app.example.com/oauth/meta.json")

        assert config.client_id == "https://app.example.com/oauth/meta.json"
        assert config.redirect_uri == "http://localhost:3000/callback"
        assert config.scopes == []
        assert config.timeout == 30.0

    def test_full_config(self) -> None:
        """Full config with all options."""
        config = OAuth21Config(
            client_id="https://app.example.com/oauth/meta.json",
            redirect_uri="http://localhost:8080/cb",
            resource="https://mcp.example.com",
            scopes=["files:read", "files:write"],
            timeout=60.0,
        )

        assert config.redirect_uri == "http://localhost:8080/cb"
        assert config.resource == "https://mcp.example.com"
        assert config.scopes == ["files:read", "files:write"]
        assert config.timeout == 60.0


# =============================================================================
# METADATA TESTS
# =============================================================================


class TestAuthorizationServerMetadata:
    """Tests for AuthorizationServerMetadata."""

    def test_from_dict(self) -> None:
        """Create from discovery response."""
        data = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": ["files:read", "files:write"],
        }

        meta = AuthorizationServerMetadata.from_dict(data)

        assert meta.issuer == "https://auth.example.com"
        assert meta.authorization_endpoint == "https://auth.example.com/authorize"
        assert meta.token_endpoint == "https://auth.example.com/token"
        assert meta.supports_pkce_s256() is True

    def test_supports_pkce_s256_true(self) -> None:
        """S256 support detected correctly."""
        meta = AuthorizationServerMetadata(
            issuer="test",
            authorization_endpoint="test",
            token_endpoint="test",
            code_challenge_methods_supported=["plain", "S256"],
        )

        assert meta.supports_pkce_s256() is True

    def test_supports_pkce_s256_false(self) -> None:
        """Missing S256 support detected."""
        meta = AuthorizationServerMetadata(
            issuer="test",
            authorization_endpoint="test",
            token_endpoint="test",
            code_challenge_methods_supported=["plain"],
        )

        assert meta.supports_pkce_s256() is False


class TestProtectedResourceMetadata:
    """Tests for ProtectedResourceMetadata."""

    def test_from_dict(self) -> None:
        """Create from discovery response."""
        data = {
            "resource": "https://mcp.example.com",
            "authorization_servers": ["https://auth.example.com"],
            "scopes_supported": ["files:read"],
        }

        meta = ProtectedResourceMetadata.from_dict(data)

        assert meta.resource == "https://mcp.example.com"
        assert meta.authorization_servers == ["https://auth.example.com"]
        assert meta.scopes_supported == ["files:read"]


# =============================================================================
# TOKEN RESPONSE TESTS
# =============================================================================


class TestTokenResponse:
    """Tests for TokenResponse."""

    def test_from_dict(self) -> None:
        """Create from token endpoint response."""
        data = {
            "access_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_xyz",
            "scope": "files:read files:write",
        }

        token = TokenResponse.from_dict(data)

        assert token.access_token == "eyJ..."
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.refresh_token == "refresh_xyz"
        assert token.scope == "files:read files:write"

    def test_is_expired_false(self) -> None:
        """Fresh token is not expired."""
        token = TokenResponse(
            access_token="test",
            expires_in=3600,
            issued_at=time.time(),
        )

        assert token.is_expired() is False

    def test_is_expired_true(self) -> None:
        """Old token is expired."""
        token = TokenResponse(
            access_token="test",
            expires_in=3600,
            issued_at=time.time() - 4000,  # Issued 4000s ago
        )

        assert token.is_expired() is True

    def test_is_expired_with_buffer(self) -> None:
        """Expiration considers buffer time."""
        token = TokenResponse(
            access_token="test",
            expires_in=100,
            issued_at=time.time() - 50,  # 50s left
        )

        # With 60s buffer, should be "expired"
        assert token.is_expired(buffer_seconds=60) is True

        # With 30s buffer, should be ok
        assert token.is_expired(buffer_seconds=30) is False

    def test_authorization_header(self) -> None:
        """Authorization header is correctly formatted."""
        token = TokenResponse(
            access_token="abc123",
            token_type="Bearer",
        )

        assert token.authorization_header == "Bearer abc123"


# =============================================================================
# OAUTH CLIENT TESTS
# =============================================================================


class TestOAuth21Client:
    """Tests for OAuth21Client."""

    @pytest.fixture
    def config(self) -> OAuth21Config:
        """Create test config."""
        return OAuth21Config(
            client_id="https://app.example.com/oauth/meta.json",
            redirect_uri="http://localhost:3000/callback",
            resource="https://mcp.example.com",
            scopes=["files:read"],
        )

    @pytest.fixture
    def client(self, config: OAuth21Config) -> OAuth21Client:
        """Create test client."""
        return OAuth21Client(config)

    def test_initial_state(self, client: OAuth21Client) -> None:
        """Client starts unauthenticated."""
        assert client.is_authenticated is False
        assert client.token is None

    def test_create_authorization_url_requires_discovery(self, client: OAuth21Client) -> None:
        """create_authorization_url fails without discovery."""
        with pytest.raises(ValueError, match="Call discover"):
            client.create_authorization_url()

    @pytest.mark.asyncio
    async def test_create_authorization_url_with_mock_discovery(
        self, client: OAuth21Client
    ) -> None:
        """create_authorization_url works after discovery."""
        # Mock discovery
        client._auth_server = AuthorizationServerMetadata(
            issuer="https://auth.example.com",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            code_challenge_methods_supported=["S256"],
        )
        client._resource_meta = ProtectedResourceMetadata(
            resource="https://mcp.example.com",
        )

        auth_url, state = client.create_authorization_url()

        assert "https://auth.example.com/authorize?" in auth_url
        assert "client_id=" in auth_url
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert "state=" in auth_url
        assert len(state) > 20  # State should be long random string

    @pytest.mark.asyncio
    async def test_validate_callback_state(self, client: OAuth21Client) -> None:
        """Callback state validation works."""
        client._auth_server = AuthorizationServerMetadata(
            issuer="test",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            code_challenge_methods_supported=["S256"],
        )
        client._resource_meta = ProtectedResourceMetadata(resource="test")

        _, state = client.create_authorization_url()

        assert client.validate_callback(state) is True
        assert client.validate_callback("wrong_state") is False

    @pytest.mark.asyncio
    async def test_exchange_code_requires_flow_started(self, client: OAuth21Client) -> None:
        """exchange_code fails if flow not started."""
        with pytest.raises(ValueError, match="not started"):
            await client.exchange_code("some_code")

    @pytest.mark.asyncio
    async def test_get_valid_token_requires_token(self, client: OAuth21Client) -> None:
        """get_valid_token fails without token."""
        with pytest.raises(ValueError, match="No token available"):
            await client.get_valid_token()

    @pytest.mark.asyncio
    async def test_context_manager(self, config: OAuth21Config) -> None:
        """Client works as async context manager."""
        async with OAuth21Client(config) as client:
            assert isinstance(client, OAuth21Client)
        # HTTP client should be closed


# =============================================================================
# INTEGRATION FLOW TEST (Mocked)
# =============================================================================


class TestOAuth21Flow:
    """Integration tests for OAuth flow (mocked HTTP)."""

    @pytest.mark.asyncio
    async def test_full_flow_mocked(self) -> None:
        """Test complete OAuth flow with mocked responses."""
        config = OAuth21Config(
            client_id="https://app.example.com/oauth/meta.json",
            resource="https://mcp.example.com",
        )

        client = OAuth21Client(config)

        # Mock auth server metadata
        client._auth_server = AuthorizationServerMetadata(
            issuer="https://auth.example.com",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            code_challenge_methods_supported=["S256"],
        )
        client._resource_meta = ProtectedResourceMetadata(
            resource="https://mcp.example.com",
            authorization_servers=["https://auth.example.com"],
        )

        # Step 1: Create authorization URL
        auth_url, state = client.create_authorization_url()
        assert auth_url.startswith("https://auth.example.com/authorize")

        # Step 2: Validate callback
        assert client.validate_callback(state) is True

        # Step 3: Mock token exchange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
        }

        with patch.object(client._http, "post", return_value=mock_response):
            token = await client.exchange_code("test_code")

        assert token.access_token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"
        assert client.is_authenticated is True

        await client.close()
