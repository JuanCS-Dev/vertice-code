import pytest

from vertice_tui.app import VerticeApp


class _MockBridge:
    """Minimal bridge for `VerticeApp` startup in `run_test()`."""

    def __init__(self) -> None:
        self.prometheus_mode = False
        self.is_connected = True
        self._provider_mode = "auto"
        self.model_name = "mock"

        self.agents = type("_Agents", (), {"available_agents": []})()
        self.tools = type("_Tools", (), {"get_tool_count": staticmethod(lambda: 0)})()
        self.governance = type("_Gov", (), {"get_status_emoji": staticmethod(lambda: "🟢")})()
        self.history = type("_History", (), {"clear_context": lambda self: None})()
        self.autocomplete = type(
            "_Autocomplete",
            (),
            {"get_completions": staticmethod(lambda _text, max_results=15: [])},
        )()
        self.llm = type("_LLM", (), {"_vertice_coreent": None})()

    async def warmup(self) -> None:
        return None

    def execute_custom_command(self, _cmd_name, _args):
        return None


@pytest.mark.asyncio
async def test_run_test_teardown_contextvars_stability() -> None:
    """
    Regression test for:
      ValueError: ContextVar Token was created in a different Context

    We repeatedly enter/exit `app.run_test()` to catch teardown-context regressions.
    """
    for _ in range(15):
        app = VerticeApp()
        app.bridge = _MockBridge()
        async with app.run_test() as pilot:
            await pilot.pause(0)
