from __future__ import annotations

import json

from vertice_core.agui.protocol import AGUIEvent, AGUIEventType, sse_encode_event


def test_sse_encode_event_roundtrip_json() -> None:
    event = AGUIEvent.final("hello", session_id="s1", metadata={"k": "v"})

    sse = sse_encode_event(event)
    assert sse.startswith("event: final\n")
    assert "\ndata: " in sse
    assert sse.endswith("\n\n")

    # Extract JSON portion
    data_line = [line for line in sse.splitlines() if line.startswith("data: ")][0]
    payload = json.loads(data_line.removeprefix("data: "))

    assert payload["type"] == AGUIEventType.FINAL.value
    assert payload["session_id"] == "s1"
    assert payload["data"]["text"] == "hello"
    assert payload["data"]["metadata"]["k"] == "v"
