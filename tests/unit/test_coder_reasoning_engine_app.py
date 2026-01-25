from __future__ import annotations

from importlib import import_module

import pytest


def test_coder_reasoning_engine_app_query(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools import deploy_brain

    deploy_brain._ensure_src_on_path()

    mod = import_module("agents.coder.reasoning_engine_app")

    class FakeProvider:
        def __init__(self, **_kwargs):
            pass

        async def generate(self, *args, **kwargs) -> str:  # noqa: ANN001, D401
            return "ok"

    monkeypatch.setattr(mod, "VertexAIProvider", FakeProvider)

    app = mod.CoderReasoningEngineApp(project="test-project", location="global", model="pro")
    out = app.query(description="generate hello world", language="python", style="minimal")
    assert out["output"] == "ok"


def test_coder_reasoning_engine_app_requires_description(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools import deploy_brain

    deploy_brain._ensure_src_on_path()
    mod = import_module("agents.coder.reasoning_engine_app")

    class FakeProvider:
        def __init__(self, **_kwargs):
            pass

        async def generate(self, *args, **kwargs) -> str:  # noqa: ANN001
            return "ok"

    monkeypatch.setattr(mod, "VertexAIProvider", FakeProvider)

    app = mod.CoderReasoningEngineApp(project="test-project")
    with pytest.raises(ValueError, match="description"):
        app.query()
