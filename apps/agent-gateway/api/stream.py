from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from vertice_core.agui.protocol import AGUIEvent, AGUIEventType, sse_encode_event
from vertice_core.memory.cortex.cortex import MemoryCortex

STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}

FrameType = Literal["intent", "thought", "code_delta", "trajectory", "delta", "final", "tool", "error"]


def _truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


_THOUGHT_OPEN = "<thought>"
_THOUGHT_CLOSE = "</thought>"


class ThoughtStreamSplitter:
    """
    Incremental splitter for `<thought>...</thought>` blocks.

    Produces ('thought'|'delta', text) segments while preserving ordering across streamed chunks.
    """

    def __init__(self) -> None:
        self._buffer = ""
        self._in_thought = False

    def feed(self, text: str) -> list[tuple[Literal["thought", "delta"], str]]:
        if not text:
            return []
        self._buffer += text
        out: list[tuple[Literal["thought", "delta"], str]] = []

        while True:
            if self._in_thought:
                end = self._buffer.find(_THOUGHT_CLOSE)
                if end == -1:
                    # Avoid unbounded buffering if the close tag never arrives.
                    if len(self._buffer) > 4096:
                        keep = len(_THOUGHT_CLOSE) - 1
                        chunk, self._buffer = self._buffer[:-keep], self._buffer[-keep:]
                        if chunk:
                            out.append(("thought", chunk))
                    break
                chunk = self._buffer[:end]
                if chunk:
                    out.append(("thought", chunk))
                self._buffer = self._buffer[end + len(_THOUGHT_CLOSE) :]
                self._in_thought = False
                continue

            start = self._buffer.find(_THOUGHT_OPEN)
            if start == -1:
                # Keep a small tail so `<thought>` split across chunks is detected.
                keep = len(_THOUGHT_OPEN) - 1
                if len(self._buffer) <= keep:
                    break
                chunk, self._buffer = self._buffer[:-keep], self._buffer[-keep:]
                if chunk:
                    out.append(("delta", chunk))
                break

            pre = self._buffer[:start]
            if pre:
                out.append(("delta", pre))
            self._buffer = self._buffer[start + len(_THOUGHT_OPEN) :]
            self._in_thought = True

        return out

    def flush(self) -> list[tuple[Literal["thought", "delta"], str]]:
        if not self._buffer:
            return []
        kind: Literal["thought", "delta"] = "thought" if self._in_thought else "delta"
        chunk = self._buffer
        self._buffer = ""
        return [(kind, chunk)]


_THOUGHT_RE = re.compile(r"<thought>.*?</thought>", re.DOTALL)


def strip_thought_blocks(text: str) -> str:
    stripped = _THOUGHT_RE.sub("", text or "")
    # Normalize whitespace introduced by removing tagged sections.
    stripped = re.sub(r"[ \t]{2,}", " ", stripped)
    return stripped.strip()


def _looks_like_code_delta_tool(name: str) -> bool:
    n = (name or "").strip().lower()
    return n in {"write_file", "create_file", "apply_patch", "delete_file", "edit_file"}


