import time
import inspect
import asyncio


class MockProvider:
    async def stream_chat(self, messages, tools=None, **kwargs):
        pass


async def measure_inspect_overhead():
    print("\n🔬 DIAGNOSTIC: inspect.signature Overhead")
    print("========================================")

    provider = MockProvider()

    # Cold run
    start = time.perf_counter()
    sig = inspect.signature(provider.stream_chat)
    end = time.perf_counter()
    print(f"Signature (Cold): {(end - start)*1000:.4f} ms")

    # Hot run loop
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        sig = inspect.signature(provider.stream_chat)
        if "tools" in sig.parameters:
            pass
    end = time.perf_counter()

    avg_ms = ((end - start) * 1000) / iterations
    print(f"Signature (Avg 1000 calls): {avg_ms:.4f} ms")

    if avg_ms > 1.0:
        print("❌ INSPECT IS VERY SLOW (>1ms)")
    elif avg_ms > 0.1:
        print("⚠️ INSPECT MIGHT ADD LAG (>0.1ms)")
    else:
        print("✅ INSPECT IS FAST")


if __name__ == "__main__":
    asyncio.run(measure_inspect_overhead())
