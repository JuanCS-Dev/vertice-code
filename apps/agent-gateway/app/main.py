from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vertice_core.agui.protocol import AGUIEvent, sse_encode_event
from vertice_core.agui.vertex_agent_engine import (
    VertexAgentEngineSpec,
    stream_vertex_agent_engine_adk_events,
)

app = FastAPI(title="Vertice Agent Gateway", version="2026.1.0")

ENGINES_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "engines.json"
GATEWAY_ROOT = Path(__file__).resolve().parents[1]
_gateway_root = str(GATEWAY_ROOT)
if _gateway_root in sys.path:
    sys.path.remove(_gateway_root)
sys.path.insert(0, _gateway_root)

_app_dir = str(Path(__file__).resolve().parent)
if _app_dir in sys.path:
    sys.path.remove(_app_dir)
sys.path.insert(1 if len(sys.path) > 0 else 0, _app_dir)

from api.stream import STREAM_HEADERS, AGUIStreamTranslator  # noqa: E402
import auth as _auth_mod  # noqa: E402
import store as _store_mod  # noqa: E402
import tenancy as _tenancy_mod  # noqa: E402

AuthContext = _auth_mod.AuthContext
get_auth_context = _auth_mod.get_auth_context

Run = _store_mod.Run
Store = _store_mod.Store
build_store = _store_mod.build_store

TenantContext = _tenancy_mod.TenantContext
resolve_tenant = _tenancy_mod.resolve_tenant


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


class OrgResponse(BaseModel):
    org_id: str
    name: str
    created_at: str
    owner_uid: str
    role: str


class CreateOrgRequest(BaseModel):
    name: str


class MeResponse(BaseModel):
    uid: str
    default_org_id: str
    orgs: list[OrgResponse]


class RunResponse(BaseModel):
    run_id: str
    org_id: str
    session_id: str
    agent: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    final_text: str | None = None


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
_STORE: Store = build_store()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _vertex_enabled() -> bool:
    return os.getenv("VERTEX_AGENT_ENGINE_ENABLED", "0").strip() in {"1", "true", "yes", "on"}


@app.get("/healthz/", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok", "time": _utc_iso(), "version": str(app.version)}


@app.get("/readyz/", include_in_schema=False)
async def readyz() -> dict[str, str]:
    if os.getenv("VERTICE_HEALTHCHECK_DEEP", "0").strip() not in {"1", "true", "yes", "on"}:
        return {"status": "ok", "mode": "shallow", "time": _utc_iso(), "version": str(app.version)}

    try:
        # Deep probe is opt-in: verify the backing store is reachable without mutating state.
        await _STORE.get_default_org_id(uid="__vertice_healthcheck__")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"store_unavailable: {exc}") from exc

    return {"status": "ok", "mode": "deep", "time": _utc_iso(), "version": str(app.version)}


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


async def get_tenant_context(
    auth: AuthContext = Depends(get_auth_context),
    x_vertice_org: str | None = Header(default=None, alias="X-Vertice-Org"),
) -> TenantContext:
    return await resolve_tenant(_STORE, uid=auth.uid, org_id=x_vertice_org)


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
        translator = AGUIStreamTranslator(session_id=task.session_id, prompt=prompt, agent=agent)
        # Understanding frame for task streams as well.
        async with task.condition:
            task.events.append(translator._intent_event())
            task.updated_at = _utc_iso()
            task.condition.notify_all()

        async for raw in _upstream_adk_events(
            prompt=prompt, session_id=task.session_id, agent=agent, tool=tool
        ):
            async with task.condition:
                for ev in translator.translate(raw):
                    task.events.append(ev)
                task.updated_at = _utc_iso()
                task.condition.notify_all()
                if task.events and task.events[-1].type.value in {"final", "error"}:
                    last = task.events[-1]
                    task.status = "completed" if last.type.value == "final" else "error"
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


@app.get("/v1/me")
async def me(auth: AuthContext = Depends(get_auth_context)) -> MeResponse:
    default_org = await _STORE.ensure_default_org(uid=auth.uid)
    await _STORE.set_default_org(uid=auth.uid, org_id=default_org.org_id)
    orgs = await _STORE.list_orgs(uid=auth.uid)
    resp_orgs: list[OrgResponse] = []
    for o in orgs:
        membership = await _STORE.get_membership(uid=auth.uid, org_id=o.org_id)
        resp_orgs.append(
            OrgResponse(
                org_id=o.org_id,
                name=o.name,
                created_at=o.created_at,
                owner_uid=o.owner_uid,
                role=(membership.role if membership else "member"),
            )
        )
    return MeResponse(uid=auth.uid, default_org_id=default_org.org_id, orgs=resp_orgs)


