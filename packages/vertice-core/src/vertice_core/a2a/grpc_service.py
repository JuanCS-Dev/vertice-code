"""
A2A Protocol gRPC Service Implementation
========================================

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
from typing import AsyncIterator, Callable, Optional

import grpc
from google.protobuf import timestamp_pb2

from .proto import (
    TaskState,
    Task,
    SendMessageRequest,
    SendMessageResponse,
    GetTaskRequest,
    ListTasksRequest,
    ListTasksResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    MessageRole,
    Message,
    StreamChunk,
    StreamEventType,
    TaskStatusUpdate,
    AgentCard,
    GetAgentCardRequest,
    GetAgentCardResponse,
    SubscribeTaskRequest,
    HealthCheckRequest,
    HealthCheckResponse,
    HealthStatus,
    A2AServiceServicer,
)
from .grpc_task_store import TaskStore

logger = logging.getLogger(__name__)


class A2AServiceImpl(A2AServiceServicer):
    """gRPC service implementation for A2A protocol.

    Provides full A2A v0.3 compliance with:
    - Message sending (unary and streaming)
    - Task management (get, list, cancel)
    - Agent discovery
    - Health checks

    Example:
        >>> server = grpc.aio.server()
        >>> service = A2AServiceImpl(agent_card, task_processor)
        >>> add_A2AServiceServicer_to_server(service, server)
        >>> await server.start()
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

        yield StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id=task.id,
            sequence=1,
            status_update=TaskStatusUpdate(state="TASK_STATE_WORKING"),
            timestamp=now,
        )

        await asyncio.sleep(0.1)

        user_message = ""
        for msg in task.messages:
            if msg.role == MessageRole.MESSAGE_ROLE_USER:
                for part in msg.parts:
                    if part.HasField("text"):
                        user_message = part.text.text

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

        now.GetCurrentTime()
        yield StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id=task.id,
            sequence=3,
            status_update=TaskStatusUpdate(state="TASK_STATE_COMPLETED"),
            timestamp=now,
        )

    async def SendMessage(
        self,
        request: SendMessageRequest,
        context: grpc.aio.ServicerContext,
    ) -> SendMessageResponse:
        """Send message and get response (unary RPC)."""
        try:
            if request.task_id:
                task = await self._task_store.get_task(request.task_id)
                if not task:
                    await context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        f"Task not found: {request.task_id}",
                    )
                    return SendMessageResponse()
                await self._task_store.update_task(task.id, message=request.message)
            else:
                task = await self._task_store.create_task(request.message)

            response_message = None
            async for chunk in self._task_processor(task):
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_MESSAGE_CHUNK:
                    response_message = chunk.message
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                    state = TaskState.Value(chunk.status_update.state)
                    await self._task_store.update_task(task.id, state=state)

            final_task = await self._task_store.get_task(task.id)
            return SendMessageResponse(task=final_task, response=response_message)

        except Exception as e:
            logger.error(f"[A2A] SendMessage error: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
            return SendMessageResponse()

    async def SendStreamingMessage(
        self,
        request: SendMessageRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[StreamChunk]:
        """Send message and stream response chunks."""
        try:
            if request.task_id:
                task = await self._task_store.get_task(request.task_id)
                if not task:
                    await context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        f"Task not found: {request.task_id}",
                    )
                    return
                await self._task_store.update_task(task.id, message=request.message)
            else:
                task = await self._task_store.create_task(request.message)

            async for chunk in self._task_processor(task):
                if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                    state = TaskState.Value(chunk.status_update.state)
                    await self._task_store.update_task(task.id, state=state)
                yield chunk

        except Exception as e:
            logger.error(f"[A2A] SendStreamingMessage error: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

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
        return ListTasksResponse(tasks=tasks, total_count=len(tasks))

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

        terminal_states = [
            TaskState.TASK_STATE_COMPLETED,
            TaskState.TASK_STATE_FAILED,
            TaskState.TASK_STATE_CANCELLED,
            TaskState.TASK_STATE_REJECTED,
        ]
        if task.state in terminal_states:
            return CancelTaskResponse(task=task, success=False)

        updated = await self._task_store.update_task(
            request.task_id, state=TaskState.TASK_STATE_CANCELLED
        )
        return CancelTaskResponse(task=updated, success=True)

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

        queue = await self._task_store.subscribe(request.task_id)
        try:
            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()
            yield StreamChunk(
                event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
                task_id=task.id,
                sequence=0,
                status_update=TaskStatusUpdate(state=TaskState.Name(task.state)),
                timestamp=now,
            )

            while True:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield chunk

                    if chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE:
                        state = TaskState.Value(chunk.status_update.state)
                        if state in [
                            TaskState.TASK_STATE_COMPLETED,
                            TaskState.TASK_STATE_FAILED,
                            TaskState.TASK_STATE_CANCELLED,
                        ]:
                            break
                except asyncio.TimeoutError:
                    now.GetCurrentTime()
                    yield StreamChunk(
                        event_type=StreamEventType.STREAM_EVENT_TYPE_HEARTBEAT,
                        task_id=request.task_id,
                        timestamp=now,
                    )
        finally:
            await self._task_store.unsubscribe(request.task_id, queue)

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


__all__ = ["A2AServiceImpl"]
