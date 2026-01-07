"""
Shared authentication utilities
Contains functions used by both human and agent authentication
"""

import hashlib
import secrets
import time
from typing import List, Optional
from pydantic import BaseModel


def generate_agent_api_key() -> str:
    """Generate a secure API key for an agent"""
    # Generate a random 32-byte key and encode as hex
    key_bytes = secrets.token_bytes(32)
    return key_bytes.hex()


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class AgentIdentity(BaseModel):
    """Agent identity information for machine-to-machine authentication"""

    agent_id: str
    workspace_id: str
    agent_name: str
    scopes: List[str] = ["read:memory", "write:logs"]
    daily_budget_cents: int = 1000
    created_at: Optional[float] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = time.time()

    def can_access_scope(self, scope: str) -> bool:
        """Check if agent has access to a specific scope"""
        return scope in self.scopes

    def has_budget_remaining(self, spent_cents: int) -> bool:
        """Check if agent has remaining daily budget"""
        return spent_cents < self.daily_budget_cents
