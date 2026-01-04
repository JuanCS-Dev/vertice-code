"""
JulesAgent - Google Jules AI Agent Wrapper.

Integrates Jules as a Vertice agent that can be invoked like others.
Streams progress updates as StreamingChunks.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Callable, Coroutine, List, Optional

from vertice_cli.agents.base import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
)
from vertice_cli.agents.protocol import (
    StreamingChunk,
    StreamingChunkType,
)
from vertice_core.types.jules_types import (
    JulesActivity,
    JulesActivityType,
    JulesConfig,
    JulesSession,
    JulesSessionState,
)
from vertice_cli.core.providers.jules_provider import JulesClient, get_jules_client

logger = logging.getLogger(__name__)

# Type alias for plan approval callback
PlanApprovalCallback = Callable[[JulesSession], Coroutine[Any, Any, bool]]


class JulesAgent(BaseAgent):
    """
    Vertice Agent wrapper for Google Jules.

    Capabilities:
    - Create coding tasks on connected repos
    - Monitor session progress with streaming
    - Approve execution plans (via callback)
    - Send messages to active sessions

    Usage:
        agent = JulesAgent(jules_client=client)
        async for chunk in agent.execute_streaming(task):
            print(chunk)

    Integration:
        - Register in AGENT_REGISTRY with role="JULES"
        - Invokable via AgentManager.invoke("jules", prompt)
        - Streams JulesActivity as StreamingChunk
    """

    def __init__(
        self,
        jules_client: Optional[JulesClient] = None,
        llm_client: Any = None,
        mcp_client: Any = None,
        config: Optional[JulesConfig] = None,
    ) -> None:
        """Initialize Jules agent.

        Args:
            jules_client: Jules API client (creates default if None)
            llm_client: LLM client (not used, for interface compatibility)
            mcp_client: MCP client (not used, for interface compatibility)
            config: Jules configuration override
        """
        super().__init__(
            role=AgentRole.EXECUTOR,  # Jules executes coding tasks
            capabilities=[
                AgentCapability.FILE_EDIT,
                AgentCapability.GIT_OPS,
                AgentCapability.READ_ONLY,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="Jules Agent - Google AI Coding Agent",
        )

        self.jules_client = jules_client or get_jules_client(config)
        self._active_session: Optional[JulesSession] = None
        self._plan_approval_callback: Optional[PlanApprovalCallback] = None

    def set_plan_approval_callback(self, callback: PlanApprovalCallback) -> None:
        """Set callback for plan approval UI.

        The callback receives JulesSession and should return True to approve.
        """
        self._plan_approval_callback = callback

    @property
    def active_session(self) -> Optional[JulesSession]:
        """Get current active session."""
        return self._active_session

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute task synchronously (collects all output)."""
        chunks: List[str] = []
        final_session: Optional[JulesSession] = None

        async for chunk in self.execute_streaming(task):
            if isinstance(chunk, StreamingChunk):
                chunks.append(str(chunk))
            else:
                chunks.append(str(chunk))

        final_session = self._active_session

        return AgentResponse(
            success=(
                final_session is not None
                and final_session.state == JulesSessionState.COMPLETED
            ),
            data={
                "output": "".join(chunks),
                "session_id": final_session.session_id if final_session else None,
                "result_url": final_session.result_url if final_session else None,
                "state": final_session.state.value if final_session else None,
            },
            reasoning="Jules session completed" if final_session else "No session",
        )

    async def execute_streaming(
        self,
        task: AgentTask,
    ) -> AsyncIterator[StreamingChunk]:
        """Execute task with streaming progress updates.

        Args:
            task: Agent task containing the prompt

        Yields:
            StreamingChunk with progress updates

        Context keys:
            - source_context: Dict with 'source' key for repo
            - title: Optional session title
        """
        if not self.jules_client.is_available:
            yield StreamingChunk(
                type=StreamingChunkType.ERROR,
                data="Jules client not configured. Set JULES_API_KEY environment variable.",
            )
            return

        # Extract context
        prompt = task.request
        source_context = task.context.get("source_context")
        title = task.context.get("title")

        yield StreamingChunk(
            type=StreamingChunkType.STATUS,
            data=f"Creating Jules session: {prompt[:60]}{'...' if len(prompt) > 60 else ''}",
        )

        try:
            # Create session
            session = await self.jules_client.create_session(
                prompt=prompt,
                source_context=source_context,
                title=title,
            )
            self._active_session = session

            yield StreamingChunk(
                type=StreamingChunkType.STATUS,
                data=f"Session created: {session.session_id}",
                metadata={"session_id": session.session_id},
            )

            # Stream activities
            async for activity in self.jules_client.stream_activities(session.session_id):
                yield self._activity_to_chunk(activity)

                # Handle plan approval
                if activity.type == JulesActivityType.PLAN_GENERATED:
                    session = await self.jules_client.get_session(session.session_id)
                    self._active_session = session

                    if session.state == JulesSessionState.AWAITING_PLAN_APPROVAL:
                        yield StreamingChunk(
                            type=StreamingChunkType.STATUS,
                            data="Plan generated. Awaiting approval...",
                            metadata={"plan": session.plan.__dict__ if session.plan else {}},
                        )

                        approved = await self._handle_plan_approval(session)

                        if approved:
                            session = await self.jules_client.approve_plan(
                                session.session_id
                            )
                            self._active_session = session
                            yield StreamingChunk(
                                type=StreamingChunkType.STATUS,
                                data="Plan approved. Execution starting...",
                            )
                        else:
                            yield StreamingChunk(
                                type=StreamingChunkType.STATUS,
                                data="Plan not approved. Session cancelled.",
                            )
                            return

            # Final status
            session = await self.jules_client.get_session(session.session_id)
            self._active_session = session

            if session.state == JulesSessionState.COMPLETED:
                yield StreamingChunk(
                    type=StreamingChunkType.RESULT,
                    data={
                        "state": session.state.value,
                        "result_url": session.result_url,
                        "message": "Session completed successfully",
                    },
                )
            elif session.state == JulesSessionState.FAILED:
                yield StreamingChunk(
                    type=StreamingChunkType.ERROR,
                    data=session.error_message or "Session failed",
                )
            else:
                yield StreamingChunk(
                    type=StreamingChunkType.STATUS,
                    data=f"Session ended with state: {session.state.value}",
                )

        except Exception as e:
            logger.error(f"Jules execution failed: {e}", exc_info=True)
            yield StreamingChunk(
                type=StreamingChunkType.ERROR,
                data=f"Jules error: {str(e)}",
            )

    def _activity_to_chunk(self, activity: JulesActivity) -> StreamingChunk:
        """Convert Jules activity to streaming chunk (v1alpha types)."""
        type_map = {
            JulesActivityType.PLAN_GENERATED: StreamingChunkType.REASONING,
            JulesActivityType.PLAN_APPROVED: StreamingChunkType.STATUS,
            JulesActivityType.PROGRESS_UPDATED: StreamingChunkType.STATUS,
            JulesActivityType.SESSION_COMPLETED: StreamingChunkType.RESULT,
            JulesActivityType.SESSION_FAILED: StreamingChunkType.ERROR,
            JulesActivityType.USER_MESSAGED: StreamingChunkType.THINKING,
            JulesActivityType.AGENT_MESSAGED: StreamingChunkType.STATUS,
        }

        chunk_type = type_map.get(activity.type, StreamingChunkType.STATUS)

        # Format message - use activity.message (already extracted by parser)
        message = activity.message
        if not message and activity.description:
            message = activity.description
        if not message and activity.data:
            if "text" in activity.data:
                message = activity.data["text"]
            elif "agentMessage" in activity.data:
                message = activity.data["agentMessage"]
            elif "userMessage" in activity.data:
                message = activity.data["userMessage"]
            else:
                message = str(activity.data)[:200]

        return StreamingChunk(
            type=chunk_type,
            data=message or f"[{activity.type.value}]",
            metadata={
                "activity_id": activity.activity_id,
                "activity_type": activity.type.value,
                "originator": activity.originator,
                "timestamp": activity.timestamp.isoformat(),
            },
        )

    async def _handle_plan_approval(self, session: JulesSession) -> bool:
        """Handle plan approval flow.

        Returns True if plan is approved.
        """
        if self._plan_approval_callback:
            # Delegate to UI callback
            try:
                return await self._plan_approval_callback(session)
            except Exception as e:
                logger.error(f"Plan approval callback failed: {e}")
                return False

        # No callback = require manual approval via send_message
        logger.info(
            f"Plan awaiting approval for session {session.session_id}. "
            "Use approve_current_plan() or set a callback."
        )
        return False

    async def send_message(self, message: str) -> Optional[JulesSession]:
        """Send message to active session."""
        if not self._active_session:
            logger.warning("No active session to send message to")
            return None

        session = await self.jules_client.send_message(
            self._active_session.session_id, message
        )
        self._active_session = session
        return session

    async def approve_current_plan(self) -> Optional[JulesSession]:
        """Approve plan for active session."""
        if not self._active_session:
            logger.warning("No active session to approve")
            return None

        if self._active_session.state != JulesSessionState.AWAITING_PLAN_APPROVAL:
            logger.warning(
                f"Session not awaiting approval (state: {self._active_session.state})"
            )
            return None

        session = await self.jules_client.approve_plan(self._active_session.session_id)
        self._active_session = session
        return session

    async def get_session_status(self) -> Optional[JulesSession]:
        """Refresh and get current session status."""
        if not self._active_session:
            return None

        session = await self.jules_client.get_session(self._active_session.session_id)
        self._active_session = session
        return session


__all__ = ["JulesAgent"]
