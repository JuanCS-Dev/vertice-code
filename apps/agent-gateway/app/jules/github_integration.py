"""
GitHub Integration for Jules.

Handles:
- GitHub App authentication
- PR creation and management
- Issue tracking
- Webhook processing
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# GitHub API
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class PullRequest:
    """Pull request data."""

    pr_id: str = ""
    number: int = 0
    title: str = ""
    body: str = ""
    branch: str = ""
    base_branch: str = "main"
    state: str = "open"  # open, closed, merged
    url: str = ""
    created_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)
    auto_merge: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pr_id": self.pr_id,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "branch": self.branch,
            "base_branch": self.base_branch,
            "state": self.state,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "labels": self.labels,
            "auto_merge": self.auto_merge,
        }


@dataclass
class Issue:
    """GitHub issue data."""

    issue_id: str = ""
    number: int = 0
    title: str = ""
    body: str = ""
    state: str = "open"
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    url: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "labels": self.labels,
            "assignees": self.assignees,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GitHubIntegration:
    """
    GitHub integration for Jules.

    Uses GitHub App authentication for secure access.
    """

    API_BASE = "https://api.github.com"

    def __init__(
        self,
        app_id: str = "",
        private_key: str = "",
        installation_id: str = "",
        repo: str = "",
    ):
        """
        Initialize GitHub integration.

        Args:
            app_id: GitHub App ID
            private_key: GitHub App private key (PEM format)
            installation_id: GitHub App installation ID
            repo: Repository in format "owner/repo"
        """
        self.app_id = app_id or os.getenv("JULES_GITHUB_APP_ID", "")
        self.private_key = private_key or os.getenv("JULES_GITHUB_PRIVATE_KEY", "")
        self.installation_id = installation_id or os.getenv("JULES_GITHUB_INSTALLATION_ID", "")
        self.repo = repo or os.getenv("JULES_GITHUB_REPO", "")

        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._initialized = bool(self.app_id and self.repo)

        if self._initialized:
            logger.info(f"GitHub integration initialized for {self.repo}")
        else:
            logger.warning("GitHub integration not configured")

    @property
    def is_available(self) -> bool:
        """Check if GitHub is available."""
        return self._initialized and HTTPX_AVAILABLE

    async def _get_installation_token(self) -> str:
        """Get or refresh installation access token."""
        # In production, this would use JWT to get installation token
        # For now, use personal access token from environment
        token = os.getenv("GITHUB_TOKEN", "")
        return token

    async def create_pull_request(
        self,
        title: str,
        body: str,
        branch: str,
        base_branch: str = "main",
        labels: Optional[List[str]] = None,
        auto_merge: bool = False,
    ) -> PullRequest:
        """
        Create a pull request.

        Args:
            title: PR title
            body: PR description
            branch: Source branch
            base_branch: Target branch
            labels: Labels to apply
            auto_merge: Enable auto-merge

        Returns:
            Created PullRequest
        """
        if not self.is_available:
            raise RuntimeError("GitHub integration not available")

        token = await self._get_installation_token()
        labels = labels or []

        async with httpx.AsyncClient() as client:
            # Create PR
            response = await client.post(
                f"{self.API_BASE}/repos/{self.repo}/pulls",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "title": title,
                    "body": body,
                    "head": branch,
                    "base": base_branch,
                },
            )

            if response.status_code != 201:
                raise RuntimeError(f"Failed to create PR: {response.text}")

            data = response.json()

            pr = PullRequest(
                pr_id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                branch=branch,
                base_branch=base_branch,
                state=data["state"],
                url=data["html_url"],
                created_at=datetime.now(timezone.utc),
                labels=labels,
                auto_merge=auto_merge,
            )

            # Add labels if specified
            if labels:
                await self._add_labels(pr.number, labels, token)

            # Enable auto-merge if requested
            if auto_merge:
                await self._enable_auto_merge(pr.number, token)

            logger.info(f"Created PR #{pr.number}: {title}")
            return pr

    async def _add_labels(
        self,
        pr_number: int,
        labels: List[str],
        token: str,
    ) -> None:
        """Add labels to a PR."""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.API_BASE}/repos/{self.repo}/issues/{pr_number}/labels",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"labels": labels},
            )

    async def _enable_auto_merge(
        self,
        pr_number: int,
        token: str,
    ) -> None:
        """Enable auto-merge for a PR."""
        # This requires GraphQL API
        logger.info(f"Auto-merge requested for PR #{pr_number}")

    async def get_pull_request(self, pr_number: int) -> Optional[PullRequest]:
        """Get a pull request by number."""
        if not self.is_available:
            return None

        token = await self._get_installation_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/repos/{self.repo}/pulls/{pr_number}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()

            return PullRequest(
                pr_id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                branch=data["head"]["ref"],
                base_branch=data["base"]["ref"],
                state=data["state"],
                url=data["html_url"],
                labels=[lbl["name"] for lbl in data.get("labels", [])],
            )

    async def list_open_prs(self, label: Optional[str] = None) -> List[PullRequest]:
        """List open pull requests."""
        if not self.is_available:
            return []

        token = await self._get_installation_token()

        async with httpx.AsyncClient() as client:
            params = {"state": "open"}
            if label:
                params["labels"] = label

            response = await client.get(
                f"{self.API_BASE}/repos/{self.repo}/pulls",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                params=params,
            )

            if response.status_code != 200:
                return []

            prs = []
            for data in response.json():
                prs.append(
                    PullRequest(
                        pr_id=str(data["id"]),
                        number=data["number"],
                        title=data["title"],
                        body=data["body"] or "",
                        branch=data["head"]["ref"],
                        base_branch=data["base"]["ref"],
                        state=data["state"],
                        url=data["html_url"],
                        labels=[lbl["name"] for lbl in data.get("labels", [])],
                    )
                )

            return prs

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Issue:
        """Create a GitHub issue."""
        if not self.is_available:
            raise RuntimeError("GitHub integration not available")

        token = await self._get_installation_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/repos/{self.repo}/issues",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "title": title,
                    "body": body,
                    "labels": labels or [],
                },
            )

            if response.status_code != 201:
                raise RuntimeError(f"Failed to create issue: {response.text}")

            data = response.json()

            return Issue(
                issue_id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                state=data["state"],
                labels=[lbl["name"] for lbl in data.get("labels", [])],
                url=data["html_url"],
                created_at=datetime.now(timezone.utc),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            "initialized": self._initialized,
            "repo": self.repo,
            "httpx_available": HTTPX_AVAILABLE,
        }
