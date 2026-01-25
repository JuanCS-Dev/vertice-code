"""
Unit tests for JulesAgent.

Tests agent functionality including:
- Streaming execution
- Activity conversion
- Plan approval flow
"""

from __future__ import annotations

from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertice_core.agents.jules_agent import JulesAgent
from vertice_core.agents.protocol import StreamingChunk, StreamingChunkType
from vertice_core.types import AgentTask
from vertice_core.types.jules_types import (
    JulesActivity,
    JulesActivityType,
    JulesPlan,
    JulesSession,
    JulesSessionState,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_jules_client() -> MagicMock:
    """Create mock Jules client."""
    client = MagicMock()
    client.is_available = True
    return client


@pytest.fixture
def jules_agent(mock_jules_client: MagicMock) -> JulesAgent:
    """Create JulesAgent with mock client."""
    return JulesAgent(jules_client=mock_jules_client)


@pytest.fixture
def sample_session() -> JulesSession:
    """Create sample session."""
    return JulesSession(
        session_id="session-123",
        state=JulesSessionState.PLANNING,
        title="Test Session",
        prompt="Test prompt",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        plan=JulesPlan(
            plan_id="plan-456",
            steps=[],
            files_to_modify=["app.py"],
            files_to_create=["feature.py"],
        ),
    )


@pytest.fixture
def sample_activities() -> List[JulesActivity]:
    """Create sample activities."""
    return [
        JulesActivity(
            activity_id="act-1",
            type=JulesActivityType.PROGRESS_UPDATED,
            timestamp=datetime.now(),
            message="Starting analysis...",
        ),
        JulesActivity(
            activity_id="act-2",
            type=JulesActivityType.PROGRESS_UPDATED,
            timestamp=datetime.now(),
            message="Created feature.py",
            data={"title": "Created feature.py"},
        ),
        JulesActivity(
            activity_id="act-3",
            type=JulesActivityType.SESSION_COMPLETED,
            timestamp=datetime.now(),
            message="Task completed successfully",
        ),
    ]


# =============================================================================
# TESTS - INITIALIZATION
# =============================================================================


class TestJulesAgentInit:
    """Test agent initialization."""

    def test_default_init(self) -> None:
        """Agent initializes with default client."""
        with patch("vertice_core.agents.jules_agent.get_jules_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.is_available = True
            mock_get_client.return_value = mock_client

            agent = JulesAgent()

            mock_get_client.assert_called_once()
            assert agent.jules_client is mock_client

    def test_custom_client(self, mock_jules_client: MagicMock) -> None:
        """Agent accepts custom client."""
        agent = JulesAgent(jules_client=mock_jules_client)

        assert agent.jules_client is mock_jules_client

    def test_plan_approval_callback(self, jules_agent: JulesAgent) -> None:
        """Agent accepts plan approval callback."""

        async def callback(session: JulesSession) -> bool:
            return True

        jules_agent.set_plan_approval_callback(callback)

        assert jules_agent._plan_approval_callback is callback


# =============================================================================
# TESTS - ACTIVITY CONVERSION
# =============================================================================


class TestActivityConversion:
    """Test activity to chunk conversion."""

    def test_progress_to_status(self, jules_agent: JulesAgent) -> None:
        """Progress activity becomes STATUS chunk."""
        activity = JulesActivity(
            activity_id="act-1",
            type=JulesActivityType.PROGRESS_UPDATED,
            timestamp=datetime.now(),
            message="Working on feature...",
        )

        chunk = jules_agent._activity_to_chunk(activity)

        assert chunk.type == StreamingChunkType.STATUS
        assert chunk.data == "Working on feature..."
        assert chunk.metadata["activity_type"] == "progressUpdated"

    def test_error_to_error(self, jules_agent: JulesAgent) -> None:
        """SessionFailed activity becomes ERROR chunk."""
        activity = JulesActivity(
            activity_id="act-2",
            type=JulesActivityType.SESSION_FAILED,
            timestamp=datetime.now(),
            message="Build failed",
        )

        chunk = jules_agent._activity_to_chunk(activity)

        assert chunk.type == StreamingChunkType.ERROR
        assert chunk.data == "Build failed"

    def test_plan_to_reasoning(self, jules_agent: JulesAgent) -> None:
        """Plan activity becomes REASONING chunk."""
        activity = JulesActivity(
            activity_id="act-3",
            type=JulesActivityType.PLAN_GENERATED,
            timestamp=datetime.now(),
            message="Generated execution plan",
        )

        chunk = jules_agent._activity_to_chunk(activity)

        assert chunk.type == StreamingChunkType.REASONING

    def test_completed_to_result(self, jules_agent: JulesAgent) -> None:
        """Completed activity becomes RESULT chunk."""
        activity = JulesActivity(
            activity_id="act-4",
            type=JulesActivityType.SESSION_COMPLETED,
            timestamp=datetime.now(),
            message="All tasks completed",
        )

        chunk = jules_agent._activity_to_chunk(activity)

        assert chunk.type == StreamingChunkType.RESULT

    def test_agent_message_extraction(self, jules_agent: JulesAgent) -> None:
        """Agent message extracted from activity data."""
        activity = JulesActivity(
            activity_id="act-5",
            type=JulesActivityType.AGENT_MESSAGED,
            timestamp=datetime.now(),
            message="",
            data={"agentMessage": "Created new_module.py successfully"},
        )

        chunk = jules_agent._activity_to_chunk(activity)

        assert "new_module.py" in chunk.data


# =============================================================================
# TESTS - STREAMING EXECUTION
# =============================================================================


class TestStreamingExecution:
    """Test streaming execution."""

    @pytest.mark.asyncio
    async def test_unavailable_client(self, jules_agent: JulesAgent) -> None:
        """Unavailable client yields error."""
        jules_agent.jules_client.is_available = False

        task = AgentTask(request="Test prompt", context={})
        chunks: List[StreamingChunk] = []

        async for chunk in jules_agent.execute_streaming(task):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].type == StreamingChunkType.ERROR
        assert "not configured" in chunks[0].data

    @pytest.mark.asyncio
    async def test_successful_execution(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
        sample_session: JulesSession,
        sample_activities: List[JulesActivity],
    ) -> None:
        """Successful execution streams all activities."""
        # Mock session creation
        mock_jules_client.create_session = AsyncMock(return_value=sample_session)

        # Mock session getter (returns completed at end)
        completed_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.COMPLETED,
            title="Test Session",
            prompt="Test prompt",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            result_url="https://github.com/org/repo/pull/123",
        )
        mock_jules_client.get_session = AsyncMock(return_value=completed_session)

        # Mock activity streaming
        async def mock_stream_activities(session_id: str, stop_on_complete: bool = True):
            for activity in sample_activities:
                yield activity

        mock_jules_client.stream_activities = mock_stream_activities

        task = AgentTask(request="Implement feature", context={})
        chunks: List[StreamingChunk] = []

        async for chunk in jules_agent.execute_streaming(task):
            chunks.append(chunk)

        # Should have: 2 status (creating, created) + 3 activities + 1 result
        assert len(chunks) >= 4
        assert any(c.type == StreamingChunkType.RESULT for c in chunks)

    @pytest.mark.asyncio
    async def test_plan_approval_callback(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
    ) -> None:
        """Plan approval callback is invoked."""
        # Setup session awaiting approval
        awaiting_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.AWAITING_PLAN_APPROVAL,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            plan=JulesPlan(plan_id="plan-1", steps=[]),
        )

        approved_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.IN_PROGRESS,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        completed_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.COMPLETED,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock client
        mock_jules_client.create_session = AsyncMock(return_value=awaiting_session)
        mock_jules_client.approve_plan = AsyncMock(return_value=approved_session)

        # Track get_session calls
        get_session_calls = [0]

        async def mock_get_session(session_id: str):
            get_session_calls[0] += 1
            if get_session_calls[0] <= 1:
                return awaiting_session
            return completed_session

        mock_jules_client.get_session = mock_get_session

        # Mock activities with plan generated
        plan_activity = JulesActivity(
            activity_id="act-plan",
            type=JulesActivityType.PLAN_GENERATED,
            timestamp=datetime.now(),
            message="Plan ready",
        )
        complete_activity = JulesActivity(
            activity_id="act-done",
            type=JulesActivityType.SESSION_COMPLETED,
            timestamp=datetime.now(),
            message="Done",
        )

        async def mock_stream(session_id: str, stop_on_complete: bool = True):
            yield plan_activity
            yield complete_activity

        mock_jules_client.stream_activities = mock_stream

        # Set approval callback
        callback_called = [False]

        async def approval_callback(session: JulesSession) -> bool:
            callback_called[0] = True
            return True

        jules_agent.set_plan_approval_callback(approval_callback)

        task = AgentTask(request="Test", context={})

        async for _ in jules_agent.execute_streaming(task):
            pass

        assert callback_called[0] is True
        mock_jules_client.approve_plan.assert_called_once()


