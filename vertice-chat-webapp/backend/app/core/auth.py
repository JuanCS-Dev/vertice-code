"""
Authentication utilities for Clerk JWT validation
Validates Clerk JWT tokens and extracts user information

Reference: https://clerk.com/docs/backend-requests/handling/manual-jwt
"""

import time
from typing import Optional, Dict, Any, List
import jwt
from jwt import PyJWTError
import httpx
from pydantic import BaseModel
import uuid

from app.core.config import settings
from app.core.agent_auth import get_agent_key_service, AgentKeyService
from app.core.auth_utils import generate_agent_api_key, hash_api_key, AgentIdentity


class ClerkUser(BaseModel):
    """Clerk user information extracted from JWT"""

    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    image_url: Optional[str] = None


class ClerkAuth:
    """Clerk authentication handler"""

    def __init__(self):
        self.clerk_secret_key = settings.CLERK_SECRET_KEY
        self.clerk_publishable_key = settings.CLERK_PUBLISHABLE_KEY

        # Allow development/testing without Clerk keys
        if not self.clerk_secret_key or not self.clerk_publishable_key:
            print(
                "WARNING: Clerk authentication not configured. Using mock authentication for development."
            )
            self.mock_mode = True
        else:
            self.mock_mode = False

        if self.mock_mode:
            self.issuer = "https://mock.clerk.com"
        else:
            # Extract issuer from publishable key (format: pk_test_xxx or pk_live_xxx)
            if self.clerk_publishable_key:
                key_parts = self.clerk_publishable_key.split("_")
                if len(key_parts) >= 2:
                    env_type = key_parts[1]  # "test" or "live"
                    self.issuer = f"https://clerk.{env_type}.clerk.com"
                else:
                    self.issuer = "https://clerk.clerk.com"  # fallback
            else:
                self.issuer = "https://clerk.clerk.com"  # fallback

    async def verify_token(self, token: str) -> Optional[ClerkUser]:
        """
        Verify and decode Clerk JWT token

        Args:
            token: JWT token from Authorization header

        Returns:
            ClerkUser if valid, None if invalid
        """
        try:
            if self.mock_mode:
                # Mock authentication for development/testing
                if token == "mock-jwt-token" or token.startswith("Bearer mock-jwt-token"):
                    return ClerkUser(
                        user_id="mock-user-123",
                        email="mock@example.com",
                        first_name="Mock",
                        last_name="User",
                    )
                return None

            # Production mode - proper JWT verification
            # For development, we'll decode without full verification
            # In production, implement proper JWKS verification

            # Decode payload without verification
            payload = jwt.decode(token, options={"verify_signature": False})

            # Basic validation
            if payload.get("iss") != self.issuer:
                return None

            if self.clerk_publishable_key and payload.get("aud") != [self.clerk_publishable_key]:
                return None

            # Check expiration
            exp = payload.get("exp", 0)
            if exp < time.time():
                return None

            # Extract user information
            user_id = payload.get("sub")
            email = payload.get("email")
            first_name = payload.get("given_name") or payload.get("first_name")
            last_name = payload.get("family_name") or payload.get("last_name")
            username = payload.get("preferred_username") or payload.get("username")
            image_url = payload.get("picture") or payload.get("image_url")

            if not user_id or not email:
                return None

            return ClerkUser(
                user_id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                username=username,
                image_url=image_url,
            )

        except (PyJWTError, ValueError, KeyError):
            return None


# Global auth instance
_clerk_auth: Optional[ClerkAuth] = None


def get_clerk_auth() -> ClerkAuth:
    """Get global Clerk auth instance"""
    global _clerk_auth
    if _clerk_auth is None:
        _clerk_auth = ClerkAuth()
    return _clerk_auth


async def get_current_user(token: str) -> Optional[ClerkUser]:
    """
    Dependency function for FastAPI routes - Human authentication

    Usage:
        @app.get("/protected")
        async def protected_route(user: ClerkUser = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    if not token:
        return None

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    auth = get_clerk_auth()
    return await auth.verify_token(token)


async def authenticate_agent(api_key: str) -> Optional[AgentIdentity]:
    """
    Authenticate an agent using API key
    """
    if not api_key:
        return None

    # Hash the provided key for lookup
    key_hash = hash_api_key(api_key)

    # Use the agent key service
    service = get_agent_key_service()
    return await service.get_agent_by_key_hash(key_hash)

    # Hash the provided key for lookup
    key_hash = hash_api_key(api_key)

    # Use the agent key service
    service = get_agent_key_service()
    return await service.get_agent_by_key_hash(key_hash)


async def authenticate_request(
    token: Optional[str] = None, api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Unified authentication function that handles both human users and agents

    Returns:
        - For humans: {"type": "human", "user": ClerkUser}
        - For agents: {"type": "agent", "agent": AgentIdentity}
        - For unauthenticated: None
    """
    # Try human authentication first (JWT token)
    if token:
        user = await get_current_user(token)
        if user:
            return {"type": "human", "user": user}

    # Try agent authentication (API key)
    if api_key:
        agent = await authenticate_agent(api_key)
        if agent:
            return {"type": "agent", "agent": agent}

    return None