@app.get("/v1/orgs")
async def list_orgs(auth: AuthContext = Depends(get_auth_context)) -> list[OrgResponse]:
    default_org = await _STORE.ensure_default_org(uid=auth.uid)
    orgs = await _STORE.list_orgs(uid=auth.uid)
    out: list[OrgResponse] = []
    for o in orgs:
        membership = await _STORE.get_membership(uid=auth.uid, org_id=o.org_id)
        out.append(
            OrgResponse(
                org_id=o.org_id,
                name=o.name,
                created_at=o.created_at,
                owner_uid=o.owner_uid,
                role=(membership.role if membership else "member"),
            )
        )
    if not any(o.org_id == default_org.org_id for o in orgs):
        membership = await _STORE.get_membership(uid=auth.uid, org_id=default_org.org_id)
        out.insert(
            0,
            OrgResponse(
                org_id=default_org.org_id,
                name=default_org.name,
                created_at=default_org.created_at,
                owner_uid=default_org.owner_uid,
                role=(membership.role if membership else "member"),
            ),
        )
    return out


@app.post("/v1/orgs", status_code=201)
async def create_org(
    req: CreateOrgRequest, auth: AuthContext = Depends(get_auth_context)
) -> OrgResponse:
    org = await _STORE.create_org(uid=auth.uid, name=req.name)
    await _STORE.set_default_org(uid=auth.uid, org_id=org.org_id)
    membership = await _STORE.get_membership(uid=auth.uid, org_id=org.org_id)
    return OrgResponse(
        org_id=org.org_id,
        name=org.name,
        created_at=org.created_at,
        owner_uid=org.owner_uid,
        role=(membership.role if membership else "owner"),
    )


@app.get("/v1/runs")
async def list_runs(
    auth: AuthContext = Depends(get_auth_context),
    tenant: TenantContext = Depends(get_tenant_context),
) -> list[RunResponse]:
    runs = await _STORE.list_runs(uid=auth.uid, org_id=tenant.org.org_id, limit=50)
    return [
        RunResponse(
            run_id=r.run_id,
            org_id=r.org_id,
            session_id=r.session_id,
            agent=r.agent,
            prompt=r.prompt,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            final_text=r.final_text,
        )
        for r in runs
    ]


@app.get("/v1/runs/{run_id}")
async def get_run(
    run_id: str,
    auth: AuthContext = Depends(get_auth_context),
    tenant: TenantContext = Depends(get_tenant_context),
) -> RunResponse:
    run = await _STORE.get_run(uid=auth.uid, org_id=tenant.org.org_id, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return RunResponse(
        run_id=run.run_id,
        org_id=run.org_id,
        session_id=run.session_id,
        agent=run.agent,
        prompt=run.prompt,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        final_text=run.final_text,
    )


@app.get("/agui/stream")
async def agui_stream(
    prompt: str,
    session_id: str = "default",
    agent: str = "coder",
    tool: Optional[str] = None,
    auth: AuthContext = Depends(get_auth_context),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """
    MVP AG-UI SSE stream.

    Query params:
      - prompt: user prompt (required)
      - session_id: stable session identifier
      - agent: agent key to resolve in engines.json when Vertex streaming is enabled
      - tool: optional tool name to simulate a tool event (MVP only)
    """

    run: Run = await _STORE.create_run(
        uid=auth.uid,
        org_id=tenant.org.org_id,
        session_id=session_id,
        agent=agent,
        prompt=prompt,
    )

    async def _gen() -> AsyncIterator[bytes]:
        translator = AGUIStreamTranslator(session_id=session_id, prompt=prompt, agent=agent)
        # Emit intent immediately (includes run/org context for richer UI).
        intent = translator._intent_event()  # noqa: SLF001
        intent.data.setdefault("frame", "intent")
        intent.data.setdefault("run_id", run.run_id)
        intent.data.setdefault("org_id", tenant.org.org_id)
        yield sse_encode_event(intent).encode("utf-8")

        final_text_accum: list[str] = []
        status = "running"
        try:
            async for raw in _upstream_adk_events(
                prompt=prompt, session_id=session_id, agent=agent, tool=tool
            ):
                for ev in translator.translate(raw):
                    if ev.type.value == "delta":
                        t = str(ev.data.get("text") or "")
                        if t:
                            final_text_accum.append(t)
                    if ev.type.value in {"final"}:
                        final_text_accum.append(str(ev.data.get("text") or ""))
                        status = "completed"
                    if ev.type.value in {"error"}:
                        status = "error"
                    yield sse_encode_event(ev).encode("utf-8")
                    if ev.type.value in {"final", "error"}:
                        break
                if status in {"completed", "error"}:
                    break
        except Exception as exc:
            status = "error"
            err = AGUIEvent.error(
                "stream crashed",
                session_id=session_id,
                code="stream_crashed",
                details={"error": repr(exc), "run_id": run.run_id},
            )
            yield sse_encode_event(err).encode("utf-8")

        final_text = "".join(final_text_accum).strip() or None
        await _STORE.update_run(
            run_id=run.run_id,
            org_id=tenant.org.org_id,
            status=status,
            final_text=final_text,
        )

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )


@app.post("/agui/stream")
async def agui_stream_post(
    req: CreateTaskRequest,
    auth: AuthContext = Depends(get_auth_context),
    tenant: TenantContext = Depends(get_tenant_context),
):
    # Reuse the GET handler semantics; POST avoids long query strings and is friendlier to proxies.
    return await agui_stream(
        prompt=req.prompt,
        session_id=req.session_id,
        agent=req.agent,
        tool=req.tool,
        auth=auth,
        tenant=tenant,
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
        headers=STREAM_HEADERS,
    )
