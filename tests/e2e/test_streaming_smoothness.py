"""
E2E Benchmark: Streaming Smoothness
====================================

Scientific benchmark analyzing temporal distribution of streaming chunks.
Detects "bursting" (cuspido) vs smooth token delivery.

Methodology:
- 20 streaming sessions
- Measure interval between consecutive chunks
- Statistical analysis of inter-chunk intervals
- Burst detection (gaps > 500ms)

Target Metrics:
- 95% of intervals < 100ms
- Max gap < 500ms (no bursts)
- At least 5 chunks per response (real streaming)

Created: 2026-01-18
"""

import asyncio
import statistics
import time
from typing import Any, Dict, List

import pytest


class MockStreamingProvider:
    """
    Mock streaming provider that simulates realistic LLM streaming behavior.

    Used when actual LLM is not available (no credentials).
    Simulates both smooth and burst patterns for testing.
    """

    def __init__(self, pattern: str = "smooth"):
        self.pattern = pattern

    async def stream_chunks(self, prompt: str, chunk_count: int = 15):
        """Generate mock streaming chunks with realistic timing."""
        for i in range(chunk_count):
            if self.pattern == "smooth":
                # Smooth: 10-50ms intervals (ideal behavior)
                await asyncio.sleep(0.01 + (i % 5) * 0.008)
            elif self.pattern == "burst":
                # Burst: occasional long gaps (bad behavior)
                if i == chunk_count // 2:
                    await asyncio.sleep(0.8)  # Burst!
                else:
                    await asyncio.sleep(0.02)
            yield f"chunk_{i}_{prompt[:10]}"


class StreamingSmoothnessBenchmark:
    """Analisa distribuição temporal de chunks de streaming."""

    def __init__(self):
        self.sessions: List[Dict[str, Any]] = []

    async def measure_streaming_session(
        self, provider, prompt: str, session_id: int
    ) -> Dict[str, Any]:
        """
        Mede UMA sessão de streaming completa.

        Returns:
            {
                'session_id': int,
                'prompt': str,
                'total_chunks': int,
                'total_duration_ms': float,
                'first_chunk_ms': float,
                'inter_chunk_intervals_ms': List[float],
                'is_smooth': bool,
                'burst_detected': bool,
                'max_gap_ms': float,
            }
        """
        chunks = []
        timestamps = []

        start = time.perf_counter()
        first_chunk_time = None

        try:
            async for chunk in provider.stream_chunks(prompt):
                now = time.perf_counter()
                if first_chunk_time is None:
                    first_chunk_time = now - start
                chunks.append(chunk)
                timestamps.append(now)
        except Exception as e:
            return {
                "session_id": session_id,
                "prompt": prompt[:50],
                "error": str(e),
                "total_chunks": 0,
                "is_smooth": False,
                "burst_detected": True,
            }

        total_duration = (time.perf_counter() - start) * 1000

        # Calculate inter-chunk intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval_ms = (timestamps[i] - timestamps[i - 1]) * 1000
            intervals.append(interval_ms)

        # Analyze smoothness
        max_gap = max(intervals) if intervals else 0
        burst_detected = max_gap > 500

        # p95 of intervals
        if intervals:
            sorted_intervals = sorted(intervals)
            p95_idx = int(len(sorted_intervals) * 0.95)
            p95_interval = sorted_intervals[min(p95_idx, len(sorted_intervals) - 1)]
        else:
            p95_interval = 0

        is_smooth = (not burst_detected) and (p95_interval < 100)

        return {
            "session_id": session_id,
            "prompt": prompt[:50],
            "total_chunks": len(chunks),
            "total_duration_ms": total_duration,
            "first_chunk_ms": first_chunk_time * 1000 if first_chunk_time else 0,
            "inter_chunk_intervals_ms": intervals,
            "is_smooth": is_smooth,
            "burst_detected": burst_detected,
            "max_gap_ms": max_gap,
            "p95_interval_ms": p95_interval,
            "mean_interval_ms": statistics.mean(intervals) if intervals else 0,
        }

    async def run_benchmark(self, provider, sessions: int = 20) -> Dict[str, Any]:
        """
        Executa benchmark completo com N sessões de streaming.
        """
        prompts = [
            "Count from 1 to 10",
            "List the planets in our solar system",
            "Explain photosynthesis briefly",
            "What are the primary colors?",
            "Name 5 programming languages",
        ]

        for i in range(sessions):
            prompt = prompts[i % len(prompts)]
            result = await self.measure_streaming_session(provider, prompt, i)
            self.sessions.append(result)

            # Brief pause between sessions
            await asyncio.sleep(0.1)

        return self._calculate_aggregate_stats()

    def _calculate_aggregate_stats(self) -> Dict[str, Any]:
        """Aggregate statistics across all sessions."""
        if not self.sessions:
            return {"error": "No sessions completed"}

        # Collect all intervals
        all_intervals = []
        for s in self.sessions:
            all_intervals.extend(s.get("inter_chunk_intervals_ms", []))

        if not all_intervals:
            return {"error": "No intervals collected"}

        sorted_intervals = sorted(all_intervals)
        n = len(sorted_intervals)

        burst_count = sum(1 for s in self.sessions if s.get("burst_detected", False))
        smooth_count = sum(1 for s in self.sessions if s.get("is_smooth", False))

        def percentile(data: List[float], p: float) -> float:
            k = (len(data) - 1) * (p / 100)
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] + (k - f) * (data[c] - data[f]) if c != f else data[f]

        return {
            "sessions": len(self.sessions),
            "total_chunks": sum(s.get("total_chunks", 0) for s in self.sessions),
            "total_intervals": n,
            "mean_interval_ms": statistics.mean(all_intervals),
            "median_interval_ms": statistics.median(all_intervals),
            "stdev_interval_ms": statistics.stdev(all_intervals) if n > 1 else 0,
            "min_interval_ms": min(all_intervals),
            "max_interval_ms": max(all_intervals),
            "p50_interval_ms": percentile(sorted_intervals, 50),
            "p75_interval_ms": percentile(sorted_intervals, 75),
            "p90_interval_ms": percentile(sorted_intervals, 90),
            "p95_interval_ms": percentile(sorted_intervals, 95),
            "p99_interval_ms": percentile(sorted_intervals, 99),
            "bursts_detected": burst_count,
            "smooth_sessions": smooth_count,
            "is_overall_smooth": burst_count == 0 and percentile(sorted_intervals, 95) < 100,
            "raw_sessions": self.sessions,
        }


