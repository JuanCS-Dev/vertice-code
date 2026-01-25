"""
OAuth 2.1 Client Implementation for MCP.
=========================================

Implements OAuth 2.1 authorization code flow with PKCE
per MCP 2025-11-25 specification requirements.

Features:
- Authorization Server Metadata discovery (RFC 8414)
- Protected Resource Metadata (RFC 9728)
- PKCE with S256 (mandatory)
- Token management (access, refresh, rotation)
- Audience binding validation

References:
- MCP Auth: https://modelcontextprotocol.io/specification/draft/basic/authorization
- OAuth 2.1: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-12
- RFC 8414: https://datatracker.ietf.org/doc/html/rfc8414
- RFC 9728: https://datatracker.ietf.org/doc/html/rfc9728

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

import httpx

from .pkce import PKCEChallenge, generate_pkce

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class AuthorizationServerMetadata:
    """OAuth 2.0 Authorization Server Metadata (RFC 8414).

    Attributes:
        issuer: Authorization server identifier
        authorization_endpoint: URL for authorization requests
        token_endpoint: URL for token requests
        code_challenge_methods_supported: Supported PKCE methods
        scopes_supported: Available OAuth scopes
        grant_types_supported: Supported grant types
        response_types_supported: Supported response types
    """

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    code_challenge_methods_supported: List[str] = field(default_factory=list)
    scopes_supported: List[str] = field(default_factory=list)
    grant_types_supported: List[str] = field(default_factory=list)
    response_types_supported: List[str] = field(default_factory=list)
    client_id_metadata_document_supported: bool = False
    revocation_endpoint: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorizationServerMetadata":
        """Create from discovery response."""
        return cls(
            issuer=data.get("issuer", ""),
            authorization_endpoint=data.get("authorization_endpoint", ""),
            token_endpoint=data.get("token_endpoint", ""),
            code_challenge_methods_supported=data.get("code_challenge_methods_supported", []),
            scopes_supported=data.get("scopes_supported", []),
            grant_types_supported=data.get("grant_types_supported", []),
            response_types_supported=data.get("response_types_supported", []),
            client_id_metadata_document_supported=data.get(
                "client_id_metadata_document_supported", False
            ),
            revocation_endpoint=data.get("revocation_endpoint"),
        )

    def supports_pkce_s256(self) -> bool:
        """Check if server supports S256 PKCE (required by MCP)."""
        return "S256" in self.code_challenge_methods_supported


@dataclass
class ProtectedResourceMetadata:
    """Protected Resource Metadata (RFC 9728).

    Attributes:
        resource: Resource server identifier
        authorization_servers: List of authorization server URLs
        scopes_supported: Scopes for this resource
        bearer_methods_supported: Token delivery methods
    """

    resource: str
    authorization_servers: List[str] = field(default_factory=list)
    scopes_supported: List[str] = field(default_factory=list)
    bearer_methods_supported: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtectedResourceMetadata":
        """Create from discovery response."""
        return cls(
            resource=data.get("resource", ""),
            authorization_servers=data.get("authorization_servers", []),
            scopes_supported=data.get("scopes_supported", []),
            bearer_methods_supported=data.get("bearer_methods_supported", ["header"]),
        )


@dataclass
class TokenResponse:
    """OAuth 2.1 Token Response.

    Attributes:
        access_token: The access token
        token_type: Token type (usually "Bearer")
        expires_in: Token lifetime in seconds
        refresh_token: Optional refresh token
        scope: Granted scopes (space-separated)
        issued_at: Timestamp when token was issued
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    issued_at: float = field(default_factory=time.time)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenResponse":
        """Create from token endpoint response."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            issued_at=time.time(),
        )

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired (with buffer)."""
        return time.time() >= (self.issued_at + self.expires_in - buffer_seconds)

    @property
    def authorization_header(self) -> str:
        """Get Authorization header value."""
        return f"{self.token_type} {self.access_token}"


@dataclass
class OAuth21Config:
    """OAuth 2.1 client configuration.

    Attributes:
        client_id: Client identifier (URL for CIMD)
        redirect_uri: OAuth callback URL
        resource: MCP server resource URL
        scopes: Requested scopes
        timeout: HTTP request timeout
    """

    client_id: str
    redirect_uri: str = "http://localhost:3000/callback"
    resource: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    timeout: float = 30.0


# =============================================================================
# OAUTH 2.1 CLIENT
# =============================================================================


