from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vertice_core.agui.ag_ui_adk import adk_event_to_agui
from vertice_core.agui.protocol import AGUIEvent, sse_encode_event

app = FastAPI(title="Vertice Agent Gateway", version="2026.1.0")


class PromptRequest(BaseModel):
    prompt: str
    session_id: str


class CreateTaskRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    tool: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    session_id: str
    status: str
    stream_url: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class TaskState:
    task_id: str
    session_id: str
    status: str
    created_at: str
    updated_at: str
    events: list[AGUIEvent] = field(default_factory=list)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)


_TASKS: dict[str, TaskState] = {}
_TASKS_LOCK = asyncio.Lock()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _mock_adk_events(prompt: str, *, tool: Optional[str] = None) -> AsyncIterator[dict]:
    """
    Mock upstream "ADK-ish" event stream.

    This isolates streaming mechanics + protocol from Vertex integration (next PR).
    """

    if prompt.strip().lower() == "__error__":
        yield {"type": "error", "message": "simulated error", "code": "simulated_error"}
        return

    yield {"type": "delta", "text": "SYSTEM ONLINE // WAITING FOR INPUT\n"}

    if tool:
        yield {
            "type": "tool",
            "name": tool,
            "input": {"prompt": prompt},
            "output": {"status": "simulated"},
            "status": "ok",
        }

    words = prompt.strip().split()
    if not words:
        yield {"type": "error", "message": "empty prompt", "code": "empty_prompt"}
        return

    for w in words:
        yield {"type": "delta", "text": f"{w} "}

    yield {
        "type": "final",
        "text": f"Echo: {prompt}",
        "metadata": {"mode": "mvp", "chunks": len(words)},
    }


async def _run_task(task: TaskState, *, prompt: str, tool: Optional[str]) -> None:
    try:
        async for raw in _mock_adk_events(prompt, tool=tool):
            event = adk_event_to_agui(raw, session_id=task.session_id)
            async with task.condition:
                task.events.append(event)
                task.updated_at = _utc_iso()
                task.condition.notify_all()
                if event.type.value in {"final", "error"}:
                    task.status = "completed" if event.type.value == "final" else "error"
                    task.updated_at = _utc_iso()
                    task.condition.notify_all()
                    return
        async with task.condition:
            task.status = "completed"
            task.updated_at = _utc_iso()
            task.condition.notify_all()
    except Exception as exc:  # fail-closed: emit terminal error
        error_event = AGUIEvent.error(
            "task crashed",
            session_id=task.session_id,
            code="task_crashed",
            details={"error": repr(exc)},
        )
        async with task.condition:
            task.events.append(error_event)
            task.status = "error"
            task.updated_at = _utc_iso()
            task.condition.notify_all()


@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "agent-gateway", "runtime": "cloud-run"}


@app.get("/agui/stream")
async def agui_stream(prompt: str, session_id: str = "default", tool: Optional[str] = None):
    """
    MVP AG-UI SSE stream.

    Query params:
      - prompt: user prompt (required)
      - session_id: stable session identifier
      - tool: optional tool name to simulate a tool event (MVP only)
    """

    async def _gen() -> AsyncIterator[bytes]:
        async for raw in _mock_adk_events(prompt, tool=tool):
            yield sse_encode_event(adk_event_to_agui(raw, session_id=session_id)).encode("utf-8")

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/agui/tasks", status_code=201)
async def create_task(req: CreateTaskRequest) -> TaskResponse:
    task_id = str(uuid.uuid4())
    now = _utc_iso()
    task = TaskState(
        task_id=task_id,
        session_id=req.session_id,
        status="running",
        created_at=now,
        updated_at=now,
    )

    async with _TASKS_LOCK:
        _TASKS[task_id] = task

    asyncio.create_task(_run_task(task, prompt=req.prompt, tool=req.tool))
    return TaskResponse(
        task_id=task_id,
        session_id=req.session_id,
        status=task.status,
        stream_url=f"/agui/tasks/{task_id}/stream",
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@app.get("/agui/tasks/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    async with _TASKS_LOCK:
        task = _TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    return TaskResponse(
        task_id=task.task_id,
        session_id=task.session_id,
        status=task.status,
        stream_url=f"/agui/tasks/{task_id}/stream",
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@app.get("/agui/tasks/{task_id}/stream")
async def stream_task(task_id: str) -> StreamingResponse:
    async with _TASKS_LOCK:
        task = _TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    async def _gen() -> AsyncIterator[bytes]:
        idx = 0
        while True:
            async with task.condition:
                while idx >= len(task.events) and task.status == "running":
                    await task.condition.wait()

                while idx < len(task.events):
                    event = task.events[idx]
                    idx += 1
                    yield sse_encode_event(event).encode("utf-8")
                    if event.type.value in {"final", "error"}:
                        return

                if task.status != "running":
                    return

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
