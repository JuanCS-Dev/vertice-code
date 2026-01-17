"""
Agent API Key Management Service
Handles creation, rotation, and management of agent API keys
"""

import time
from typing import Optional, Dict, Any, List
import uuid

from app.core.auth_utils import generate_agent_api_key, hash_api_key, AgentIdentity


class AgentKeyService:
    """Service for managing agent API keys"""

    def __init__(self):
        # In production, this would be a database connection
        self._mock_storage: Dict[str, Dict[str, Any]] = {}

    async def create_agent_key(
        self,
        workspace_id: str,
        agent_name: str,
        scopes: Optional[List[str]] = None,
        daily_budget_cents: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create a new API key for an agent

        Returns:
            {
                "agent_id": "agent-uuid",
                "api_key": "raw-key-for-onetime-return",
                "key_hash": "hashed-key-for-storage",
                "agent_identity": AgentIdentity
            }
        """
        # Generate unique agent ID
        agent_id = f"agent-{uuid.uuid4().hex[:16]}"

        # Generate API key
        raw_api_key = generate_agent_api_key()
        key_hash = hash_api_key(raw_api_key)

        # Create agent identity
        agent_identity = AgentIdentity(
            agent_id=agent_id,
            workspace_id=workspace_id,
            agent_name=agent_name,
            scopes=scopes or ["read:memory", "write:logs"],
            daily_budget_cents=daily_budget_cents,
        )

        # Store in mock database (in production: PostgreSQL)
        self._mock_storage[key_hash] = {
            "agent_id": agent_id,
            "workspace_id": workspace_id,
            "agent_name": agent_name,
            "key_hash": key_hash,
            "scopes": agent_identity.scopes,
            "daily_budget_cents": daily_budget_cents,
            "created_at": agent_identity.created_at,
            "is_active": True,
        }

        return {
            "agent_id": agent_id,
            "api_key": raw_api_key,  # Only returned once!
            "key_hash": key_hash,
            "agent_identity": agent_identity,
        }

    async def list_agent_keys(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all active agent keys for a workspace
        Never returns the actual API keys, only metadata
        """
        keys = []
        for key_hash, data in self._mock_storage.items():
            if data["workspace_id"] == workspace_id and data["is_active"]:
                keys.append(
                    {
                        "agent_id": data["agent_id"],
                        "agent_name": data["agent_name"],
                        "scopes": data["scopes"],
                        "daily_budget_cents": data["daily_budget_cents"],
                        "created_at": data["created_at"],
                    }
                )
        return keys

    async def rotate_agent_key(self, agent_id: str, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Rotate an agent's API key (invalidate old, create new)
        """
        # Find existing agent
        for key_hash, data in self._mock_storage.items():
            if (
                data["agent_id"] == agent_id
                and data["workspace_id"] == workspace_id
                and data["is_active"]
            ):
                # Mark old key as inactive
                data["is_active"] = False
                data["rotated_at"] = time.time()

                # Create new key with same properties
                return await self.create_agent_key(
                    workspace_id=workspace_id,
                    agent_name=data["agent_name"],
                    scopes=data["scopes"],
                    daily_budget_cents=data["daily_budget_cents"],
                )

        return None

    async def revoke_agent_key(self, agent_id: str, workspace_id: str) -> bool:
        """Revoke an agent's API key"""
        for key_hash, data in self._mock_storage.items():
            if data["agent_id"] == agent_id and data["workspace_id"] == workspace_id:
                data["is_active"] = False
                data["revoked_at"] = time.time()
                return True
        return False

    async def get_agent_by_key_hash(self, key_hash: str) -> Optional[AgentIdentity]:
        """Get agent identity by key hash"""
        if key_hash in self._mock_storage:
            data = self._mock_storage[key_hash]
            if data["is_active"]:
                return AgentIdentity(
                    agent_id=data["agent_id"],
                    workspace_id=data["workspace_id"],
                    agent_name=data["agent_name"],
                    scopes=data["scopes"],
                    daily_budget_cents=data["daily_budget_cents"],
                    created_at=data["created_at"],
                )
        return None


# Global service instance
_agent_key_service: Optional[AgentKeyService] = None


def get_agent_key_service() -> AgentKeyService:
    """Get global agent key service instance"""
    global _agent_key_service
    if _agent_key_service is None:
        _agent_key_service = AgentKeyService()
    return _agent_key_service
