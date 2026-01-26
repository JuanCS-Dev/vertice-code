from __future__ import annotations

from pathlib import Path

import pytest


def test_deploy_brain_passes_runtime_packaging_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import deploy_brain as mod

    captured: dict = {}

    def _fake_create_reasoning_engine(**kwargs):
        captured.update(kwargs)
        return "engine-xyz"

    monkeypatch.setattr(mod, "_create_reasoning_engine", _fake_create_reasoning_engine)

    cfg = tmp_path / "engines.json"
    mod.deploy_brain(
        agent="coder",
        project="test-project",
        location="us-central1",
        display_name="vertice-coder",
        engines_config_path=cfg,
        dry_run=False,
        staging_bucket="gs://vertice-ai-reasoning-staging",
        requirements=["google-cloud-aiplatform"],
        extra_packages=["/tmp/pkg"],
        sys_version="3.11",
    )

    assert captured["project"] == "test-project"
    assert captured["location"] == "us-central1"
    assert captured["staging_bucket"] == "gs://vertice-ai-reasoning-staging"
    assert captured["requirements"] == ["google-cloud-aiplatform"]
    assert captured["extra_packages"] == ["/tmp/pkg"]
    assert captured["sys_version"] == "3.11"
