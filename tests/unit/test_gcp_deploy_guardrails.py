from __future__ import annotations

import inspect


def test_coder_reasoning_engine_app_query_contract() -> None:
    from agents.coder.reasoning_engine_app import CoderReasoningEngineApp

    assert inspect.iscoroutinefunction(CoderReasoningEngineApp.query)
    sig = inspect.signature(CoderReasoningEngineApp.query)
    assert "input" in sig.parameters
    assert sig.parameters["input"].kind is inspect.Parameter.KEYWORD_ONLY


def test_deploy_brain_rejects_global_location() -> None:
    from pathlib import Path

    import pytest

    from tools.deploy_brain import DeployBrainError, deploy_brain

    with pytest.raises(DeployBrainError, match="location='global'"):
        deploy_brain(
            agent="coder",
            project="vertice-ai",
            location="global",
            display_name="vertice-coder",
            engines_config_path=Path("apps/agent-gateway/config/engines.json"),
            dry_run=True,
        )


def test_cloudbuild_configs_reference_repo_root_context() -> None:
    backend = (open("cloudbuild.backend.yaml", encoding="utf-8").read(), "cloudbuild.backend.yaml")
    mcp = (open("cloudbuild.mcp.yaml", encoding="utf-8").read(), "cloudbuild.mcp.yaml")

    for txt, name in [backend, mcp]:
        assert "gcr.io/cloud-builders/docker" in txt, name
        assert "- 'build'" in txt or " - 'build'" in txt or "build" in txt, name
        assert (
            " - '.'" in txt
            or "\n      - '.'\n" in txt
            or "\n      - '.'" in txt
            or "\n      - .\n" in txt
        ), name

    assert "Dockerfile.backend" in backend[0]
    assert "vertice-cloud/backend" in backend[0]
    assert "Dockerfile.mcp" in mcp[0]
    assert "vertice-cloud/mcp-server" in mcp[0]


def test_dockerfile_backend_cloud_run_port_contract() -> None:
    txt = open("Dockerfile.backend", encoding="utf-8").read()
    assert "python:3.11-slim" in txt
    assert "--host" in txt and "0.0.0.0" in txt
    assert "${PORT" in txt


def test_vertex_provider_has_no_gemini_1_2_model_ids() -> None:
    import re

    txt = open(
        "packages/vertice-core/src/vertice_core/providers/vertex_ai.py", encoding="utf-8"
    ).read()
    assert re.search(r"\\bgemini-(?:1|2)(?:\\.|\\b)", txt, flags=re.IGNORECASE) is None
