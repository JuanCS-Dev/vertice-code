import asyncio
import statistics
import time
from typing import List, Dict, Any

from memory.cortex import MemoryCortex


class MIRIXBenchmark:
    """Stress test harness for MIRIX memory system."""

    def __init__(self, num_queries: int = 50):
        self.num_queries = num_queries
        self.results: List[float] = []
        self.errors: List[str] = []

    async def _single_query(self, cortex: MemoryCortex, query: str) -> float:
        """Execute single query and return latency in ms."""
        start = time.perf_counter()
        try:
            await cortex.active_retrieve(query)
        except Exception as e:
            self.errors.append(str(e))
        return (time.perf_counter() - start) * 1000  # ms

    async def run_sequential(self, cortex: MemoryCortex, queries: List[str]) -> Dict[str, float]:
        """Run queries sequentially (baseline)."""
        self.results = []
        self.errors = []
        for q in queries:
            latency = await self._single_query(cortex, q)
            self.results.append(latency)
        return self._calculate_stats()

    async def run_concurrent(self, cortex: MemoryCortex, queries: List[str]) -> Dict[str, float]:
        """Run queries concurrently with asyncio."""
        self.results = []
        self.errors = []
        tasks = [self._single_query(cortex, q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                self.errors.append(str(res))
            else:
                self.results.append(res)

        return self._calculate_stats()

    def _calculate_stats(self) -> Dict[str, float]:
        """Calculate latency statistics."""
        if not self.results:
            return {"errors": len(self.errors)}
        sorted_results = sorted(self.results)
        return {
            "count": len(self.results),
            "min_ms": min(self.results),
            "max_ms": max(self.results),
            "mean_ms": statistics.mean(self.results),
            "median_ms": statistics.median(self.results),
            "p50_ms": sorted_results[int(len(sorted_results) * 0.50)],
            "p95_ms": sorted_results[int(len(sorted_results) * 0.95)],
            "p99_ms": sorted_results[int(len(sorted_results) * 0.99)] if len(sorted_results) >= 100 else sorted_results[-1],
            "stddev_ms": statistics.stdev(self.results) if len(self.results) > 1 else 0,
            "errors": len(self.errors),
        }


# Sample queries for realistic workload
SAMPLE_QUERIES = [
    "How do I implement authentication?",
    "What is the architecture of the system?",
    "Show me error handling patterns",
    "Database connection setup",
    "API endpoint implementation",
]
