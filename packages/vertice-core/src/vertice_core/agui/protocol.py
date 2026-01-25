"""
AG-UI MVP protocol (stability-first).

This defines a minimal, predictable event envelope for streaming over SSE:
  - delta: incremental assistant output
  - final: terminal assistant output + optional metadata
  - tool: tool call / tool result (optional, for observability)
  - error: terminal error

Wire format: Server-Sent Events (SSE)
  event: <type>
  data: <json>

The JSON payload always validates as AGUIEvent.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AGUIEventType(str, Enum):
    DELTA = "delta"
    FINAL = "final"
    TOOL = "tool"
    ERROR = "error"


class AGUIDeltaData(BaseModel):
    text: str


class AGUIFinalData(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AGUIToolData(BaseModel):
    name: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    status: str = "ok"  # ok|error


class AGUIErrorData(BaseModel):
    message: str
    code: str = "unknown"
    details: Dict[str, Any] = Field(default_factory=dict)


class AGUIEvent(BaseModel):
    """
    Stable envelope for all streamed events.

    Notes:
    - `id` is per-event (UUID4). Clients can use it for de-duplication.
    - `ts` is UTC ISO8601 for easy ingestion/logging.
    - `data` is a dict payload shaped by `type` (validated by the gateway).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: AGUIEventType
    session_id: str = "default"
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def delta(cls, text: str, *, session_id: str = "default") -> "AGUIEvent":
        payload = AGUIDeltaData(text=text).model_dump()
        return cls(type=AGUIEventType.DELTA, session_id=session_id, data=payload)

    @classmethod
    def final(
        cls,
        text: str,
        *,
        session_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AGUIEvent":
        payload = AGUIFinalData(text=text, metadata=metadata or {}).model_dump()
        return cls(type=AGUIEventType.FINAL, session_id=session_id, data=payload)

    @classmethod
    def tool(
        cls,
        name: str,
        *,
        session_id: str = "default",
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        status: str = "ok",
    ) -> "AGUIEvent":
        payload = AGUIToolData(
            name=name,
            input=input or {},
            output=output,
            status=status,
        ).model_dump()
        return cls(type=AGUIEventType.TOOL, session_id=session_id, data=payload)

    @classmethod
    def error(
        cls,
        message: str,
        *,
        session_id: str = "default",
        code: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ) -> "AGUIEvent":
        payload = AGUIErrorData(message=message, code=code, details=details or {}).model_dump()
        return cls(type=AGUIEventType.ERROR, session_id=session_id, data=payload)


def sse_encode_event(event: AGUIEvent) -> str:
    """
    Encode an AGUIEvent to SSE payload.

    We keep it intentionally simple and predictable to maximize compatibility.
    """

    data = json.dumps(event.model_dump(), separators=(",", ":"), ensure_ascii=False)
    return f"event: {event.type.value}\ndata: {data}\n\n"
