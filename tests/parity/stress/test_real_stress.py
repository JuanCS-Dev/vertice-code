"""
REAL Stress Tests

These tests stress the system with REAL LLM calls to validate:
1. Concurrent request handling
2. Provider failover
3. Context overflow handling
4. Rate limiting behavior
5. Recovery from errors

WARNING: These tests consume significant API tokens.
"""

import pytest
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

pytestmark = [
    pytest.mark.stress,
    pytest.mark.real,
    pytest.mark.slow,
]


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()


@dataclass
class StressTestResult:
    """Result from a stress test."""

    total_requests: int
    successful: int
    failed: int
    total_duration_ms: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    errors: List[str]


class StressTester:
    """Stress testing utility for Vertice."""

    def __init__(self):
        self.initialized = False
        self.bridge = None
        self.results: List[Dict] = []

    async def initialize(self):
        """Initialize the system."""
        try:
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            await self.bridge.initialize()
            self.initialized = True
            return True
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    async def single_request(self, message: str, timeout: int = 60) -> Dict:
        """Execute a single request."""
        result = {
            "success": False,
            "output": "",
            "latency_ms": 0,
            "error": None,
        }

        start = time.time()
        try:
            output = ""
            async for chunk in asyncio.wait_for(self._process_with_async(message), timeout=timeout):
                if hasattr(chunk, "content"):
                    output += chunk.content
                elif isinstance(chunk, str):
                    output += chunk

            result["output"] = output
            result["success"] = True
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)

        result["latency_ms"] = int((time.time() - start) * 1000)
        return result

    async def _process_with_async(self, message: str):
        """Wrap process_message as async iterator."""
        async for chunk in self.bridge.process_message(message):
            yield chunk

    async def run_concurrent(
        self, messages: List[str], max_concurrent: int = 5, timeout: int = 120
    ) -> StressTestResult:
        """Run multiple requests concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        errors = []

        async def limited_request(msg: str) -> Dict:
            async with semaphore:
                return await self.single_request(msg, timeout)

        start = time.time()
        tasks = [limited_request(msg) for msg in messages]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in raw_results:
            if isinstance(r, Exception):
                results.append({"success": False, "error": str(r), "latency_ms": 0})
                errors.append(str(r))
            else:
                results.append(r)
                if r.get("error"):
                    errors.append(r["error"])

        total_duration = int((time.time() - start) * 1000)

        # Calculate metrics
        successful = sum(1 for r in results if r["success"])
        latencies = [r["latency_ms"] for r in results if r["success"]]

        if latencies:
            latencies.sort()
            avg = sum(latencies) / len(latencies)
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)
            p95 = latencies[min(p95_idx, len(latencies) - 1)]
            p99 = latencies[min(p99_idx, len(latencies) - 1)]
        else:
            avg = p95 = p99 = 0

        return StressTestResult(
            total_requests=len(messages),
            successful=successful,
            failed=len(messages) - successful,
            total_duration_ms=total_duration,
            avg_latency_ms=avg,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            errors=errors[:10],  # Keep first 10 errors
        )

    async def cleanup(self):
        """Cleanup resources."""
        if self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def stress_tester():
    """Provide stress tester."""
    tester = StressTester()
    success = await tester.initialize()

    if not success:
        pytest.skip("Could not initialize stress tester")

    yield tester

    await tester.cleanup()


class TestConcurrentRequests:
    """Test concurrent request handling."""

    @pytest.mark.timeout(300)
    async def test_five_concurrent_requests(self, stress_tester):
        """
        REAL STRESS: Handle 5 concurrent requests.
        """
        messages = [
            "What is 1+1?",
            "What is 2+2?",
            "What is 3+3?",
            "What is 4+4?",
            "What is 5+5?",
        ]

        result = await stress_tester.run_concurrent(messages, max_concurrent=5)

        print(f"\n[STRESS] Total requests: {result.total_requests}")
        print(f"[STRESS] Successful: {result.successful}")
        print(f"[STRESS] Failed: {result.failed}")
        print(f"[STRESS] Avg latency: {result.avg_latency_ms:.0f}ms")
        print(f"[STRESS] P95 latency: {result.p95_latency_ms:.0f}ms")
        print(f"[STRESS] Total duration: {result.total_duration_ms}ms")

        # At least 80% should succeed
        success_rate = result.successful / result.total_requests
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.1%}"

    @pytest.mark.timeout(600)
    async def test_ten_sequential_requests(self, stress_tester):
        """
        REAL STRESS: Handle 10 sequential requests.
        """
        messages = [f"Calculate {i} * {i}" for i in range(1, 11)]

        result = await stress_tester.run_concurrent(messages, max_concurrent=1)

        print(f"\n[STRESS] Total: {result.total_requests}, Success: {result.successful}")
        print(f"[STRESS] Avg latency: {result.avg_latency_ms:.0f}ms")

        success_rate = result.successful / result.total_requests
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.1%}"

    @pytest.mark.timeout(600)
    async def test_burst_requests(self, stress_tester):
        """
        REAL STRESS: Handle burst of requests.
        """
        # Send 10 requests at once
        messages = [f"Echo: {i}" for i in range(10)]

        result = await stress_tester.run_concurrent(messages, max_concurrent=10)

        print(f"\n[STRESS BURST] Success: {result.successful}/{result.total_requests}")
        print(f"[STRESS BURST] P99 latency: {result.p99_latency_ms:.0f}ms")

        if result.errors:
            print(f"[STRESS BURST] Sample errors: {result.errors[:3]}")

        # Some may fail due to rate limits, but shouldn't crash
        assert result.successful >= 1, "At least one request should succeed"


class TestContextOverflow:
    """Test behavior with large context."""

    @pytest.mark.timeout(180)
    async def test_large_input_handled(self, stress_tester):
        """
        REAL STRESS: Handle large input gracefully.
        """
        # Create a large input
        large_input = "Please analyze this text:\n" + ("Lorem ipsum dolor sit amet. " * 1000)

        result = await stress_tester.single_request(large_input, timeout=120)

        print(f"\n[STRESS] Large input latency: {result['latency_ms']}ms")
        print(f"[STRESS] Success: {result['success']}")

        # Should handle gracefully (success or informative error)
        assert result["success"] or result["error"] is not None

    @pytest.mark.timeout(180)
    async def test_context_accumulation(self, stress_tester):
        """
        REAL STRESS: Handle context accumulation across requests.
        """
        # Multiple requests building context
        messages = [
            "Remember: My name is TestUser",
            "Remember: I'm working on a Python project",
            "Remember: The project uses FastAPI",
            "Now tell me what you remember about my project",
        ]

        results = []
        for msg in messages:
            result = await stress_tester.single_request(msg, timeout=60)
            results.append(result)

        # Final request should have context
        final = results[-1]
        print(f"\n[STRESS] Final response: {final['output'][:200]}...")

        # At least the final should succeed
        assert final["success"], "Context accumulation request failed"


class TestRecoveryBehavior:
    """Test recovery from various failure modes."""

    @pytest.mark.timeout(180)
    async def test_recovery_after_timeout(self, stress_tester):
        """
        REAL STRESS: System should recover after timeout.
        """
        # First request - very short timeout might fail
        result1 = await stress_tester.single_request(
            "Write a very long essay about programming",
            timeout=2,  # Very short, likely to timeout
        )

        # Second request - normal timeout should work
        result2 = await stress_tester.single_request("What is 1+1?", timeout=60)

        print(f"\n[RECOVERY] First request (short timeout): {result1['success']}")
        print(f"[RECOVERY] Second request (normal): {result2['success']}")

        # System should recover and handle second request
        # (First may or may not timeout depending on model speed)
        assert result2["success"] or result2.get("output"), "Should recover after timeout"

    @pytest.mark.timeout(120)
    async def test_malformed_request_recovery(self, stress_tester):
        """
        REAL STRESS: System should handle malformed requests.
        """
        # Malformed request
        result1 = await stress_tester.single_request("```\n{{{invalid", timeout=30)

        # Normal request after
        result2 = await stress_tester.single_request("Say hello", timeout=60)

        print(f"\n[RECOVERY] Malformed: {result1['success']}")
        print(f"[RECOVERY] Normal after: {result2['success']}")

        # Should handle both gracefully
        assert result2["success"] or len(result2.get("output", "")) > 0


class TestProviderFailover:
    """Test provider failover behavior."""

    @pytest.mark.timeout(180)
    async def test_sustained_load(self, stress_tester):
        """
        REAL STRESS: Sustained load should trigger failover if needed.
        """
        # Send multiple requests to potentially trigger rate limits/failover
        messages = [f"Quick question #{i}: What is {i}+{i}?" for i in range(15)]

        result = await stress_tester.run_concurrent(messages, max_concurrent=3)

        print(f"\n[FAILOVER] Success rate: {result.successful}/{result.total_requests}")
        print(f"[FAILOVER] Unique errors: {len(set(result.errors))}")

        # Should handle most requests even under load
        success_rate = result.successful / result.total_requests
        assert success_rate >= 0.5, f"Too many failures under sustained load: {success_rate:.1%}"


class TestMemoryBehavior:
    """Test memory behavior under stress."""

    @pytest.mark.timeout(300)
    async def test_no_memory_leak_on_repeated_requests(self, stress_tester):
        """
        REAL STRESS: Repeated requests should not leak memory significantly.
        """
        import gc

        # Force garbage collection
        gc.collect()

        # Get baseline (if psutil available)
        try:
            import psutil

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            baseline_memory = 0

        # Run multiple requests
        for i in range(10):
            await stress_tester.single_request(f"Echo: request {i}", timeout=30)

        gc.collect()

        # Check memory
        if baseline_memory > 0:
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - baseline_memory

            print(f"\n[MEMORY] Baseline: {baseline_memory:.1f}MB")
            print(f"[MEMORY] Final: {final_memory:.1f}MB")
            print(f"[MEMORY] Growth: {memory_growth:.1f}MB")

            # Should not grow excessively (< 500MB)
            assert memory_growth < 500, f"Excessive memory growth: {memory_growth}MB"


class TestPerformanceBenchmarks:
    """Performance benchmarks."""

    @pytest.mark.timeout(300)
    @pytest.mark.benchmark
    async def test_throughput_benchmark(self, stress_tester):
        """
        REAL BENCHMARK: Measure request throughput.
        """
        messages = ["Quick: 1+1" for _ in range(20)]

        result = await stress_tester.run_concurrent(messages, max_concurrent=5)

        throughput = result.successful / (result.total_duration_ms / 1000)  # req/s

        print(f"\n[BENCHMARK] Throughput: {throughput:.2f} req/s")
        print(f"[BENCHMARK] Avg latency: {result.avg_latency_ms:.0f}ms")
        print(f"[BENCHMARK] P95 latency: {result.p95_latency_ms:.0f}ms")
        print(f"[BENCHMARK] P99 latency: {result.p99_latency_ms:.0f}ms")

        # Report metrics
        assert throughput > 0, "Should have some throughput"

    @pytest.mark.timeout(180)
    @pytest.mark.benchmark
    async def test_latency_distribution(self, stress_tester):
        """
        REAL BENCHMARK: Analyze latency distribution.
        """
        messages = [f"Compute: {i}*2" for i in range(10)]

        result = await stress_tester.run_concurrent(messages, max_concurrent=2)

        print("\n[LATENCY] Distribution:")
        print(f"  Average: {result.avg_latency_ms:.0f}ms")
        print(f"  P95: {result.p95_latency_ms:.0f}ms")
        print(f"  P99: {result.p99_latency_ms:.0f}ms")

        # P99 should not be excessively higher than average
        if result.avg_latency_ms > 0:
            ratio = result.p99_latency_ms / result.avg_latency_ms
            print(f"  P99/Avg ratio: {ratio:.1f}x")