class OAuth21Client:
    """OAuth 2.1 client with PKCE for MCP authorization.

    Implements the authorization code flow with PKCE as required
    by MCP 2025-11-25 specification.

    Example:
        >>> config = OAuth21Config(
        ...     client_id="https://app.example.com/oauth/metadata.json",
        ...     redirect_uri="http://localhost:3000/callback",
        ...     resource="https://mcp.example.com",
        ... )
        >>> client = OAuth21Client(config)
        >>> await client.discover("https://mcp.example.com")
        >>> auth_url, state = client.create_authorization_url()
        >>> # User visits auth_url, authorizes, redirected with code
        >>> token = await client.exchange_code(code)
    """

    def __init__(self, config: OAuth21Config) -> None:
        """Initialize OAuth 2.1 client.

        Args:
            config: Client configuration
        """
        self.config = config
        self._http = httpx.AsyncClient(timeout=config.timeout)
        self._auth_server: Optional[AuthorizationServerMetadata] = None
        self._resource_meta: Optional[ProtectedResourceMetadata] = None
        self._pkce: Optional[PKCEChallenge] = None
        self._state: Optional[str] = None
        self._token: Optional[TokenResponse] = None

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "OAuth21Client":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # =========================================================================
    # DISCOVERY
    # =========================================================================

    async def discover(self, resource_url: str) -> None:
        """Discover authorization server from MCP resource.

        Implements RFC 9728 Protected Resource Metadata discovery
        and RFC 8414 Authorization Server Metadata discovery.

        Args:
            resource_url: URL of the MCP server

        Raises:
            ValueError: If discovery fails or PKCE not supported
        """
        # Step 1: Discover Protected Resource Metadata
        self._resource_meta = await self._discover_resource_metadata(resource_url)

        if not self._resource_meta.authorization_servers:
            raise ValueError(f"No authorization servers found for resource: {resource_url}")

        # Step 2: Discover Authorization Server Metadata
        auth_server_url = self._resource_meta.authorization_servers[0]
        self._auth_server = await self._discover_auth_server_metadata(auth_server_url)

        # Step 3: Verify PKCE S256 support (REQUIRED by MCP)
        if not self._auth_server.supports_pkce_s256():
            raise ValueError(
                "Authorization server does not support S256 PKCE " "(required by MCP 2025-11-25)"
            )

        logger.info(
            f"OAuth discovery complete: issuer={self._auth_server.issuer}, "
            f"scopes={self._auth_server.scopes_supported}"
        )

    async def _discover_resource_metadata(self, resource_url: str) -> ProtectedResourceMetadata:
        """Discover Protected Resource Metadata (RFC 9728).

        Args:
            resource_url: Resource server URL

        Returns:
            ProtectedResourceMetadata
        """
        parsed = urlparse(resource_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Try well-known endpoints
        well_known_paths = [
            f"{base_url}/.well-known/oauth-protected-resource{parsed.path}",
            f"{base_url}/.well-known/oauth-protected-resource",
        ]

        for url in well_known_paths:
            try:
                response = await self._http.get(url)
                if response.status_code == 200:
                    return ProtectedResourceMetadata.from_dict(response.json())
            except Exception as e:
                logger.debug(f"Resource metadata discovery failed for {url}: {e}")

        # If no well-known found, create minimal metadata
        logger.warning(
            f"No Protected Resource Metadata found for {resource_url}, " "using minimal defaults"
        )
        return ProtectedResourceMetadata(
            resource=resource_url,
            authorization_servers=[],
        )

    async def _discover_auth_server_metadata(self, issuer_url: str) -> AuthorizationServerMetadata:
        """Discover Authorization Server Metadata (RFC 8414).

        Args:
            issuer_url: Authorization server issuer URL

        Returns:
            AuthorizationServerMetadata

        Raises:
            ValueError: If discovery fails
        """
        parsed = urlparse(issuer_url)

        # Build discovery URLs per RFC 8414
        if parsed.path and parsed.path != "/":
            # Issuer with path component
            well_known_paths = [
                f"{parsed.scheme}://{parsed.netloc}/.well-known/oauth-authorization-server{parsed.path}",
                f"{parsed.scheme}://{parsed.netloc}/.well-known/openid-configuration{parsed.path}",
                f"{issuer_url}/.well-known/openid-configuration",
            ]
        else:
            # Issuer without path
            well_known_paths = [
                f"{issuer_url}/.well-known/oauth-authorization-server",
                f"{issuer_url}/.well-known/openid-configuration",
            ]

        for url in well_known_paths:
            try:
                response = await self._http.get(url)
                if response.status_code == 200:
                    return AuthorizationServerMetadata.from_dict(response.json())
            except Exception as e:
                logger.debug(f"Auth server metadata discovery failed for {url}: {e}")

        raise ValueError(f"Could not discover authorization server metadata for: {issuer_url}")

    # =========================================================================
    # AUTHORIZATION
    # =========================================================================

    def create_authorization_url(self, extra_scopes: Optional[List[str]] = None) -> tuple[str, str]:
        """Create authorization URL for user redirect.

        Generates PKCE challenge and state parameter.

        Args:
            extra_scopes: Additional scopes to request

        Returns:
            Tuple of (authorization_url, state)

        Raises:
            ValueError: If discovery not completed
        """
        if not self._auth_server:
            raise ValueError("Call discover() first")

        # Generate PKCE challenge
        self._pkce = generate_pkce()

        # Generate state for CSRF protection
        self._state = secrets.token_urlsafe(32)

        # Build scopes
        scopes = list(self.config.scopes)
        if extra_scopes:
            scopes.extend(extra_scopes)
        if self._resource_meta and self._resource_meta.scopes_supported:
            # Use resource-advertised scopes if none specified
            if not scopes:
                scopes = self._resource_meta.scopes_supported

        # Build authorization request parameters
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "state": self._state,
            **self._pkce.to_auth_params(),
        }

        if scopes:
            params["scope"] = " ".join(scopes)

        if self.config.resource:
            params["resource"] = self.config.resource

        auth_url = f"{self._auth_server.authorization_endpoint}?{urlencode(params)}"

        logger.debug(f"Authorization URL created: {auth_url}")
        return auth_url, self._state

    def validate_callback(self, state: str) -> bool:
        """Validate callback state parameter.

        Args:
            state: State from callback

        Returns:
            True if state matches
        """
        if not self._state:
            return False
        return secrets.compare_digest(state, self._state)

    async def exchange_code(self, code: str) -> TokenResponse:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            TokenResponse with access and refresh tokens

        Raises:
            ValueError: If exchange fails
        """
        if not self._auth_server or not self._pkce:
            raise ValueError("Authorization flow not started")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            **self._pkce.to_token_params(),
        }

        if self.config.resource:
            data["resource"] = self.config.resource

        response = await self._http.post(
            self._auth_server.token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise ValueError(
                f"Token exchange failed: {error_data.get('error', response.status_code)} "
                f"- {error_data.get('error_description', 'Unknown error')}"
            )

        self._token = TokenResponse.from_dict(response.json())

        # Clear PKCE after use (one-time)
        self._pkce = None
        self._state = None

        logger.info(
            f"Token obtained: expires_in={self._token.expires_in}s, " f"scope={self._token.scope}"
        )
        return self._token

    async def refresh_token(self) -> TokenResponse:
        """Refresh access token using refresh token.

        Returns:
            New TokenResponse

        Raises:
            ValueError: If no refresh token available
        """
        if not self._token or not self._token.refresh_token:
            raise ValueError("No refresh token available")

        if not self._auth_server:
            raise ValueError("Discovery not completed")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.config.client_id,
        }

        if self.config.resource:
            data["resource"] = self.config.resource

        response = await self._http.post(
            self._auth_server.token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise ValueError(
                f"Token refresh failed: {error_data.get('error', response.status_code)}"
            )

        self._token = TokenResponse.from_dict(response.json())

        logger.info(f"Token refreshed: expires_in={self._token.expires_in}s")
        return self._token

    async def get_valid_token(self) -> str:
        """Get valid access token, refreshing if needed.

        Returns:
            Access token string

        Raises:
            ValueError: If no token available and can't refresh
        """
        if not self._token:
            raise ValueError("No token available - complete authorization first")

        if self._token.is_expired():
            if self._token.refresh_token:
                await self.refresh_token()
            else:
                raise ValueError("Token expired and no refresh token available")

        return self._token.access_token

    @property
    def token(self) -> Optional[TokenResponse]:
        """Current token response."""
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid token."""
        return self._token is not None and not self._token.is_expired()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "OAuth21Client",
    "OAuth21Config",
    "TokenResponse",
    "AuthorizationServerMetadata",
    "ProtectedResourceMetadata",
]
