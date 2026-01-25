"""
JulesClient - Google Jules API Client.

Implements polling-based interaction with Jules AI coding agent.
Follows VerticeClient patterns for consistency.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from vertice_core.core.types import ModelInfo
from vertice_core.types.jules_types import (
    JulesActivity,
    JulesActivityType,
    JulesConfig,
    JulesPlan,
    JulesPlanStep,
    JulesSession,
    JulesSessionState,
    JulesSource,
)
from vertice_core.providers.base import EnhancedProviderBase
from vertice_core.providers.types import CostTier, SpeedTier
from typing import AsyncGenerator


logger = logging.getLogger(__name__)


class JulesProvider(EnhancedProviderBase):
    """
    Jules AI Provider.
    """

    PROVIDER_NAME = "jules"
    BASE_URL = "https://jules.googleapis.com/v1alpha"
    COST_TIER = CostTier.FREE
    SPEED_TIER = SpeedTier.SLOW

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "jules-v1",
        timeout: float = 300.0,
        max_retries: int = 2,
    ):
        """Initialize Jules provider."""
        super().__init__(
            api_key=api_key or os.getenv("JULES_API_KEY"),
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.client = JulesClient(JulesConfig(api_key=self.api_key, timeout=self.timeout))

    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self.client.is_available

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Generate a response from a Jules session."""
        prompt = messages[-1]["content"]
        session = await self.client.create_session(prompt=prompt)
        # This is a simplified interaction; a real one would stream activities
        # and wait for a completion state.
        # For now, we'll just return a message indicating the session was created.
        return f"Jules session created: {session.session_id}"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream responses from a Jules session."""
        prompt = messages[-1]["content"]
        session = await self.client.create_session(prompt=prompt)
        async for activity in self.client.stream_activities(session.session_id):
            yield activity.message

    def get_model_info(self) -> ModelInfo:
        """Get model information for Jules."""
        return ModelInfo(
            model=self.model_name,
            provider=self.PROVIDER_NAME,
            cost_tier=self.COST_TIER.value,
            speed_tier=self.SPEED_TIER.value,
            supports_streaming=True,
        )


class JulesClientError(Exception):
    """Base exception for Jules client errors."""


class JulesAuthError(JulesClientError):
    """Authentication failed (401)."""


class JulesRateLimitError(JulesClientError):
    """Rate limit exceeded (429)."""

    def __init__(self, retry_after: Optional[int] = None) -> None:
        self.retry_after = retry_after
        msg = f"Rate limit exceeded, retry after {retry_after}s" if retry_after else "Rate limited"
        super().__init__(msg)


class JulesSessionError(JulesClientError):
    """Session-specific error (not found, invalid state)."""


class JulesClient:
    """
    Google Jules API Client with polling-based session management.

    Features:
    - Session lifecycle management (create, poll, approve, message)
    - Activity streaming via polling
    - Retry logic with exponential backoff
    - Circuit breaker pattern

    Example:
        >>> config = JulesConfig(api_key="...")
        >>> client = JulesClient(config)
        >>> session = await client.create_session(
        ...     prompt="Implement dark mode",
        ...     source_context={"source": "sources/github/org/repo"}
        ... )
        >>> async for activity in client.stream_activities(session.session_id):
        ...     print(activity.message)
    """

    CIRCUIT_BREAKER_THRESHOLD = 5
    MAX_RETRIES = 3

    def __init__(self, config: Optional[JulesConfig] = None) -> None:
        """Initialize Jules client.

        Args:
            config: Jules configuration. If None, uses env vars.
        """
        if config is None:
            api_key = os.getenv("JULES_API_KEY", "")
            config = JulesConfig(api_key=api_key)

        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._failure_count = 0
        self._circuit_open = False
        self._seen_activities: Dict[str, set] = {}  # session_id -> seen activity_ids

    @property
    def is_available(self) -> bool:
        """Check if client is properly configured."""
        return bool(self.config.api_key) and not self._circuit_open

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "x-goog-api-key": self.config.api_key,
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state."""
        self._failure_count = 0
        self._circuit_open = False

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with retry logic."""
        if self._circuit_open:
            raise JulesClientError("Circuit breaker open - too many failures")

        session = await self._ensure_session()
        url = f"{self.config.base_url}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                async with session.request(method, url, json=data) as resp:
                    if resp.status == 200:
                        self._failure_count = 0
                        return await resp.json()
                    elif resp.status == 401:
                        raise JulesAuthError("Invalid API key")
                    elif resp.status == 404:
                        raise JulesSessionError("Resource not found")
                    elif resp.status == 429:
                        retry_after = resp.headers.get("Retry-After")
                        raise JulesRateLimitError(int(retry_after) if retry_after else 60)
                    else:
                        text = await resp.text()
                        raise JulesClientError(f"API error {resp.status}: {text}")

            except aiohttp.ClientError as e:
                self._failure_count += 1
                if self._failure_count >= self.CIRCUIT_BREAKER_THRESHOLD:
                    self._circuit_open = True
                    logger.error("Circuit breaker opened due to consecutive failures")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise JulesClientError(f"Connection failed: {e}")

        raise JulesClientError("Max retries exceeded")

    # =========================================================================
    # SOURCE MANAGEMENT
    # =========================================================================

    async def list_sources(self) -> List[JulesSource]:
        """List connected repository sources."""
        data = await self._request("GET", "/sources")
        return [
            JulesSource(
                id=s.get("name", s.get("id", "")),
                name=s.get("displayName", s.get("name", "")),
                provider=self._extract_provider(s.get("name", "")),
                url=s.get("url"),
            )
            for s in data.get("sources", [])
        ]

    def _extract_provider(self, source_name: str) -> str:
        """Extract provider from source name (e.g., sources/github/org/repo)."""
        parts = source_name.split("/")
        return parts[1] if len(parts) > 1 else "unknown"

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    async def create_session(
        self,
        prompt: str,
        source_context: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> JulesSession:
        """Create a new Jules session.

        Args:
            prompt: Task description for Jules
            source_context: Repository context with 'source' key
            title: Optional session title

        Returns:
            Created JulesSession
        """
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "requirePlanApproval": self.config.require_plan_approval,
        }

        if source_context:
            payload["sourceContext"] = source_context
        if title:
            payload["title"] = title

        data = await self._request("POST", "/sessions", payload)
        session = self._parse_session(data)

        # Initialize activity tracking for this session
        self._seen_activities[session.session_id] = set()

        return session

    async def get_session(self, session_id: str) -> JulesSession:
        """Get session details."""
        data = await self._request("GET", f"/sessions/{session_id}")
        return self._parse_session(data)

    async def list_sessions(self, page_size: int = 20) -> List[JulesSession]:
        """List recent sessions."""
        data = await self._request("GET", f"/sessions?pageSize={page_size}")
        return [self._parse_session(s) for s in data.get("sessions", [])]

    async def approve_plan(self, session_id: str) -> JulesSession:
        """Approve session plan to begin execution."""
        data = await self._request("POST", f"/sessions/{session_id}:approvePlan", {})
        return self._parse_session(data)

    async def send_message(self, session_id: str, message: str) -> JulesSession:
        """Send a message to an active session (v1alpha API)."""
        payload = {"prompt": message}
        data = await self._request("POST", f"/sessions/{session_id}:sendMessage", payload)
        return self._parse_session(data)

    # =========================================================================
    # ACTIVITY STREAMING (via polling)
    # =========================================================================

    async def get_activities(
        self,
        session_id: str,
        page_size: int = 50,
    ) -> List[JulesActivity]:
        """Get session activities."""
        data = await self._request("GET", f"/sessions/{session_id}/activities?pageSize={page_size}")
        return [self._parse_activity(a) for a in data.get("activities", [])]

    async def stream_activities(
        self,
        session_id: str,
        stop_on_complete: bool = True,
    ) -> AsyncIterator[JulesActivity]:
        """Stream activities via polling.

        Yields new activities as they arrive, until session completes.

        Args:
            session_id: Session to monitor
            stop_on_complete: Stop when session completes

        Yields:
            JulesActivity events
        """
        if session_id not in self._seen_activities:
            self._seen_activities[session_id] = set()

        seen_ids = self._seen_activities[session_id]
        poll_count = 0

        while poll_count < self.config.max_poll_attempts:
            try:
                activities = await self.get_activities(session_id)

                # Yield new activities (sorted by timestamp)
                new_activities = [a for a in activities if a.activity_id not in seen_ids]
                new_activities.sort(key=lambda a: a.timestamp)

                for activity in new_activities:
                    seen_ids.add(activity.activity_id)
                    yield activity

                    # Check for completion activity
                    if stop_on_complete and activity.type in (
                        JulesActivityType.SESSION_COMPLETED,
                        JulesActivityType.SESSION_FAILED,
                    ):
                        return

                # Check session state
                session = await self.get_session(session_id)
                if stop_on_complete and session.state in (
                    JulesSessionState.COMPLETED,
                    JulesSessionState.FAILED,
                ):
                    return

            except JulesRateLimitError as e:
                logger.warning(f"Rate limited, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after or 60)
            except JulesClientError as e:
                logger.warning(f"Poll error: {e}")

            poll_count += 1
            await asyncio.sleep(self.config.poll_interval)

        logger.warning(f"Max poll attempts ({self.config.max_poll_attempts}) reached")

    # =========================================================================
    # PARSING HELPERS
    # =========================================================================

    def _parse_session(self, data: Dict[str, Any]) -> JulesSession:
        """Parse API response into JulesSession (v1alpha schema)."""
        plan_data = data.get("plan")
        plan = None
        if plan_data:
            steps = [
                JulesPlanStep(
                    step_id=s.get("id", str(i)),
                    index=s.get("index", i),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                )
                for i, s in enumerate(plan_data.get("steps", []))
            ]
            plan = JulesPlan(
                plan_id=plan_data.get("id", ""),
                steps=steps,
                estimated_duration=plan_data.get("estimatedDuration"),
                files_to_modify=plan_data.get("filesToModify", []),
                files_to_create=plan_data.get("filesToCreate", []),
                raw_content=plan_data.get("rawContent", ""),
            )

        # Parse timestamps
        created_str = data.get("createTime", data.get("createdAt"))
        updated_str = data.get("updateTime", data.get("updatedAt"))
        now = datetime.now()

        # Extract result URL from outputs.pullRequest.url
        result_url = None
        outputs = data.get("outputs", [])
        if outputs:
            for output in outputs:
                pr = output.get("pullRequest")
                if pr:
                    result_url = pr.get("url")
                    break
        # Fallback to legacy fields
        if not result_url:
            result_url = data.get("resultUrl", data.get("pullRequestUrl"))

        return JulesSession(
            session_id=data.get("name", data.get("id", "")),
            state=JulesSessionState(data.get("state", "QUEUED")),
            title=data.get("title", ""),
            prompt=data.get("prompt", ""),
            created_at=self._parse_timestamp(created_str) if created_str else now,
            updated_at=self._parse_timestamp(updated_str) if updated_str else now,
            url=data.get("url", ""),
            plan=plan,
            source_context=data.get("sourceContext"),
            result_url=result_url,
            error_message=data.get("errorMessage", data.get("error", {}).get("message")),
        )

    def _parse_activity(self, data: Dict[str, Any]) -> JulesActivity:
        """Parse API response into JulesActivity (v1alpha schema).

        The Jules API uses exactly ONE event type field per activity:
        - planGenerated: { plan: Plan }
        - planApproved: { planId: string }
        - progressUpdated: { title, description }
        - sessionCompleted: {}
        - sessionFailed: { reason: string }
        - userMessaged: { userMessage: string }
        - agentMessaged: { agentMessage: string }
        """
        timestamp_str = data.get("createTime", data.get("timestamp"))
        activity_type, message, activity_data = self._extract_activity_info(data)

        return JulesActivity(
            activity_id=data.get("name", data.get("id", "")),
            type=activity_type,
            timestamp=self._parse_timestamp(timestamp_str) if timestamp_str else datetime.now(),
            originator=data.get("originator", ""),
            description=data.get("description", ""),
            data=activity_data,
            message=message,
        )

    def _extract_activity_info(
        self, data: Dict[str, Any]
    ) -> tuple[JulesActivityType, str, Dict[str, Any]]:
        """Extract activity type, message, and data from API response (v1alpha).

        Official API activity types:
        - planGenerated: { plan: Plan }
        - planApproved: { planId: string }
        - progressUpdated: { title, description }
        - sessionCompleted: {}
        - sessionFailed: { reason: string }
        - userMessaged: { userMessage: string }
        - agentMessaged: { agentMessage: string }

        Returns:
            Tuple of (activity_type, message, data)
        """
        # planGenerated: { plan: Plan }
        if "planGenerated" in data:
            plan_data = data["planGenerated"]
            plan = plan_data.get("plan", {})
            steps = plan.get("steps", [])
            if steps:
                first_step = steps[0].get("title", "Plan generated")
                message = (
                    f"Plan: {first_step[:100]}..."
                    if len(first_step) > 100
                    else f"Plan: {first_step}"
                )
            else:
                message = "Plan generated"
            return JulesActivityType.PLAN_GENERATED, message, plan_data

        # planApproved: { planId: string }
        if "planApproved" in data:
            plan_id = data["planApproved"].get("planId", "")
            return (
                JulesActivityType.PLAN_APPROVED,
                f"Plan approved: {plan_id}" if plan_id else "Plan approved",
                data.get("planApproved", {}),
            )

        # progressUpdated: { title, description }
        if "progressUpdated" in data:
            progress = data["progressUpdated"]
            title = progress.get("title", "")
            description = progress.get("description", "")
            message = title or description or "Processing..."
            return JulesActivityType.PROGRESS_UPDATED, message, progress

        # sessionCompleted: {}
        if "sessionCompleted" in data:
            return (
                JulesActivityType.SESSION_COMPLETED,
                "Session completed",
                data.get("sessionCompleted", {}),
            )

        # sessionFailed: { reason: string }
        if "sessionFailed" in data:
            failed = data["sessionFailed"]
            reason = failed.get("reason", "Session failed")
            return JulesActivityType.SESSION_FAILED, reason, failed

        # userMessaged: { userMessage: string }
        if "userMessaged" in data:
            msg_data = data["userMessaged"]
            text = msg_data.get("userMessage", "")
            return JulesActivityType.USER_MESSAGED, text or "User message", msg_data

        # agentMessaged: { agentMessage: string }
        if "agentMessaged" in data:
            msg_data = data["agentMessaged"]
            text = msg_data.get("agentMessage", "")
            return JulesActivityType.AGENT_MESSAGED, text or "Agent message", msg_data

        # Fallback: check for generic type field (legacy compatibility)
        if "type" in data:
            type_str = data["type"]
            type_map = {
                "planGenerated": JulesActivityType.PLAN_GENERATED,
                "planApproved": JulesActivityType.PLAN_APPROVED,
                "progressUpdated": JulesActivityType.PROGRESS_UPDATED,
                "sessionCompleted": JulesActivityType.SESSION_COMPLETED,
                "sessionFailed": JulesActivityType.SESSION_FAILED,
                "userMessaged": JulesActivityType.USER_MESSAGED,
                "agentMessaged": JulesActivityType.AGENT_MESSAGED,
            }
            activity_type = type_map.get(type_str, JulesActivityType.PROGRESS_UPDATED)
            message = data.get("message", data.get("text", str(type_str)))
            return activity_type, message, data

        # Unknown activity type - use originator info
        originator = data.get("originator", "unknown")
        return JulesActivityType.PROGRESS_UPDATED, f"Activity from {originator}", data

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp string."""
        try:
            # Handle various formats
            timestamp_str = timestamp_str.replace("Z", "+00:00")
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            return datetime.now()


# Factory function
_default_client: Optional[JulesClient] = None


def get_jules_client(config: Optional[JulesConfig] = None) -> JulesClient:
    """Get or create default Jules client."""
    global _default_client
    if config is not None:
        return JulesClient(config)
    if _default_client is None:
        _default_client = JulesClient()
    return _default_client


__all__ = [
    "JulesClient",
    "JulesClientError",
    "JulesAuthError",
    "JulesRateLimitError",
    "JulesSessionError",
    "get_jules_client",
]
