from __future__ import annotations

import pytest

from vertice_core.agui.ag_ui_adk import adk_event_to_agui
from vertice_core.agui.protocol import AGUIEventType


def test_adk_event_to_agui_delta() -> None:
    event = adk_event_to_agui({"type": "delta", "text": "hi"}, session_id="s1")
    assert event.type == AGUIEventType.DELTA
    assert event.session_id == "s1"
    assert event.data["text"] == "hi"


def test_adk_event_to_agui_final_with_metadata() -> None:
    event = adk_event_to_agui(
        {"type": "final", "text": "done", "metadata": {"k": "v"}},
        session_id="s1",
    )
    assert event.type == AGUIEventType.FINAL
    assert event.data["text"] == "done"
    assert event.data["metadata"]["k"] == "v"


def test_adk_event_to_agui_tool() -> None:
    event = adk_event_to_agui(
        {"type": "tool", "name": "search", "input": {"q": "x"}, "output": {"ok": True}},
        session_id="s2",
    )
    assert event.type == AGUIEventType.TOOL
    assert event.data["name"] == "search"
    assert event.data["input"]["q"] == "x"
    assert event.data["output"]["ok"] is True


def test_adk_event_to_agui_error() -> None:
    event = adk_event_to_agui(
        {"type": "error", "message": "boom", "code": "x", "details": {"a": 1}},
        session_id="s3",
    )
    assert event.type == AGUIEventType.ERROR
    assert event.data["message"] == "boom"
    assert event.data["code"] == "x"
    assert event.data["details"]["a"] == 1


def test_adk_event_to_agui_unknown_type_raises() -> None:
    with pytest.raises(ValueError):
        adk_event_to_agui({"type": "wat"}, session_id="s1")
