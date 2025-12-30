"""
A2A Protocol gRPC Server
========================

gRPC service implementation for A2A v0.3 protocol.

Features:
- Unary RPC for SendMessage, GetTask, ListTasks, CancelTask
- Server streaming for SendStreamingMessage, SubscribeTaskUpdates
- Health check endpoint
- Agent Card discovery

Reference:
- A2A Spec: https://a2a-protocol.org/latest/specification/
- gRPC AsyncIO: https://grpc.github.io/grpc/python/grpc_asyncio.html

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from concurrent import futures
from typing import AsyncIterator, Callable, Dict, List, Optional, TYPE_CHECKING

import grpc
from google.protobuf import timestamp_pb2

from .proto import (
    # Task types
    TaskState,
    Task,
    TaskStateTransition,
    SendMessageRequest,
    SendMessageResponse,
    GetTaskRequest,
    ListTasksRequest,
    ListTasksResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    # Message types
    MessageRole,
    Message,
    StreamChunk,
    StreamEventType,
    TaskStatusUpdate,
    # Agent Card
    AgentCard,
    GetAgentCardRequest,
    GetAgentCardResponse,
    # Service
    SubscribeTaskRequest,
    HealthCheckRequest,
    HealthCheckResponse,
    HealthStatus,
    # gRPC
    A2AServiceServicer,
    add_A2AServiceServicer_to_server,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# TASK STORE
# =============================================================================


class TaskStore:
    """In-memory task storage with event subscription support.

    Thread-safe storage for tasks with pub/sub for updates.
    For production, replace with persistent storage (Redis, PostgreSQL).
    """

    def __init__(self) -> None:
        """Initialize task store."""
        self._tasks: Dict[str, Task] = {}
        self._subscribers: Dict[str, List[asyncio.Queue[StreamChunk]]] = {}
        self._lock = asyncio.Lock()
        self._sequence_counters: Dict[str, int] = {}

    async def create_task(self, message: Message) -> Task:
        """Create a new task from an initial message."""
        async with self._lock:
            task_id = str(uuid.uuid4())
            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()

            task = Task(
                id=task_id,
                state=TaskState.TASK_STATE_SUBMITTED,
                created_at=now,
                updated_at=now,
            )
            task.messages.append(message)

            self._tasks[task_id] = task
            self._sequence_counters[task_id] = 0

            logger.info(f"[A2A] Created task: {task_id}")
            return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    async def update_task(
        self,
        task_id: str,
        state: Optional[TaskState] = None,
        message: Optional[Message] = None,
    ) -> Optional[Task]:
        """Update task and notify subscribers."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None

            # Update timestamp
            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()
            task.updated_at.CopyFrom(now)

            # Update state if provided
            if state is not None and state != task.state:
                # Record transition
                transition = TaskStateTransition(
                    from_state=task.state,
                    to_state=state,
                    timestamp=now,
                )
                task.history.append(transition)
                task.state = state

                # Notify subscribers
                await self._notify_status_update(task_id, state)

            # Add message if provided
            if message is not None:
                task.messages.append(message)

            return task

    async def list_tasks(
        self,
        states: Optional[List[TaskState]] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
        """List tasks with optional filtering."""
        tasks = list(self._tasks.values())

        if states:
            tasks = [t for t in tasks if t.state in states]

        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]

        # Sort by updated_at descending
        tasks.sort(
            key=lambda t: t.updated_at.ToDatetime(),
            reverse=True,
        )

        return tasks[:limit]

    async def subscribe(self, task_id: str) -> asyncio.Queue[StreamChunk]:
        """Subscribe to task updates."""
        async with self._lock:
            if task_id not in self._subscribers:
                self._subscribers[task_id] = []

            queue: asyncio.Queue[StreamChunk] = asyncio.Queue()
            self._subscribers[task_id].append(queue)

            logger.debug(f"[A2A] New subscriber for task {task_id}")
            return queue

    async def unsubscribe(
        self,
        task_id: str,
        queue: asyncio.Queue[StreamChunk],
    ) -> None:
        """Unsubscribe from task updates."""
        async with self._lock:
            if task_id in self._subscribers:
                try:
                    self._subscribers[task_id].remove(queue)
                except ValueError:
                    pass

    async def _notify_status_update(
        self,
        task_id: str,
        state: TaskState,
    ) -> None:
        """Notify all subscribers of status update."""
        if task_id not in self._subscribers:
            return

        self._sequence_counters[task_id] = (
            self._sequence_counters.get(task_id, 0) + 1
        )
        seq = self._sequence_counters[task_id]

        now = timestamp_pb2.Timestamp()
        now.GetCurrentTime()

        chunk = StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id=task_id,
            sequence=seq,
            status_update=TaskStatusUpdate(
                state=TaskState.Name(state),
            ),
            timestamp=now,
        )

        for queue in self._subscribers[task_id]:
            try:
                queue.put_nowait(chunk)
            except asyncio.QueueFull:
                logger.warning(f"[A2A] Subscriber queue full for {task_id}")

    async def notify_chunk(
        self,
        task_id: str,
        chunk: StreamChunk,
    ) -> None:
        """Send a chunk to all subscribers."""
        if task_id not in self._subscribers:
            return

        for queue in self._subscribers[task_id]:
            try:
                queue.put_nowait(chunk)
            except asyncio.QueueFull:
                logger.warning(f"[A2A] Subscriber queue full for {task_id}")


