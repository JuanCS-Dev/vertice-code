from __future__ import annotations

import json
from pathlib import Path

import pytest


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_deploy_brain_dry_run_writes_engines_json(tmp_path: Path) -> None:
    from tools.deploy_brain import deploy_brain

    cfg = tmp_path / "engines.json"
    deployed = deploy_brain(
        agent="coder",
        project="test-project",
        location="global",
        display_name="vertice-coder-test",
        engines_config_path=cfg,
        dry_run=True,
    )

    assert deployed.agent == "coder"
    assert deployed.display_name == "vertice-coder-test"
    assert deployed.engine_id.startswith("dry-run://coder/")

    data = _read_json(cfg)
    assert "updated_at" in data
    assert data["engines"]["coder"]["engine_id"] == deployed.engine_id
    assert data["engines"]["coder"]["project"] == "test-project"


def test_deploy_brain_updates_existing_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import deploy_brain as mod

    cfg = tmp_path / "engines.json"
    cfg.write_text(
        json.dumps({"engines": {"reviewer": {"engine_id": "old"}}, "updated_at": "old"}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "_create_reasoning_engine", lambda **_: "engine-123")

    deployed = mod.deploy_brain(
        agent="coder",
        project="test-project",
        location="us-central1",
        display_name=None,
        engines_config_path=cfg,
        dry_run=False,
    )

    assert deployed.engine_id == "engine-123"
    data = _read_json(cfg)
    assert data["engines"]["reviewer"]["engine_id"] == "old"
    assert data["engines"]["coder"]["engine_id"] == "engine-123"
