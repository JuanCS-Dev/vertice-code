from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
import pytest

from vertice_core.agui.protocol import AGUIEvent, AGUIEventType


def _load_agent_gateway_app():
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / "apps" / "agent-gateway" / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("agent_gateway_main", main_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


def _parse_sse_block(block: str) -> Tuple[str, Dict[str, Any]]:
    lines = block.splitlines()
    event_line = next(l for l in lines if l.startswith("event: "))
    data_line = next(l for l in lines if l.startswith("data: "))
    event_type = event_line.removeprefix("event: ").strip()
    payload = json.loads(data_line.removeprefix("data: ").strip())
    return event_type, payload


async def _collect_sse_events(
    resp: httpx.Response,
    *,
    stop_on: set[str] | None = None,
    max_events: int = 100,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Consume SSE stream until a terminal event arrives.

    SSE streams can keep connections open; tests should stop after receiving `final` or `error`.
    """

    stop_on = stop_on or {AGUIEventType.FINAL.value, AGUIEventType.ERROR.value}
    events: List[Tuple[str, Dict[str, Any]]] = []
    buffer = ""

    async for chunk in resp.aiter_text():
        buffer += chunk
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            if not block.strip():
                continue
            event_type, payload = _parse_sse_block(block)
            events.append((event_type, payload))
            if payload.get("type") in stop_on:
                return events
            if len(events) >= max_events:
                raise AssertionError("SSE stream exceeded max_events without terminal event")

    return events


@pytest.mark.asyncio
async def test_agui_stream_happy_path() -> None:
    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET", "/agui/stream", params={"prompt": "hello world", "session_id": "s1"}
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            events = await _collect_sse_events(resp)

    assert len(events) >= 3
    validated = [AGUIEvent.model_validate(payload) for _, payload in events]
    assert validated[-1].type == AGUIEventType.FINAL
    assert validated[-1].session_id == "s1"
    assert validated[-1].data["text"] == "Echo: hello world"


@pytest.mark.asyncio
async def test_agui_stream_tool_event() -> None:
    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET",
            "/agui/stream",
            params={"prompt": "run search", "session_id": "s2", "tool": "search"},
        ) as resp:
            assert resp.status_code == 200
            events = await _collect_sse_events(resp)

    types = [payload["type"] for _, payload in events]
    assert AGUIEventType.TOOL.value in types


@pytest.mark.asyncio
async def test_agui_stream_error_event() -> None:
    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET", "/agui/stream", params={"prompt": "__error__", "session_id": "s3"}
        ) as resp:
            assert resp.status_code == 200
            events = await _collect_sse_events(resp)

    assert len(events) == 1
    assert events[0][1]["type"] == AGUIEventType.ERROR.value


@pytest.mark.asyncio
async def test_healthz() -> None:
    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "agent-gateway"


@pytest.mark.asyncio
async def test_agui_stream_completes_and_closes() -> None:
    """
    Regression guard for the original hang: consuming the full body should complete.

    We do not use FastAPI/Starlette TestClient here because it hangs in this environment; httpx works.
    """

    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET", "/agui/stream", params={"prompt": "hello world", "session_id": "s1"}
        ) as resp:
            body = await asyncio.wait_for(resp.aread(), timeout=2.0)

    assert body
    events = [_parse_sse_block(b) for b in body.decode("utf-8").split("\n\n") if b.strip()]
    assert events[-1][1]["type"] == AGUIEventType.FINAL.value


@pytest.mark.asyncio
async def test_agui_tasks_create_status_and_stream() -> None:
    app = _load_agent_gateway_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/agui/tasks",
            json={"prompt": "hello world", "session_id": "s10", "tool": "search"},
        )
        assert created.status_code == 201
        task = created.json()
        assert task["status"] == "running"
        task_id = task["task_id"]

        status = await client.get(f"/agui/tasks/{task_id}")
        assert status.status_code == 200
        assert status.json()["task_id"] == task_id

        async with client.stream("GET", f"/agui/tasks/{task_id}/stream") as resp:
            assert resp.status_code == 200
            events = await _collect_sse_events(resp)

    types = [payload["type"] for _, payload in events]
    assert AGUIEventType.TOOL.value in types
    assert types[-1] == AGUIEventType.FINAL.value
