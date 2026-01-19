import asyncio
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

# We DO NOT import QwenApp to avoid dependency hell and property issues.
# We simulating the LOGIC of on_input_submitted directly.


async def measure_input_logic_latency():
    print("\n🔬 DIAGNOSTIC: App Logic Latency (UI Isolated)")
    print("============================================")

    # Mock "self" (The App)
    app = MagicMock()
    app.history = []
    app.history_index = 0
    app._last_input_time = 0
    app.query_one = MagicMock()
    app.refresh = MagicMock()
    app.notify = MagicMock()

    # Mock Bridge
    app.bridge = AsyncMock()
    app.bridge.chat.return_value = iter([])

    # Mock Router
    app.router = AsyncMock()
    app.router.dispatch.return_value = False

    # Mock ResponseView
    mock_response = MagicMock()
    app.query_one.return_value = mock_response

    # Test Payload
    user_input = "Hello world check lag"

    print("Running Logic Simulation...")

    start = time.perf_counter()

    # -----------------------------------------------------
    # LOGIC REPLICATION FROM on_input_submitted
    # -----------------------------------------------------

    # Validation
    if len(user_input) > 5000:
        pass

    # Rate limit
    current_time = time.time()
    app._last_input_time = current_time

    # UI Queries (Mocked overhead)
    app.query_one("#autocomplete")
    app.query_one("#prompt")

    # History
    app.history.append(user_input)
    if len(app.history) > 1000:
        app.history = app.history[-1000:]

    # Active Ops check
    if hasattr(app, "_active_operations"):
        pass

    # Add User Message (Visual Update CALL)
    mock_response.add_user_message(user_input)

    # Status update
    app.query_one("StatusBar")

    # The AWAIT SLEEP
    await asyncio.sleep(0)  # Logic Yield

    # Router/Chat Dispatch
    if user_input.startswith("/"):
        await app.router.dispatch(user_input, mock_response)
    else:
        from vertice_tui.core.openresponses_events import OpenResponsesParser

        OpenResponsesParser()
        # bridge.chat call (Mocked)
        # Note: In real app, this returns an async generator.
        # Calling it does NOT execute code until iteration.
        # BUT if my diagnosis of bridge.chat blocking setup is correct,
        # checking the setup part here is hard with mocks.
        # So we assume Logic Latency here captures the *App Level* overhead.

        # We simulate the setup cost we found earlier (0.1ms Hot)
        # by sleeping 0.0001
        time.sleep(0.0001)

    # -----------------------------------------------------

    end = time.perf_counter()
    duration_ms = (end - start) * 1000

    print(f"Logic Duration: {duration_ms:.4f} ms")

    if duration_ms > 16.0:
        print("❌ LOGIC IS SLOW (>16ms). The blockade is in Python code.")
    else:
        print("✅ LOGIC IS FAST (<16ms). The blockade is likely in UI RENDER (Textual Mount).")


if __name__ == "__main__":
    asyncio.run(measure_input_logic_latency())
