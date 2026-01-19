import asyncio
import os
import sys
import time

# Ensure src is in path
sys.path.append(os.getcwd())

TASK_PROMPT = """
Implement a robust, production-ready 'AsyncLRUCache' class in Python 3.11+.

Requirements:
1. **Thread-Safe**: Must use asyncio primitives (Locks) to handle concurrent access.
2. **TTL Support**: Each item should have a Time-To-Live. Accessing expired items should treat them as missing.
3. **Eviction Callback**: An optional callback `on_evict(key, value)` should be awaited when an item is removed (due to size limit or TTL).
4. **Data Structures**: Use efficient structures (e.g., OrderedDict) for O(1) access and eviction.
5. **Methods**: `get(key)`, `put(key, value, ttl=None)`, `size()`, `clear()`.

Return ONLY the Python code. No markdown, no explanations.
"""


async def run_single_provider(name, provider_cls, **kwargs):
    print(f"🔹 Starting {name}...")
    try:
        provider = provider_cls(**kwargs)
        start = time.time()
        # 60s timeout for generation
        response = await asyncio.wait_for(
            provider.generate([{"role": "user", "content": TASK_PROMPT}]), timeout=60.0
        )
        duration = time.time() - start
        print(f"✅ {name} finished in {duration:.2f}s")
        return {"name": name, "model": provider.model_name, "time": duration, "code": response}
    except asyncio.TimeoutError:
        print(f"❌ {name} TIMED OUT (>60s)")
        return None
    except Exception as e:
        print(f"❌ {name} FAILED: {e}")
        return None


async def run_benchmark():
    print("🚀 Starting Concurrent Benchmark: DeepSeek V3 vs Gemini 2.5 Pro")
    print("=" * 60)

    from src.providers.nebius import NebiusProvider
    from src.providers.vertex_ai import VertexAIProvider

    # Run in parallel
    tasks = [
        run_single_provider("Nebius (DeepSeek)", NebiusProvider),
        run_single_provider(
            "Vertex (Gemini)", VertexAIProvider, model_name="gemini-2.5-pro", location="us-central1"
        ),
    ]

    results = await asyncio.gather(*tasks)

    print("=" * 60)

    # Save Outputs
    os.makedirs("benchmark_results", exist_ok=True)

    valid_results = [r for r in results if r]

    for res in valid_results:
        filename = f"benchmark_results/{res['name'].split()[0].lower()}.py"
        with open(filename, "w") as f:
            f.write(res["code"])
        print(f"💾 Saved {res['name']} result to {filename}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
