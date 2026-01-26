from __future__ import annotations

import os

import pytest

from vertice_core.providers.vertex_ai import VertexAIProvider


def test_vertex_ai_provider_location_prefers_explicit_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    p = VertexAIProvider(project="p1", location="global", model_name="pro")
    assert p.location == "global"


def test_vertex_ai_provider_location_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")
    p = VertexAIProvider(project="p1", location="", model_name="pro")
    assert p.location == "us-central1"

    monkeypatch.delenv("VERTEX_AI_LOCATION", raising=False)
    p = VertexAIProvider(project="p1", location="", model_name="pro")
    assert p.location == "global"
