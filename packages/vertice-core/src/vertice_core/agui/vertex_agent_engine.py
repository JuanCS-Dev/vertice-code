"""
Vertex AI Agent Engine streaming -> Vertice "ADK-ish" events.

Why this module exists
----------------------
The public, stable contract in this repo is the AG-UI event schema implemented by:
`vertice_core.agui.protocol.AGUIEvent` + `vertice_core.agui.ag_ui_adk.adk_event_to_agui`.

Vertex AI Agent Engines stream dict events whose shape may evolve. This module normalizes those
stream chunks into a minimal, stability-first "ADK-ish" envelope:
  - {"type":"delta","text":"..."}
  - {"type":"tool","name":"...","input":{...},"output":{...}|None,"status":"call"|"ok"}
  - {"type":"final","text":"...","metadata":{...}}
  - {"type":"error","message":"...","code":"...","details":{...}}

No local tool execution happens here; this module is purely an adapter.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncIterable, AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class VertexAgentEngineSpec:
    engine_id: str
    project: str
    # Runtime is regional; model inference may be "global" but engines are not.
    location: str = "us-central1"


def _is_reasoning_engine_resource(engine_id: str) -> bool:
    return "/reasoningEngines/" in engine_id


def _chunk_text(text: str, *, target_chunk_size: int = 80) -> list[str]:
    if not text:
        return []
    if target_chunk_size <= 0:
        return [text]
    chunk_count = max(1, math.ceil(len(text) / target_chunk_size))
    chunk_size = max(1, math.ceil(len(text) / chunk_count))
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def _iter_vertex_parts(event: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    content = event.get("content")
    if not isinstance(content, Mapping):
        return []
    parts = content.get("parts")
    if not isinstance(parts, list):
        return []
    out: list[Mapping[str, Any]] = []
    for p in parts:
        if isinstance(p, Mapping):
            out.append(p)
    return out


def vertex_event_to_adk_events(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    """
    Convert a single Vertex Agent Engines streamed dict event into 0..N ADK-ish events.

    Known shapes (2026 docs):
      - text delta: {"content":{"parts":[{"text":"..."}]}}
      - tool call:  {"content":{"parts":[{"function_call":{"name":"x","args":{...}}}]}}
      - tool resp:  {"content":{"parts":[{"function_response":{"name":"x","response":{...}}}]}}
    """

    out: list[dict[str, Any]] = []
    for part in _iter_vertex_parts(event):
        if isinstance(part.get("text"), str) and part["text"]:
            out.append({"type": "delta", "text": part["text"]})
            continue

        fc = part.get("function_call")
        if isinstance(fc, Mapping):
            name = str(fc.get("name", "") or "")
            args = fc.get("args") if isinstance(fc.get("args"), Mapping) else {}
            out.append(
                {
                    "type": "tool",
                    "name": name,
                    "input": dict(args),
                    "output": None,
                    "status": "call",
                }
            )
            continue

        fr = part.get("function_response")
        if isinstance(fr, Mapping):
            name = str(fr.get("name", "") or "")
            resp = fr.get("response") if isinstance(fr.get("response"), Mapping) else {}
            out.append(
                {
                    "type": "tool",
                    "name": name,
                    "input": {},
                    "output": dict(resp),
                    "status": "ok",
                }
            )
            continue

    return out


async def adk_events_from_vertex_stream(
    stream: AsyncIterable[Mapping[str, Any]],
    *,
    emit_final: bool = True,
    metadata: Optional[Mapping[str, Any]] = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Convert a Vertex Agent Engines streamed event iterator into ADK-ish events.

    If `emit_final` is True, emits a terminal {"type":"final", ...} when the stream ends,
    using the concatenation of all deltas observed.
    """

    full_text: list[str] = []
    async for raw in stream:
        for ev in vertex_event_to_adk_events(raw):
            if ev.get("type") == "delta":
                full_text.append(str(ev.get("text", "")))
            yield ev
        await asyncio.sleep(0)

    if emit_final:
        yield {
            "type": "final",
            "text": "".join(full_text).strip(),
            "metadata": dict(metadata or {}),
        }


async def stream_vertex_agent_engine_adk_events(
    *,
    spec: VertexAgentEngineSpec,
    prompt: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream ADK-ish events from a deployed Vertex Agent/Reasoning Engine.

    This uses `vertexai.agent_engines` (2026) which exposes an async streaming API.
    """

    try:
        import vertexai  # type: ignore
        from vertexai import agent_engines  # type: ignore
    except Exception as exc:
        yield {
            "type": "error",
            "message": "vertexai SDK not available (cannot stream from Agent Engine)",
            "code": "vertex_sdk_missing",
            "details": {"error": repr(exc)},
        }
        return

    try:
        vertexai.init(project=spec.project, location=spec.location)
        remote_app = agent_engines.get(resource_name=spec.engine_id)
    except Exception as exc:
        yield {
            "type": "error",
            "message": "failed to initialize Vertex Agent Engine client",
            "code": "vertex_init_failed",
            "details": {
                "engine_id": spec.engine_id,
                "project": spec.project,
                "location": spec.location,
                "error": repr(exc),
            },
        }
        return

    try:
        uid = user_id or session_id

        if hasattr(remote_app, "async_stream_query"):
            try:
                stream = remote_app.async_stream_query(
                    user_id=uid, session_id=session_id, message=prompt
                )
            except TypeError:
                # Older/newer SDK variations: fall back to a minimal call signature.
                stream = remote_app.async_stream_query(message=prompt)

            async for ev in adk_events_from_vertex_stream(
                stream,
                metadata={
                    "engine_id": spec.engine_id,
                    "project": spec.project,
                    "location": spec.location,
                },
            ):
                yield ev
            return

        # ReasoningEngine (custom agent) fallback: non-streaming query.
        #
        # The runtime may not support async streaming, but we still need to satisfy
        # the AG-UI contract (delta|final|tool|error). We synthesize deltas from
        # the final output to keep downstream consumers stable.
        if _is_reasoning_engine_resource(spec.engine_id) and hasattr(remote_app, "query"):
            response = await asyncio.to_thread(remote_app.query, input=prompt)
            text = ""
            if isinstance(response, Mapping):
                out = response.get("output")
                if isinstance(out, str):
                    text = out
                else:
                    text = str(out) if out is not None else ""
            else:
                text = str(response)

            for chunk in _chunk_text(text):
                yield {"type": "delta", "text": chunk}
                await asyncio.sleep(0)

            yield {
                "type": "final",
                "text": text.strip(),
                "metadata": {
                    "engine_id": spec.engine_id,
                    "project": spec.project,
                    "location": spec.location,
                    "mode": "reasoning_engine_query_fallback",
                },
            }
            return

        yield {
            "type": "error",
            "message": "remote engine does not expose a supported streaming/query API",
            "code": "vertex_unsupported_engine_api",
            "details": {
                "engine_id": spec.engine_id,
                "has_async_stream_query": hasattr(remote_app, "async_stream_query"),
                "has_query": hasattr(remote_app, "query"),
            },
        }

    except Exception as exc:
        yield {
            "type": "error",
            "message": "vertex stream crashed",
            "code": "vertex_stream_crashed",
            "details": {"error": repr(exc)},
        }
