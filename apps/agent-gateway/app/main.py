from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vertice_core.agui.ag_ui_adk import adk_event_to_agui
from vertice_core.agui.protocol import AGUIEvent, sse_encode_event
from vertice_core.agui.vertex_agent_engine import (
    VertexAgentEngineSpec,
    stream_vertex_agent_engine_adk_events,
)

app = FastAPI(title="Vertice Agent Gateway", version="2026.1.0")

ENGINES_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "engines.json"


class PromptRequest(BaseModel):
    prompt: str
    session_id: str


class CreateTaskRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    agent: str = "coder"
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


def _vertex_enabled() -> bool:
    return os.getenv("VERTEX_AGENT_ENGINE_ENABLED", "0").strip() in {"1", "true", "yes", "on"}


def _load_engine_spec(agent: str) -> VertexAgentEngineSpec:
    try:
        raw = json.loads(ENGINES_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing engines config at {ENGINES_CONFIG_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in engines config at {ENGINES_CONFIG_PATH}") from exc

    engines = raw.get("engines")
    if not isinstance(engines, dict) or agent not in engines:
        raise RuntimeError(f"engine not configured for agent={agent!r} in engines.json")

    spec = engines[agent]
    if not isinstance(spec, dict):
        raise RuntimeError(f"invalid engine entry for agent={agent!r}")

    engine_id = spec.get("engine_id")
    project = spec.get("project")
    # Runtime (Agent/Reasoning Engine) is regional. Do not default to "global" here.
    location = spec.get("location") or "us-central1"
    if not isinstance(engine_id, str) or not engine_id:
        raise RuntimeError(f"missing engine_id for agent={agent!r}")
    if not isinstance(project, str) or not project:
        raise RuntimeError(f"missing project for agent={agent!r}")
    if not isinstance(location, str) or not location:
        location = "us-central1"

    return VertexAgentEngineSpec(engine_id=engine_id, project=project, location=location)


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


async def _upstream_adk_events(
    *,
    prompt: str,
    session_id: str,
    agent: str,
    tool: Optional[str],
) -> AsyncIterator[dict]:
    if not _vertex_enabled():
        async for ev in _mock_adk_events(prompt, tool=tool):
            yield ev
        return

    try:
        spec = _load_engine_spec(agent)
    except Exception as exc:
        yield {"type": "error", "message": str(exc), "code": "engine_config_error", "details": {}}
        return

    async for ev in stream_vertex_agent_engine_adk_events(
        spec=spec,
        prompt=prompt,
        session_id=session_id,
    ):
        yield ev


async def _run_task(task: TaskState, *, prompt: str, tool: Optional[str], agent: str) -> None:
    try:
        async for raw in _upstream_adk_events(
            prompt=prompt, session_id=task.session_id, agent=agent, tool=tool
        ):
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
async def agui_stream(
    prompt: str,
    session_id: str = "default",
    agent: str = "coder",
    tool: Optional[str] = None,
):
    """
    MVP AG-UI SSE stream.

    Query params:
      - prompt: user prompt (required)
      - session_id: stable session identifier
      - agent: agent key to resolve in engines.json when Vertex streaming is enabled
      - tool: optional tool name to simulate a tool event (MVP only)
    """

    async def _gen() -> AsyncIterator[bytes]:
        async for raw in _upstream_adk_events(
            prompt=prompt, session_id=session_id, agent=agent, tool=tool
        ):
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

    asyncio.create_task(_run_task(task, prompt=req.prompt, tool=req.tool, agent=req.agent))
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
