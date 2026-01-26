from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_stream_module():
    repo_root = Path(__file__).resolve().parents[2]
    stream_path = repo_root / "apps" / "agent-gateway" / "api" / "stream.py"
    spec = importlib.util.spec_from_file_location("agent_gateway_stream", stream_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_thought_stream_splitter_handles_boundary_spans() -> None:
    m = _load_stream_module()
    splitter = m.ThoughtStreamSplitter()

    out = []
    out += splitter.feed("hello <th")
    out += splitter.feed("ought>sec")
    out += splitter.feed("ret</thought> world")
    out += splitter.flush()

    deltas = "".join(text for kind, text in out if kind == "delta")
    thoughts = "".join(text for kind, text in out if kind == "thought")
    assert deltas == "hello  world"
    assert thoughts == "secret"


def test_strip_thought_blocks_removes_content() -> None:
    m = _load_stream_module()
    assert m.strip_thought_blocks("a <thought>x</thought> b") == "a b"