@dataclass(slots=True)
class AGUIStreamTranslator:
    """
    Translate upstream "ADK-ish" events into AGUIEvent(s) with multi-frame annotations.

    Stability policy:
    - We keep the outer SSE `event:` values stable: delta|final|tool|error.
    - We add `data.frame` and `data.channel` to enable richer UI rendering.
    """

    session_id: str
    prompt: Optional[str] = None
    agent: Optional[str] = None
    persist_code_deltas: bool = True
    _splitter: ThoughtStreamSplitter = field(init=False, repr=False)
    _cortex: MemoryCortex = field(init=False, repr=False)
    _redact_thoughts: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._splitter = ThoughtStreamSplitter()
        self._cortex = MemoryCortex(base_path=self._cortex_path(), agent_id=self.agent or "gateway")
        self._redact_thoughts = not _truthy_env("VERTICE_STREAM_THOUGHTS", "0")
        if not _truthy_env("VERTICE_PERSIST_CODE_DELTAS", "1"):
            self.persist_code_deltas = False

    def _cortex_path(self) -> Path:
        # Keep gateway state in /tmp by default (Cloud Run friendly).
        return Path(os.getenv("VERTICE_CORTEX_PATH", "/tmp/vertice-cortex"))

    def _intent_event(self) -> AGUIEvent:
        ev = AGUIEvent.tool(
            "intent",
            session_id=self.session_id,
            input={"prompt": self.prompt or "", "agent": self.agent or ""},
            output=None,
            status="ok",
        )
        ev.data["frame"] = "intent"
        return ev

    def _thought_delta(self, text: str) -> AGUIEvent:
        payload: dict[str, Any] = {"text": text, "frame": "thought", "channel": "thought"}
        if self._redact_thoughts:
            payload["text"] = "[REDACTED]"
            payload["redacted"] = True
        return AGUIEvent(type=AGUIEventType.DELTA, session_id=self.session_id, data=payload)

    def _text_delta(self, text: str) -> AGUIEvent:
        return AGUIEvent(type=AGUIEventType.DELTA, session_id=self.session_id, data={"text": text})

    def _code_delta_tool(self, tool_event: Mapping[str, Any]) -> AGUIEvent:
        name = str(tool_event.get("name") or "")
        tool_input = tool_event.get("input") if isinstance(tool_event.get("input"), Mapping) else {}
        output = tool_event.get("output") if isinstance(tool_event.get("output"), Mapping) else None
        status = str(tool_event.get("status") or "ok")
        ev = AGUIEvent.tool(
            name,
            session_id=self.session_id,
            input=dict(tool_input),
            output=dict(output) if output is not None else None,
            status=status,
        )
        ev.data["frame"] = "code_delta"
        return ev

    def _trajectory_tool(self, tool_event: Mapping[str, Any]) -> AGUIEvent:
        name = str(tool_event.get("name") or "trajectory")
        tool_input = tool_event.get("input") if isinstance(tool_event.get("input"), Mapping) else {}
        output = tool_event.get("output") if isinstance(tool_event.get("output"), Mapping) else None
        status = str(tool_event.get("status") or "ok")
        ev = AGUIEvent.tool(
            name,
            session_id=self.session_id,
            input=dict(tool_input),
            output=dict(output) if output is not None else None,
            status=status,
        )
        ev.data["frame"] = "trajectory"
        return ev

    def _schedule_code_delta_persist(self, tool_event: Mapping[str, Any]) -> None:
        if not self.persist_code_deltas:
            return

        payload = {
            "name": str(tool_event.get("name") or ""),
            "input": tool_event.get("input") if isinstance(tool_event.get("input"), Mapping) else {},
            "output": tool_event.get("output") if isinstance(tool_event.get("output"), Mapping) else None,
            "status": str(tool_event.get("status") or "ok"),
        }

        # Persist in the background to avoid adding latency to the SSE loop.
        async def _persist() -> None:
            content = json.dumps(payload, ensure_ascii=False)
            await asyncio.to_thread(
                self._cortex.remember,
                content,
                "episodic",
                None,
                self.session_id,
                event_type="code_delta",
                metadata={"frame": "code_delta", **payload},
            )

        asyncio.create_task(_persist())

    def translate(self, event: Mapping[str, Any]) -> list[AGUIEvent]:
        event_type = str(event.get("type", "")).strip().lower()
        data = event.get("data") if isinstance(event.get("data"), Mapping) else None

        if event_type == "delta":
            text = (data or {}).get("text") if data is not None else event.get("text")
            pieces = self._splitter.feed(str(text or ""))
            out: list[AGUIEvent] = []
            for kind, chunk in pieces:
                if not chunk:
                    continue
                out.append(self._thought_delta(chunk) if kind == "thought" else self._text_delta(chunk))
            return out

        if event_type == "final":
            if data is not None:
                text = data.get("text", "")
                metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}
            else:
                text = event.get("text", "")
                metadata = event.get("metadata") if isinstance(event.get("metadata"), Mapping) else {}

            flushed = self._splitter.flush()
            out: list[AGUIEvent] = []
            for kind, chunk in flushed:
                if not chunk:
                    continue
                out.append(self._thought_delta(chunk) if kind == "thought" else self._text_delta(chunk))

            out.append(
                AGUIEvent.final(
                    strip_thought_blocks(str(text or "")),
                    session_id=self.session_id,
                    metadata=dict(metadata),
                )
            )
            return out

        if event_type == "tool":
            tool_ev = data if data is not None else event
            name = str(tool_ev.get("name") or "")

            # Dedicated frames
            if _looks_like_code_delta_tool(name):
                ev = self._code_delta_tool(tool_ev)
                self._schedule_code_delta_persist(tool_ev)
                return [ev]

            if name.startswith("trajectory") or name in {"trajectory_update", "trajectory.update"}:
                return [self._trajectory_tool(tool_ev)]

            # Default tool passthrough
            tool_input = tool_ev.get("input") if isinstance(tool_ev.get("input"), Mapping) else {}
            output = tool_ev.get("output") if isinstance(tool_ev.get("output"), Mapping) else None
            status = str(tool_ev.get("status") or "ok")
            return [
                AGUIEvent.tool(
                    name,
                    session_id=self.session_id,
                    input=dict(tool_input),
                    output=dict(output) if output is not None else None,
                    status=status,
                )
            ]

        if event_type == "error":
            if data is not None:
                message = data.get("message", "")
                code = data.get("code", "unknown")
                details = data.get("details") if isinstance(data.get("details"), Mapping) else {}
            else:
                message = event.get("message", "")
                code = event.get("code", "unknown")
                details = event.get("details") if isinstance(event.get("details"), Mapping) else {}
            return [
                AGUIEvent.error(
                    str(message or ""),
                    session_id=self.session_id,
                    code=str(code or "unknown"),
                    details=dict(details),
                )
            ]

        # v2.0 frame aliases (best-effort)
        if event_type in {"intent", "thought", "code_delta", "trajectory"}:
            if event_type == "intent":
                ev = self._intent_event()
                # allow upstream to override prompt/agent payload
                if data is not None:
                    ev.data["input"] = dict(data)
                return [ev]
            if event_type == "thought":
                text = (data or {}).get("text") if data is not None else event.get("text")
                return [self._thought_delta(str(text or ""))]
            if event_type == "code_delta":
                tool_ev = data if data is not None else event
                ev = self._code_delta_tool(tool_ev)
                self._schedule_code_delta_persist(tool_ev)
                return [ev]
            if event_type == "trajectory":
                tool_ev = data if data is not None else event
                return [self._trajectory_tool(tool_ev)]

        raise ValueError(f"Unsupported upstream event type: {event_type!r}")


async def stream_agui_sse_bytes(
    upstream_events: AsyncIterator[Mapping[str, Any]],
    *,
    session_id: str,
    prompt: str,
    agent: str,
) -> AsyncIterator[bytes]:
    translator = AGUIStreamTranslator(session_id=session_id, prompt=prompt, agent=agent)
    # Emit intent as soon as streaming starts (gateway-level "Understanding Frame").
    yield sse_encode_event(translator._intent_event()).encode("utf-8")

    async for raw in upstream_events:
        for ev in translator.translate(raw):
            yield sse_encode_event(ev).encode("utf-8")
