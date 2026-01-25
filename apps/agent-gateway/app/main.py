from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vertice_core.agui.protocol import AGUIEvent, sse_encode_event

app = FastAPI(title="Vertice Agent Gateway", version="2026.1.0")


class PromptRequest(BaseModel):
    prompt: str
    session_id: str


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
        if prompt.strip().lower() == "__error__":
            yield sse_encode_event(
                AGUIEvent.error("simulated error", session_id=session_id, code="simulated_error")
            ).encode("utf-8")
            return

        yield sse_encode_event(
            AGUIEvent.delta("SYSTEM ONLINE // WAITING FOR INPUT\n", session_id=session_id)
        ).encode("utf-8")

        if tool:
            yield sse_encode_event(
                AGUIEvent.tool(
                    tool,
                    session_id=session_id,
                    input={"prompt": prompt},
                    output={"status": "simulated"},
                )
            ).encode("utf-8")

        # Simple deterministic chunking (no sleeps; tests must be fast/offline).
        words = prompt.strip().split()
        if not words:
            yield sse_encode_event(
                AGUIEvent.error("empty prompt", session_id=session_id, code="empty_prompt")
            ).encode("utf-8")
            return

        for w in words:
            yield sse_encode_event(AGUIEvent.delta(f"{w} ", session_id=session_id)).encode("utf-8")

        yield sse_encode_event(
            AGUIEvent.final(
                text=f"Echo: {prompt}",
                session_id=session_id,
                metadata={"mode": "mvp", "chunks": len(words)},
            )
        ).encode("utf-8")

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
