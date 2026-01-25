"""
AG-UI <-> ADK adapter (backend-only, stability-first).

This module exists to isolate any upstream runtime/event-shape changes (Vertex ADK / Reasoning Engines)
from the rest of the codebase. The gateway should only deal with AGUIEvent.
"""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Mapping
from typing import Any

from vertice_core.agui.protocol import AGUIEvent


def adk_event_to_agui(event: Mapping[str, Any], *, session_id: str = "default") -> AGUIEvent:
    """
    Convert a single upstream (ADK-ish) event payload into a stable AGUIEvent envelope.

    Supported minimal shapes (MVP):
      - {"type":"delta","text":"..."} OR {"type":"delta","data":{"text":"..."}}
      - {"type":"final","text":"...","metadata":{...}} OR {"type":"final","data":{...}}
      - {"type":"tool","name":"...","input":{...},"output":{...}} OR {"type":"tool","data":{...}}
      - {"type":"error","message":"...","code":"...","details":{...}} OR {"type":"error","data":{...}}
    """

    event_type = str(event.get("type", "")).strip().lower()
    data = event.get("data") if isinstance(event.get("data"), Mapping) else None

    if event_type == "delta":
        text = (data or {}).get("text") if data is not None else event.get("text")
        return AGUIEvent.delta(str(text or ""), session_id=session_id)

    if event_type == "final":
        if data is not None:
            text = data.get("text", "")
            metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}
        else:
            text = event.get("text", "")
            metadata = event.get("metadata") if isinstance(event.get("metadata"), Mapping) else {}
        return AGUIEvent.final(str(text or ""), session_id=session_id, metadata=dict(metadata))

    if event_type == "tool":
        if data is not None:
            name = data.get("name", "")
            tool_input = data.get("input") if isinstance(data.get("input"), Mapping) else {}
            output = data.get("output") if isinstance(data.get("output"), Mapping) else None
            status = str(data.get("status", "ok"))
        else:
            name = event.get("name", "")
            tool_input = event.get("input") if isinstance(event.get("input"), Mapping) else {}
            output = event.get("output") if isinstance(event.get("output"), Mapping) else None
            status = str(event.get("status", "ok"))
        return AGUIEvent.tool(
            str(name or ""),
            session_id=session_id,
            input=dict(tool_input),
            output=dict(output) if output is not None else None,
            status=status,
        )

    if event_type == "error":
        if data is not None:
            message = data.get("message", "")
            code = data.get("code", "unknown")
            details = data.get("details") if isinstance(data.get("details"), Mapping) else {}
        else:
            message = event.get("message", "")
            code = event.get("code", "unknown")
            details = event.get("details") if isinstance(event.get("details"), Mapping) else {}
        return AGUIEvent.error(
            str(message or ""),
            session_id=session_id,
            code=str(code or "unknown"),
            details=dict(details),
        )

    raise ValueError(f"Unsupported ADK event type: {event_type!r}")


async def adk_events_to_agui(
    events: AsyncIterable[Mapping[str, Any]],
    *,
    session_id: str = "default",
) -> AsyncIterator[AGUIEvent]:
    async for event in events:
        yield adk_event_to_agui(event, session_id=session_id)
