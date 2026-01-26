from __future__ import annotations

import sys
import types
from collections.abc import AsyncIterator

import pytest

from vertice_core.agui.vertex_agent_engine import (
    VertexAgentEngineSpec,
    stream_vertex_agent_engine_adk_events,
)


class _FakeRemoteApp:
    def __init__(self, *, output: str) -> None:
        self._output = output

    def query(self, **kwargs):  # noqa: ANN003
        assert kwargs.get("input") == "ping"
        return {"output": self._output}


def _install_fake_vertexai(monkeypatch: pytest.MonkeyPatch, *, output: str) -> None:
    vertexai_mod = types.ModuleType("vertexai")

    def _init(*args, **kwargs):  # noqa: ANN002, ANN003
        return None

    vertexai_mod.init = _init  # type: ignore[attr-defined]

    agent_engines_mod = types.ModuleType("vertexai.agent_engines")

    def _get(*args, **kwargs):  # noqa: ANN002, ANN003
        return _FakeRemoteApp(output=output)

    agent_engines_mod.get = _get  # type: ignore[attr-defined]

    vertexai_mod.agent_engines = agent_engines_mod  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "vertexai", vertexai_mod)
    monkeypatch.setitem(sys.modules, "vertexai.agent_engines", agent_engines_mod)


async def _collect_events(it: AsyncIterator[dict]) -> list[dict]:
    out: list[dict] = []
    async for ev in it:
        out.append(ev)
    return out


@pytest.mark.asyncio
async def test_reasoning_engine_query_fallback_synthesizes_delta_and_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_vertexai(monkeypatch, output="hello world")
    spec = VertexAgentEngineSpec(
        engine_id="projects/p/locations/us-central1/reasoningEngines/123",
        project="p",
        location="us-central1",
    )

    events = await _collect_events(
        stream_vertex_agent_engine_adk_events(spec=spec, prompt="ping", session_id="s1")
    )

    assert events[0]["type"] == "delta"
    assert "hello" in events[0]["text"]
    assert events[-1]["type"] == "final"
    assert events[-1]["text"] == "hello world"
    assert events[-1]["metadata"]["mode"] == "reasoning_engine_query_fallback"
