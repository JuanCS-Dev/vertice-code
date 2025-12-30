"""
A2A Protocol Task Store
=======================

In-memory task storage with pub/sub for gRPC streaming.

For production, replace with persistent storage (Redis, PostgreSQL).

Reference:
- A2A Spec: https://a2a-protocol.org/latest/specification/

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, List, Optional

from google.protobuf import timestamp_pb2

from .proto import (
    TaskState,
    Task,
    TaskStateTransition,
    Message,
    StreamChunk,
    StreamEventType,
    TaskStatusUpdate,
)

logger = logging.getLogger(__name__)


class TaskStore:
    """In-memory task storage with event subscription support.

    Thread-safe storage for tasks with pub/sub for updates.

    Example:
        >>> store = TaskStore()
        >>> task = await store.create_task(message)
        >>> await store.update_task(task.id, state=TaskState.TASK_STATE_WORKING)
    """

    def __init__(self) -> None:
        """Initialize task store."""
        self._tasks: Dict[str, Task] = {}
        self._subscribers: Dict[str, List[asyncio.Queue[StreamChunk]]] = {}
        self._lock = asyncio.Lock()
        self._sequence_counters: Dict[str, int] = {}

    async def create_task(self, message: Message) -> Task:
        """Create a new task from an initial message.

        Args:
            message: Initial message for the task

        Returns:
            Created Task with unique ID
        """
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
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    async def update_task(
        self,
        task_id: str,
        state: Optional[TaskState] = None,
        message: Optional[Message] = None,
    ) -> Optional[Task]:
        """Update task and notify subscribers.

        Args:
            task_id: Task identifier
            state: New state (optional)
            message: Message to append (optional)

        Returns:
            Updated Task if found, None otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None

            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()
            task.updated_at.CopyFrom(now)

            if state is not None and state != task.state:
                transition = TaskStateTransition(
                    from_state=task.state,
                    to_state=state,
                    timestamp=now,
                )
                task.history.append(transition)
                task.state = state
                await self._notify_status_update(task_id, state)

            if message is not None:
                task.messages.append(message)

            return task

    async def list_tasks(
        self,
        states: Optional[List[TaskState]] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
        """List tasks with optional filtering.

        Args:
            states: Filter by states (optional)
            agent_id: Filter by agent ID (optional)
            limit: Maximum tasks to return

        Returns:
            List of tasks sorted by updated_at descending
        """
        tasks = list(self._tasks.values())

        if states:
            tasks = [t for t in tasks if t.state in states]

        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]

        tasks.sort(
            key=lambda t: t.updated_at.ToDatetime(),
            reverse=True,
        )

        return tasks[:limit]

    async def subscribe(self, task_id: str) -> asyncio.Queue[StreamChunk]:
        """Subscribe to task updates.

        Args:
            task_id: Task identifier

        Returns:
            Queue that receives StreamChunk updates
        """
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
        """Unsubscribe from task updates.

        Args:
            task_id: Task identifier
            queue: Queue to unsubscribe
        """
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
        """Send a chunk to all subscribers.

        Args:
            task_id: Task identifier
            chunk: StreamChunk to broadcast
        """
        if task_id not in self._subscribers:
            return

        for queue in self._subscribers[task_id]:
            try:
                queue.put_nowait(chunk)
            except asyncio.QueueFull:
                logger.warning(f"[A2A] Subscriber queue full for {task_id}")


__all__ = ["TaskStore"]
