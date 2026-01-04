import asyncio
import tempfile
from pathlib import Path

import pytest

from memory.cortex import MemoryCortex
from tests.benchmarks.utils import MIRIXBenchmark, SAMPLE_QUERIES


@pytest.fixture
def cortex():
    """Fresh cortex instance for each test, using a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)
        c = MemoryCortex(base_path=db_path)
        # Pre-populate for realistic retrieval
        for i in range(100):
            c.remember(f"Test memory entry {i}", memory_type="episodic", session_id="test_session")
        yield c


@pytest.fixture
def benchmark():
    return MIRIXBenchmark(num_queries=50)


@pytest.mark.asyncio
class TestMIRIXStress:
    """MIRIX stress test suite."""

    async def test_sequential_baseline(self, cortex, benchmark):
        """Baseline: sequential query performance."""
        queries = (SAMPLE_QUERIES * 10)[:50]
        stats = await benchmark.run_sequential(cortex, queries)

        print(f"\n{'='*60}")
        print("SEQUENTIAL BASELINE")
        print(f"{'='*60}")
        for k, v in stats.items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

        assert stats["errors"] == 0, f"Errors occurred: {benchmark.errors}"
        assert stats.get("p99_ms", 1001) < 1000, f"p99 latency too high: {stats.get('p99_ms')}ms"

    async def test_concurrent_50_queries(self, cortex, benchmark):
        """Stress test: 50 concurrent queries."""
        queries = (SAMPLE_QUERIES * 10)[:50]
        stats = await benchmark.run_concurrent(cortex, queries)

        print(f"\n{'='*60}")
        print("CONCURRENT (50 queries, asyncio)")
        print(f"{'='*60}")
        for k, v in stats.items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

        assert stats["errors"] == 0
        assert stats.get("p99_ms", 501) < 500, f"p99 too high under load: {stats.get('p99_ms')}ms"

    async def test_connection_pool_efficiency(self, cortex, benchmark):
        """Verify connection pool prevents connection exhaustion."""
        queries = ["quick test"] * 100
        stats = await benchmark.run_concurrent(cortex, queries)

        print(f"\n{'='*60}")
        print("CONNECTION POOL STRESS (100 rapid queries)")
        print(f"{'='*60}")
        for k, v in stats.items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

        assert stats["errors"] == 0, "Connection pool failed under stress"