# =============================================================================
# A2A SERVICE IMPLEMENTATION
# =============================================================================


class A2AServiceImpl(A2AServiceServicer):
    """gRPC service implementation for A2A protocol.

    Provides full A2A v0.3 compliance with:
    - Message sending (unary and streaming)
    - Task management (get, list, cancel)
    - Agent discovery
    - Health checks

    Example:
        server = grpc.aio.server()
        service = A2AServiceImpl(agent_card, task_processor)
        add_A2AServiceServicer_to_server(service, server)
        await server.start()
    """

    def __init__(
        self,
        agent_card: AgentCard,
        task_processor: Optional[Callable[[Task], AsyncIterator[StreamChunk]]] = None,
    ) -> None:
        """Initialize A2A service.

        Args:
            agent_card: Agent card for discovery
            task_processor: Async generator that processes tasks
        """
        self._agent_card = agent_card
        self._task_processor = task_processor or self._default_processor
        self._task_store = TaskStore()
        self._start_time = time.time()

        logger.info(f"[A2A] Service initialized: {agent_card.name}")

    async def _default_processor(
        self,
        task: Task,
    ) -> AsyncIterator[StreamChunk]:
        """Default task processor - echoes input."""
        now = timestamp_pb2.Timestamp()
        now.GetCurrentTime()

        # Status: working
        yield StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id=task.id,
            sequence=1,
            status_update=TaskStatusUpdate(
                state="TASK_STATE_WORKING",
            ),
            timestamp=now,
        )

        await asyncio.sleep(0.1)  # Simulate processing

        # Get last user message
        user_message = ""
        for msg in task.messages:
            if msg.role == MessageRole.MESSAGE_ROLE_USER:
                for part in msg.parts:
                    if part.HasField("text"):
                        user_message = part.text.text

        # Response message
        response = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.MESSAGE_ROLE_AGENT,
            timestamp=now,
            task_id=task.id,
        )
        from .proto.common_pb2 import Part as PartProto

        text_part = PartProto()
        text_part.text.text = f"Processed: {user_message}"
        response.parts.append(text_part)

        yield StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_MESSAGE_CHUNK,
            task_id=task.id,
            sequence=2,
            message=response,
            timestamp=now,
        )

        # Status: completed
        now.GetCurrentTime()
        yield StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id=task.id,
            sequence=3,
            status_update=TaskStatusUpdate(
                state="TASK_STATE_COMPLETED",
            ),
            timestamp=now,
        )

    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================

    async def SendMessage(
        self,
        request: SendMessageRequest,
        context: grpc.aio.ServicerContext,
    ) -> SendMessageResponse:
        """Send message and get response (unary RPC)."""
        try:
            # Get or create task
            if request.task_id:
                task = await self._task_store.get_task(request.task_id)
                if not task:
                    await context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        f"Task not found: {request.task_id}",
                    )
                    return SendMessageResponse()

                # Add message to existing task
                await self._task_store.update_task(
                    task.id,
                    message=request.message,
                )
            else:
                # Create new task
                task = await self._task_store.create_task(request.message)

            # Process task (collect all chunks for unary response)
            response_message = None
            async for chunk in self._task_processor(task):
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_MESSAGE_CHUNK:
                    response_message = chunk.message

                # Update task state from status updates
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                    state_name = chunk.status_update.state
                    state = TaskState.Value(state_name)
                    await self._task_store.update_task(task.id, state=state)

            # Get final task state
            final_task = await self._task_store.get_task(task.id)

            return SendMessageResponse(
                task=final_task,
                response=response_message,
            )

        except Exception as e:
            logger.error(f"[A2A] SendMessage error: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL,
                str(e),
            )
            return SendMessageResponse()

    async def SendStreamingMessage(
        self,
        request: SendMessageRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[StreamChunk]:
        """Send message and stream response chunks."""
        try:
            # Get or create task
            if request.task_id:
                task = await self._task_store.get_task(request.task_id)
                if not task:
                    await context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        f"Task not found: {request.task_id}",
                    )
                    return

                await self._task_store.update_task(
                    task.id,
                    message=request.message,
                )
            else:
                task = await self._task_store.create_task(request.message)

            # Stream processing chunks
            async for chunk in self._task_processor(task):
                # Update task state
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                    state_name = chunk.status_update.state
                    state = TaskState.Value(state_name)
                    await self._task_store.update_task(task.id, state=state)

                yield chunk

        except Exception as e:
            logger.error(f"[A2A] SendStreamingMessage error: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    # =========================================================================
    # TASK OPERATIONS
    # =========================================================================

    async def GetTask(
        self,
        request: GetTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> Task:
        """Get task by ID."""
        task = await self._task_store.get_task(request.task_id)
        if not task:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Task not found: {request.task_id}",
            )
            return Task()

        return task

    async def ListTasks(
        self,
        request: ListTasksRequest,
        context: grpc.aio.ServicerContext,
    ) -> ListTasksResponse:
        """List tasks with filtering."""
        tasks = await self._task_store.list_tasks(
            states=list(request.states) if request.states else None,
            agent_id=request.agent_id or None,
            limit=request.limit or 100,
        )

        return ListTasksResponse(
            tasks=tasks,
            total_count=len(tasks),
        )

    async def CancelTask(
        self,
        request: CancelTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> CancelTaskResponse:
        """Cancel an in-progress task."""
        task = await self._task_store.get_task(request.task_id)
        if not task:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Task not found: {request.task_id}",
            )
            return CancelTaskResponse(success=False)

        # Check if task can be cancelled
        terminal_states = [
            TaskState.TASK_STATE_COMPLETED,
            TaskState.TASK_STATE_FAILED,
            TaskState.TASK_STATE_CANCELLED,
            TaskState.TASK_STATE_REJECTED,
        ]
        if task.state in terminal_states:
            return CancelTaskResponse(
                task=task,
                success=False,
            )

        # Cancel task
        updated = await self._task_store.update_task(
            request.task_id,
            state=TaskState.TASK_STATE_CANCELLED,
        )

        return CancelTaskResponse(
            task=updated,
            success=True,
        )

    async def SubscribeTaskUpdates(
        self,
        request: SubscribeTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[StreamChunk]:
        """Subscribe to task updates (server streaming)."""
        task = await self._task_store.get_task(request.task_id)
        if not task:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Task not found: {request.task_id}",
            )
            return

        # Subscribe to updates
        queue = await self._task_store.subscribe(request.task_id)

        try:
            # Send initial status
            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()
            yield StreamChunk(
                event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
                task_id=task.id,
                sequence=0,
                status_update=TaskStatusUpdate(
                    state=TaskState.Name(task.state),
                ),
                timestamp=now,
            )

            # Stream updates
            while True:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield chunk

                    # Stop if terminal state
                    if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                        state = TaskState.Value(chunk.status_update.state)
                        if state in [
                            TaskState.TASK_STATE_COMPLETED,
                            TaskState.TASK_STATE_FAILED,
                            TaskState.TASK_STATE_CANCELLED,
                        ]:
                            break

                except asyncio.TimeoutError:
                    # Send heartbeat
                    now.GetCurrentTime()
                    yield StreamChunk(
                        event_type=StreamEventType.STREAM_EVENT_TYPE_HEARTBEAT,
                        task_id=request.task_id,
                        timestamp=now,
                    )

        finally:
            await self._task_store.unsubscribe(request.task_id, queue)

    # =========================================================================
    # DISCOVERY OPERATIONS
    # =========================================================================

    async def GetAgentCard(
        self,
        request: GetAgentCardRequest,
        context: grpc.aio.ServicerContext,
    ) -> GetAgentCardResponse:
        """Get agent card for discovery."""
        return GetAgentCardResponse(card=self._agent_card)

    async def HealthCheck(
        self,
        request: HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> HealthCheckResponse:
        """Health check endpoint."""
        uptime = int(time.time() - self._start_time)

        return HealthCheckResponse(
            status=HealthStatus.HEALTH_STATUS_HEALTHY,
            version=self._agent_card.version,
            uptime_seconds=uptime,
        )


# =============================================================================
# SERVER FACTORY
# =============================================================================


async def create_grpc_server(
    agent_card: AgentCard,
    task_processor: Optional[Callable[[Task], AsyncIterator[StreamChunk]]] = None,
    port: int = 50051,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """Create and configure gRPC server.

    Args:
        agent_card: Agent card for discovery
        task_processor: Custom task processor
        port: Server port
        max_workers: Maximum worker threads

    Returns:
        Configured gRPC server (not started)

    Example:
        server = await create_grpc_server(agent_card, port=50051)
        await server.start()
        await server.wait_for_termination()
    """
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 30000),
            ("grpc.keepalive_timeout_ms", 10000),
        ],
    )

    service = A2AServiceImpl(agent_card, task_processor)
    add_A2AServiceServicer_to_server(service, server)

    server.add_insecure_port(f"[::]:{port}")

    logger.info(f"[A2A] gRPC server configured on port {port}")
    return server


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TaskStore",
    "A2AServiceImpl",
    "create_grpc_server",
]
