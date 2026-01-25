import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from vertice_tui.core.ui_bridge import AutocompleteBridge  # noqa: E402
from vertice_tui.core.bridge import Bridge  # noqa: E402
from vertice_core.clients.vertice_coreent import VerticeClient  # noqa: E402


async def benchmark_input_latency():
    print("\n⚡ BENCHMARK: INPUT LATENCY (AutocompleteBridge)")
    bridge = AutocompleteBridge()

    # Warmup
    bridge.get_completions("te")

    start = time.time()
    iterations = 100
    for _ in range(iterations):
        bridge.get_completions("test_input_string")

    total = (time.time() - start) * 1000
    avg = total / iterations

    print(f"Total time ({iterations} ops): {total:.2f}ms")
    print(f"Average latency per key: {avg:.4f}ms")

    if avg < 1.0:
        print("✅ Input Latency: EXCELLENT (<1ms)")
    elif avg < 16.0:
        print("✅ Input Latency: GOOD (<16ms/60fps)")
    else:
        print("❌ Input Latency: POOR (>16ms)")


async def benchmark_system_prompt():
    print("\n⚡ BENCHMARK: SYSTEM PROMPT GENERATION (Bridge)")

    # Bridge initialized without app
    bridge = Bridge()

    # First call (Uncached - simulating cold start)
    start = time.time()
    bridge._get_system_prompt()
    first_call = (time.time() - start) * 1000
    print(f"Cold Call (Git access): {first_call:.2f}ms")

    # Second call (Cached)
    start = time.time()
    for _ in range(10):
        bridge._get_system_prompt()
    avg_cached = ((time.time() - start) * 1000) / 10
    print(f"Cached Call: {avg_cached:.4f}ms")

    if avg_cached < 1.0:
        print("✅ System Prompt Cache: WORKING (<1ms)")
    else:
        print("❌ System Prompt Cache: FAILED (>1ms)")


async def verify_tool_routing():
    print("\n⚡ VERIFICATION: TOOL ROUTING (VerticeClient)")
    client = VerticeClient()

    import inspect

    source = inspect.getsource(client.stream_open_responses)

    if "tools = kwargs.pop" in source and "tools=tools" in source:
        print("✅ Static Analysis: stream_open_responses passes 'tools' correctly.")
    else:
        print("❌ Static Analysis: stream_open_responses MISSING tools passthrough!")


async def main():
    print("🚀 STARTING TUI PERFORMANCE AUDIT")
    print("=================================")

    await benchmark_input_latency()
    await benchmark_system_prompt()
    await verify_tool_routing()

    print("\n=================================")
    print("🏁 AUDIT COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
