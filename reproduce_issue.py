import asyncio
import contextvars
from vertice_tui.app import VerticeApp


async def main():
    print(f"Main start context: {id(contextvars.copy_context())}")

    app = VerticeApp()

    # Mock bridge to avoid external dependencies
    class MockBridge:
        def __init__(self):
            self.responses = {}
            self.prometheus_mode = False
            self.is_connected = True
            self._provider_mode = "auto"
            self.agents = type("MockAgents", (), {"available_agents": []})()
            self.tools = type("MockTools", (), {"get_tool_count": lambda: 0})()
            self.governance = type("MockGovernance", (), {"get_status_emoji": lambda: "🟢"})()
            self.history = type("MockHistory", (), {"clear_context": lambda self: None})()
            self.autocomplete = type("MockAutocomplete", (), {"get_completions": lambda t, m: []})()
            self.llm = type("MockLLM", (), {"_vertice_client": None})()

        async def warmup(self):
            pass

    app.bridge = MockBridge()

    print("Entering app.run_test()...")
    try:
        async with app.run_test() as pilot:
            print(f"Inside run_test context: {id(contextvars.copy_context())}")
            await pilot.pause(0.1)
            print("Exiting run_test...")
    except Exception as e:
        print(f"CAUGHT ERROR: {e}")
        import traceback

        traceback.print_exc()
    else:
        print("Success!")


if __name__ == "__main__":
    asyncio.run(main())
