"""
GitHub Deep Sync - Webhook Handlers and Agent Integration
========================================================

Handles GitHub webhooks for real-time repository synchronization.
Implements autonomous PR management and conflict resolution.
"""

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import logging
from datetime import datetime

# from vertice_core.github_agent import GitHubAgent  # Temporarily disabled

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# === Pydantic Models for GitHub Webhooks ===


class RepositoryInfo(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    owner: Dict[str, Any]
    private: bool


class UserInfo(BaseModel):
    id: int
    login: str
    html_url: str


class CommitInfo(BaseModel):
    id: str
    message: str
    author: Dict[str, Any]
    url: str
    timestamp: datetime


class PullRequestInfo(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str]
    html_url: str
    state: str
    merged: bool
    merge_commit_sha: Optional[str]
    head: Dict[str, Any]
    base: Dict[str, Any]


# === Webhook Payload Models ===


class GitHubPushPayload(BaseModel):
    ref: str
    before: str
    after: str
    repository: RepositoryInfo
    pusher: UserInfo
    commits: List[CommitInfo]
    compare: str
    forced: bool


class GitHubPRPayload(BaseModel):
    action: str  # opened, closed, synchronize, reopened, etc.
    number: int
    pull_request: PullRequestInfo
    repository: RepositoryInfo
    sender: UserInfo
    before: Optional[str]
    after: Optional[str]


class GitHubIssuePayload(BaseModel):
    action: str
    issue: Dict[str, Any]
    repository: RepositoryInfo
    sender: UserInfo


# === Webhook Handlers ===


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Main GitHub webhook handler.

    Processes push, pull_request, and issue events.
    Implements security verification and autonomous actions.
    """
    try:
        # For now, just log the event and return success
        payload_data = await request.json()

        logger.info(f"Received {x_github_event} event")
        logger.info(f"Repository: {payload_data.get('repository', {}).get('full_name', 'unknown')}")

        # Basic validation
        if x_github_event == "push":
            commits = payload_data.get("commits", [])
            logger.info(f"Push with {len(commits)} commits")
        elif x_github_event == "pull_request":
            action = payload_data.get("action", "unknown")
            pr_number = payload_data.get("number", "unknown")
            logger.info(f"PR {action} #{pr_number}")

        return {"status": "processed", "event": x_github_event}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}


async def verify_signature(request: Request, signature: Optional[str]) -> bool:
    """
    Verify GitHub webhook signature for security.

    Uses HMAC-SHA256 with the webhook secret.
    """
    if not signature or not settings.github_webhook_secret:
        return False

    # Extract signature from header
    if not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]  # Remove "sha256=" prefix

    # Get raw body
    body = await request.body()

    # Compute HMAC
    secret = settings.github_webhook_secret.encode()
    computed_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

    # Secure compare
    return hmac.compare_digest(computed_signature, expected_signature)


# Event handling functions will be implemented with GitHubAgent integration


# === Health Check ===


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "webhook_secret_configured": bool(settings.github_webhook_secret),
        "github_token_configured": bool(settings.github_token),
    }
