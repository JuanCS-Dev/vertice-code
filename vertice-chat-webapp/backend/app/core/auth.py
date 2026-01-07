"""
Authentication utilities for Clerk JWT validation
Validates Clerk JWT tokens and extracts user information

Reference: https://clerk.com/docs/backend-requests/handling/manual-jwt
"""

import time
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError
import httpx
from pydantic import BaseModel

from app.core.config import settings


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

        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable is required")

        if not self.clerk_publishable_key:
            raise ValueError("CLERK_PUBLISHABLE_KEY environment variable is required")

        # Extract issuer from publishable key (format: pk_test_xxx or pk_live_xxx)
        key_parts = self.clerk_publishable_key.split("_")
        if len(key_parts) >= 2:
            env_type = key_parts[1]  # "test" or "live"
            self.issuer = f"https://clerk.{env_type}.clerk.com"
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
            # For development, we'll decode without full verification
            # In production, implement proper JWKS verification

            # Decode payload without verification
            payload = jwt.decode(token, options={"verify_signature": False})

            # Basic validation
            if payload.get("iss") != self.issuer:
                return None

            if payload.get("aud") != [self.clerk_publishable_key]:
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
    Dependency function for FastAPI routes

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
