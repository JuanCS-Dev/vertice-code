from __future__ import annotations

from collections.abc import AsyncIterator

from vertice_core.agui.vertex_agent_engine import (
    adk_events_from_vertex_stream,
    vertex_event_to_adk_events,
)


async def _fake_vertex_stream() -> AsyncIterator[dict]:
    yield {"author": "model", "content": {"parts": [{"text": "Hello "}]}}
    yield {
        "author": "model",
        "content": {"parts": [{"function_call": {"name": "read_file", "args": {"path": "a.txt"}}}]},
    }
    yield {
        "author": "tool",
        "content": {
            "parts": [{"function_response": {"name": "read_file", "response": {"text": "OK"}}}]
        },
    }
    yield {"author": "model", "content": {"parts": [{"text": "world"}]}}


def test_vertex_event_to_adk_events_unknown_shape_returns_empty() -> None:
    assert vertex_event_to_adk_events({"nope": True}) == []


async def test_adk_events_from_vertex_stream_emits_delta_tool_and_final() -> None:
    events = [
        ev
        async for ev in adk_events_from_vertex_stream(
            _fake_vertex_stream(),
            metadata={"engine_id": "e1"},
        )
    ]

    assert [e["type"] for e in events] == ["delta", "tool", "tool", "delta", "final"]
    assert events[0]["text"] == "Hello "
    assert events[1]["name"] == "read_file"
    assert events[1]["status"] == "call"
    assert events[1]["input"]["path"] == "a.txt"
    assert events[2]["status"] == "ok"
    assert events[2]["output"]["text"] == "OK"
    assert events[-1]["text"] == "Hello world"
    assert events[-1]["metadata"]["engine_id"] == "e1"
