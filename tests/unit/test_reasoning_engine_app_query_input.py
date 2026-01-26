from __future__ import annotations

import asyncio

import pytest

from agents.coder.reasoning_engine_app import CoderReasoningEngineApp


class _FakeProvider:
    async def generate(self, *args, **kwargs) -> str:  # noqa: ANN001, ANN002, ANN003
        await asyncio.sleep(0)
        return "OK"


@pytest.mark.asyncio
async def test_reasoning_engine_app_query_accepts_input_str() -> None:
    app = CoderReasoningEngineApp()
    app._provider = _FakeProvider()  # type: ignore[attr-defined]

    out = await app.query(input="ping")
    assert out["output"] == "OK"


@pytest.mark.asyncio
async def test_reasoning_engine_app_query_accepts_input_mapping_variants() -> None:
    app = CoderReasoningEngineApp()
    app._provider = _FakeProvider()  # type: ignore[attr-defined]

    out = await app.query(input={"message": "ping"})
    assert out["output"] == "OK"


@pytest.mark.asyncio
async def test_reasoning_engine_app_query_rejects_empty_prompt() -> None:
    app = CoderReasoningEngineApp()
    with pytest.raises(ValueError):
        await app.query(input="   ")
