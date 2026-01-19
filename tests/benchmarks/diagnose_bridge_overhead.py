import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from vertice_tui.core.bridge import Bridge  # noqa: E402


class MockApp:
    pass


async def measure_chat_kickoff():
    print("\n🔬 DIAGNOSTIC: Bridge.chat Kickoff Latency")
    print("==========================================")

    bridge = Bridge()

    # Force minimal init
    try:
        bridge._safe_init(lambda: None, "test", False)
    except Exception:
        pass

    start = time.perf_counter()

    # Initialize generator but don't consume it fully yet
    # We want to measure how long until the FIRST chunk is yielded OR
    # how long it blocks before returning the generator/iterator.

    print("Calling bridge.chat()...")
    gen = bridge.chat("test message", auto_route=False)

    # Taking the first step implies running all pre-yield code
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass
    except Exception as e:
        # Expected since we don't have real LLM setup in this micro-benchmark
        # But we want to see if it crashed INSTANTLY or after thinking
        print(f"gen returned (with error, expected): {e}")

    end = time.perf_counter()
    duration_ms = (end - start) * 1000

    print(f"Cold Kickoff Duration: {duration_ms:.4f} ms")

    # HOT PATH BENCHMARK
    start = time.perf_counter()
    gen = bridge.chat("second message", auto_route=False)
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass
    except Exception:
        pass
    end = time.perf_counter()
    hot_duration_ms = (end - start) * 1000
    print(f"Hot Kickoff Duration: {hot_duration_ms:.4f} ms")

    if hot_duration_ms > 16.0:
        print("❌ BRIDGE HOT PATH IS BLOCKING (>16ms)")
    else:
        print("✅ BRIDGE HOT PATH IS FAST (<16ms)")


if __name__ == "__main__":
    asyncio.run(measure_chat_kickoff())