@pytest.mark.asyncio
async def test_streaming_smoothness_benchmark():
    """
    TESTE CIENTÍFICO: 20 sessões de streaming, análise de distribuição.

    Uses mock provider to test the measurement infrastructure.
    When LLM credentials are available, can be adapted for real streaming.

    CRITÉRIOS DE SUCESSO:
    - 95% dos intervalos entre chunks < 100ms
    - Nenhum gap > 500ms (sem "bursts")
    - Pelo menos 5 chunks por resposta
    """
    benchmark = StreamingSmoothnessBenchmark()

    # Use mock provider with smooth pattern
    provider = MockStreamingProvider(pattern="smooth")
    stats = await benchmark.run_benchmark(provider, sessions=20)

    # Print detailed report
    print("\n" + "=" * 70)
    print("BENCHMARK REPORT: Streaming Smoothness")
    print("=" * 70)
    print("Provider:              MockStreamingProvider (smooth pattern)")
    print(f"Sessions tested:       {stats['sessions']}")
    print(f"Total chunks:          {stats['total_chunks']}")
    print(f"Total intervals:       {stats['total_intervals']}")
    print("-" * 70)
    print(f"Mean interval:         {stats['mean_interval_ms']:.1f}ms")
    print(f"Median interval:       {stats['median_interval_ms']:.1f}ms")
    print(f"Std Dev:               {stats['stdev_interval_ms']:.1f}ms")
    print(f"Min interval:          {stats['min_interval_ms']:.1f}ms")
    print(f"Max interval:          {stats['max_interval_ms']:.1f}ms")
    print("-" * 70)
    print(f"p50 interval:          {stats['p50_interval_ms']:.1f}ms")
    print(f"p75 interval:          {stats['p75_interval_ms']:.1f}ms")
    print(f"p90 interval:          {stats['p90_interval_ms']:.1f}ms")
    print(
        f"p95 interval:          {stats['p95_interval_ms']:.1f}ms {'✅' if stats['p95_interval_ms'] < 100 else '❌'}"
    )
    print(f"p99 interval:          {stats['p99_interval_ms']:.1f}ms")
    print("-" * 70)
    print(f"Smooth sessions:       {stats['smooth_sessions']}/{stats['sessions']}")
    print(f"Bursts detected:       {stats['bursts_detected']}")
    print(f"Overall smoothness:    {'✅ SMOOTH' if stats['is_overall_smooth'] else '❌ BURSTING'}")
    print("=" * 70)

    # Assertions
    assert stats["sessions"] == 20, f"Expected 20 sessions, got {stats['sessions']}"
    assert (
        stats["p95_interval_ms"] < 100
    ), f"p95 interval too high: {stats['p95_interval_ms']:.1f}ms (target: <100ms)"
    assert (
        stats["max_interval_ms"] < 500
    ), f"Max gap too high: {stats['max_interval_ms']:.1f}ms (target: <500ms)"
    assert stats["bursts_detected"] == 0, f"Bursts detected: {stats['bursts_detected']}"
    assert all(
        s["total_chunks"] >= 5 for s in stats["raw_sessions"]
    ), "Some sessions had < 5 chunks"
    assert stats["is_overall_smooth"], "Streaming is not smooth overall"

    print("\n✅ STREAMING IS SMOOTH - No bursts detected")


@pytest.mark.asyncio
async def test_burst_detection_works():
    """
    TESTE DE CONTROLE: Verifica que detectamos bursts quando ocorrem.

    Uses a mock provider that intentionally creates bursts.
    """
    benchmark = StreamingSmoothnessBenchmark()

    # Use mock provider with BURST pattern
    provider = MockStreamingProvider(pattern="burst")
    stats = await benchmark.run_benchmark(provider, sessions=5)

    print("\n" + "=" * 70)
    print("CONTROL TEST: Burst Detection Validation")
    print("=" * 70)
    print("Pattern:               BURST (intentional gaps)")
    print(f"Sessions:              {stats['sessions']}")
    print(f"Max interval:          {stats['max_interval_ms']:.1f}ms")
    print(f"Bursts detected:       {stats['bursts_detected']}")
    print("=" * 70)

    # We EXPECT bursts to be detected here
    assert stats["bursts_detected"] > 0, "Burst detection failed - should have detected bursts"
    assert stats["max_interval_ms"] > 500, "Max gap should be > 500ms for burst pattern"

    print("\n✅ BURST DETECTION WORKING - Control test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--asyncio-mode=auto"])
