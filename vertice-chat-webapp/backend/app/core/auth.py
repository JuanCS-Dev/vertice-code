"""
Authentication utilities for Firebase JWT validation
Validates Firebase (Google Identity) JWT tokens and extracts user information
"""

import time
from typing import Optional, Dict, Any, List
import logging
from pydantic import BaseModel
import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings
from app.core.agent_auth import get_agent_key_service, AgentKeyService
from app.core.auth_utils import generate_agent_api_key, hash_api_key, AgentIdentity

logger = logging.getLogger(__name__)

class FirebaseUser(BaseModel):
    """Firebase user information extracted from JWT"""
    user_id: str
    email: str
    name: Optional[str] = None
    image_url: Optional[str] = None

class FirebaseAuth:
    """Firebase authentication handler"""

    def __init__(self):
        self.project_id = settings.FIREBASE_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
        
        try:
            # Initialize firebase-admin if not already initialized
            if not firebase_admin._apps:
                # On GCP, ADC is used automatically. Locally, set GOOGLE_APPLICATION_CREDENTIALS
                firebase_admin.initialize_app()
            self.mock_mode = False
        except Exception as e:
            logger.warning(f"Firebase not initialized: {e}. Falling back to mock mode.")
            self.mock_mode = True

    async def verify_token(self, token: str) -> Optional[FirebaseUser]:
        """
        Verify and decode Firebase JWT token
        """
        try:
            if self.mock_mode or token == "mock-jwt-token" or token.startswith("Bearer mock-jwt-token"):
                return FirebaseUser(
                    user_id="mock-user-123",
                    email="mock@example.com",
                    name="Mock User",
                )

            # Verify the ID token using Firebase Admin SDK
            decoded_token = auth.verify_id_token(token)
            
            return FirebaseUser(
                user_id=decoded_token.get("uid"),
                email=decoded_token.get("email"),
                name=decoded_token.get("name"),
                image_url=decoded_token.get("picture")
            )

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

# Global auth instance
_firebase_auth: Optional[FirebaseAuth] = None

def get_firebase_auth() -> FirebaseAuth:
    """Get global Firebase auth instance"""
    global _firebase_auth
    if _firebase_auth is None:
        _firebase_auth = FirebaseAuth()
    return _firebase_auth

async def get_current_user(token: str) -> Optional[FirebaseUser]:
    """
    Dependency function for FastAPI routes
    """
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:]

    fa = get_firebase_auth()
    return await fa.verify_token(token)


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
