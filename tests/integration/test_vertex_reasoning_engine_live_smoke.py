from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_VERTEX_LIVE_TESTS", "0").strip() not in {"1", "true", "yes", "on"},
    reason="live Vertex test (set RUN_VERTEX_LIVE_TESTS=1 to enable)",
)
def test_reasoning_engine_live_query_smoke() -> None:
    """
    Live smoke test against a deployed Vertex ReasoningEngine/Agent Engine resource.

    Preconditions (local/dev machine):
      - Working DNS/network access to *.googleapis.com
      - ADC configured (e.g. `gcloud auth application-default login`)
      - `apps/agent-gateway/config/engines.json` contains a `coder` engine_id.
    """

    import vertexai  # type: ignore
    from vertexai import agent_engines  # type: ignore

    cfg_path = (
        Path(__file__).resolve().parents[2] / "apps" / "agent-gateway" / "config" / "engines.json"
    )
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    spec = raw["engines"]["coder"]
    engine_id = spec["engine_id"]
    project = spec["project"]
    location = spec.get("location", "us-central1")

    vertexai.init(project=project, location=location)
    app = agent_engines.get(resource_name=engine_id)

    resp = app.query(input='Say exactly "ok".')
    assert isinstance(resp, dict)
    assert "output" in resp
    assert isinstance(resp["output"], str)
    assert resp["output"].strip()