# =============================================================================
# TESTS - SESSION OPERATIONS
# =============================================================================


class TestSessionOperations:
    """Test session management operations."""

    @pytest.mark.asyncio
    async def test_send_message(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
        sample_session: JulesSession,
    ) -> None:
        """Send message to active session."""
        jules_agent._active_session = sample_session
        mock_jules_client.send_message = AsyncMock(return_value=sample_session)

        result = await jules_agent.send_message("Continue work")

        mock_jules_client.send_message.assert_called_with("session-123", "Continue work")
        assert result is sample_session

    @pytest.mark.asyncio
    async def test_send_message_no_session(
        self, jules_agent: JulesAgent, mock_jules_client: MagicMock
    ) -> None:
        """Send message without session returns None."""
        jules_agent._active_session = None

        result = await jules_agent.send_message("Test")

        assert result is None
        mock_jules_client.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_current_plan(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
    ) -> None:
        """Approve plan for active session."""
        awaiting_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.AWAITING_PLAN_APPROVAL,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        approved_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.IN_PROGRESS,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        jules_agent._active_session = awaiting_session
        mock_jules_client.approve_plan = AsyncMock(return_value=approved_session)

        result = await jules_agent.approve_current_plan()

        mock_jules_client.approve_plan.assert_called_with("session-123")
        assert result.state == JulesSessionState.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_approve_wrong_state(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
        sample_session: JulesSession,
    ) -> None:
        """Approve returns None if not awaiting approval."""
        sample_session.state = JulesSessionState.IN_PROGRESS
        jules_agent._active_session = sample_session

        result = await jules_agent.approve_current_plan()

        assert result is None
        mock_jules_client.approve_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_status(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
        sample_session: JulesSession,
    ) -> None:
        """Get session status refreshes session."""
        jules_agent._active_session = sample_session
        sample_session.state = JulesSessionState.COMPLETED
        mock_jules_client.get_session = AsyncMock(return_value=sample_session)

        result = await jules_agent.get_session_status()

        mock_jules_client.get_session.assert_called_with("session-123")
        assert result.state == JulesSessionState.COMPLETED


# =============================================================================
# TESTS - EXECUTE (NON-STREAMING)
# =============================================================================


class TestExecute:
    """Test non-streaming execute."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        jules_agent: JulesAgent,
        mock_jules_client: MagicMock,
    ) -> None:
        """Execute collects streaming output."""
        completed_session = JulesSession(
            session_id="session-123",
            state=JulesSessionState.COMPLETED,
            title="Test",
            prompt="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            result_url="https://github.com/org/repo/pull/1",
        )

        mock_jules_client.create_session = AsyncMock(return_value=completed_session)
        mock_jules_client.get_session = AsyncMock(return_value=completed_session)

        async def mock_stream(session_id: str, stop_on_complete: bool = True):
            yield JulesActivity(
                activity_id="act-1",
                type=JulesActivityType.SESSION_COMPLETED,
                timestamp=datetime.now(),
                message="Done",
            )

        mock_jules_client.stream_activities = mock_stream

        task = AgentTask(request="Test", context={})
        response = await jules_agent.execute(task)

        assert response.success is True
        assert response.data["session_id"] == "session-123"
        assert response.data["result_url"] == "https://github.com/org/repo/pull/1"
