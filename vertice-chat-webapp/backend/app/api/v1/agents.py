"""
Agent API Key Management Endpoints
REST API for creating, managing, and rotating agent API keys
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.auth import ClerkUser, get_current_user, authenticate_request
from app.core.agent_auth import get_agent_key_service

router = APIRouter()


class CreateAgentKeyRequest(BaseModel):
    agent_name: str
    scopes: Optional[List[str]] = None
    daily_budget_cents: Optional[int] = 1000


class AgentKeyResponse(BaseModel):
    agent_id: str
    agent_name: str
    scopes: List[str]
    daily_budget_cents: int
    created_at: float


class AgentKeyWithSecretResponse(BaseModel):
    agent_id: str
    api_key: str  # Only returned on creation!
    agent_name: str
    scopes: List[str]
    daily_budget_cents: int
    created_at: float


@router.post("/agents/keys", response_model=AgentKeyWithSecretResponse)
async def create_agent_key(
    request: CreateAgentKeyRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Create a new API key for an agent

    **Important:** The raw API key is only returned once on creation.
    Store it securely as it cannot be retrieved later.
    """
    # Authenticate user (only humans can create agent keys)
    auth_result = await authenticate_request(token=authorization, api_key=x_api_key)
    if not auth_result or auth_result["type"] != "human":
        raise HTTPException(status_code=401, detail="Authentication required")

    user: ClerkUser = auth_result["user"]

    # For now, use user_id as workspace_id (in production, this would be more complex)
    workspace_id = user.user_id

    # Create the agent key
    service = get_agent_key_service()
    result = await service.create_agent_key(
        workspace_id=workspace_id,
        agent_name=request.agent_name,
        scopes=request.scopes,
        daily_budget_cents=request.daily_budget_cents or 1000,
    )

    return AgentKeyWithSecretResponse(
        agent_id=result["agent_id"],
        api_key=result["api_key"],  # Only returned once!
        agent_name=request.agent_name,
        scopes=result["agent_identity"].scopes,
        daily_budget_cents=result["agent_identity"].daily_budget_cents,
        created_at=result["agent_identity"].created_at,
    )


@router.get("/agents/keys", response_model=List[AgentKeyResponse])
async def list_agent_keys(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    List all agent API keys for the authenticated user/workspace
    """
    # Authenticate user or agent
    auth_result = await authenticate_request(token=authorization, api_key=x_api_key)
    if not auth_result:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Determine workspace based on auth type
    if auth_result["type"] == "human":
        user: ClerkUser = auth_result["user"]
        workspace_id = user.user_id
    elif auth_result["type"] == "agent":
        agent = auth_result["agent"]
        workspace_id = agent.workspace_id
    else:
        raise HTTPException(status_code=401, detail="Invalid authentication type")

    # List agent keys
    service = get_agent_key_service()
    keys = await service.list_agent_keys(workspace_id)

    return [
        AgentKeyResponse(
            agent_id=key["agent_id"],
            agent_name=key["agent_name"],
            scopes=key["scopes"],
            daily_budget_cents=key["daily_budget_cents"],
            created_at=key["created_at"],
        )
        for key in keys
    ]


@router.post("/agents/keys/{agent_id}/rotate")
async def rotate_agent_key(
    agent_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Rotate an agent's API key (invalidate old, create new)

    Returns the new API key - store it securely as it cannot be retrieved later.
    """
    # Authenticate user
    auth_result = await authenticate_request(token=authorization, api_key=x_api_key)
    if not auth_result or auth_result["type"] != "human":
        raise HTTPException(status_code=401, detail="Authentication required")

    user: ClerkUser = auth_result["user"]
    workspace_id = user.user_id

    # Rotate the key
    service = get_agent_key_service()
    result = await service.rotate_agent_key(agent_id, workspace_id)

    if not result:
        raise HTTPException(status_code=404, detail="Agent key not found")

    return AgentKeyWithSecretResponse(
        agent_id=result["agent_id"],
        api_key=result["api_key"],  # Only returned once!
        agent_name=result["agent_identity"].agent_name,
        scopes=result["agent_identity"].scopes,
        daily_budget_cents=result["agent_identity"].daily_budget_cents,
        created_at=result["agent_identity"].created_at,
    )


@router.delete("/agents/keys/{agent_id}")
async def revoke_agent_key(
    agent_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Revoke an agent's API key permanently
    """
    # Authenticate user
    auth_result = await authenticate_request(token=authorization, api_key=x_api_key)
    if not auth_result or auth_result["type"] != "human":
        raise HTTPException(status_code=401, detail="Authentication required")

    user: ClerkUser = auth_result["user"]
    workspace_id = user.user_id

    # Revoke the key
    service = get_agent_key_service()
    success = await service.revoke_agent_key(agent_id, workspace_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent key not found")

    return {"message": "Agent key revoked successfully"}
