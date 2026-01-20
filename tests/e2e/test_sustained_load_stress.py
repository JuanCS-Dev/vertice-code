"""
E2E Stress Test: Sustained Load
================================

Tests TUI stability under sustained load:
- 100 consecutive operations
- Memory tracking (detect leaks)
- Performance degradation detection
- Resource monitoring

Target Metrics:
- No performance degradation > 50%
- No memory growth > 100MB
- Zero crashes

Created: 2026-01-18
"""

import asyncio
import gc
import os
import statistics
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import pytest


class SustainedLoadStressTest:
    """
    Teste de carga sustentada para detectar degradação.

    Simulates heavy usage by running 100 consecutive operations
    and monitoring for performance degradation and memory leaks.
    """

    def __init__(self):
        self.latencies: List[float] = []
        self.memory_samples: List[float] = []
        self.initial_memory_mb: float = 0
        self.errors: List[str] = []

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback to tracemalloc
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024

    async def run_stress_test(self, iterations: int = 100, history_manager=None) -> Dict[str, Any]:
        """
        Executa N operações consecutivas e monitora recursos.

        Tests the critical path: add_command_async which was the
        source of the blocking behavior.
        """
        from vertice_tui.core.history_manager import HistoryManager

        # Start memory tracking
        tracemalloc.start()
        gc.collect()  # Clean slate

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "stress_test_history"
            hm = history_manager or HistoryManager(history_file=history_file)

            self.initial_memory_mb = self._get_memory_mb()
            self.memory_samples.append(self.initial_memory_mb)

            for i in range(iterations):
                try:
                    # Measure operation latency
                    start = time.perf_counter()

                    if hasattr(hm, "add_command_async"):
                        await hm.add_command_async(f"stress_test_command_{i}_{'x' * (i % 100)}")
                    else:
                        hm.add_command(f"stress_test_command_{i}")

                    latency_ms = (time.perf_counter() - start) * 1000
                    self.latencies.append(latency_ms)

                    # Sample memory every 10 iterations
                    if i % 10 == 0:
                        self.memory_samples.append(self._get_memory_mb())

                except Exception as e:
                    self.errors.append(f"Iteration {i}: {str(e)}")

                # Very brief yield to event loop
                if i % 20 == 0:
                    await asyncio.sleep(0.001)

            # Final memory sample
            gc.collect()
            final_memory = self._get_memory_mb()
            self.memory_samples.append(final_memory)

        tracemalloc.stop()

        return self._analyze_results()

    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze stress test results for degradation and leaks."""
        if not self.latencies:
            return {"error": "No measurements collected"}

        n = len(self.latencies)

        # Divide latencies into quartiles
        q_size = n // 4
        q1_latencies = self.latencies[:q_size]
        q4_latencies = self.latencies[-q_size:]

        q1_mean = statistics.mean(q1_latencies)
        q4_mean = statistics.mean(q4_latencies)

        # Calculate degradation percentage
        latency_degradation = ((q4_mean - q1_mean) / q1_mean) * 100 if q1_mean > 0 else 0

        # Memory analysis
        initial_mem = self.memory_samples[0]
        final_mem = self.memory_samples[-1]
        memory_growth_mb = final_mem - initial_mem
        memory_growth_pct = (memory_growth_mb / initial_mem) * 100 if initial_mem > 0 else 0

        # Thresholds
        has_degradation = latency_degradation > 50
        has_memory_leak = memory_growth_mb > 100

        return {
            "iterations": n,
            "errors": len(self.errors),
            "error_rate": len(self.errors) / n if n > 0 else 0,
            # Latency stats
            "mean_latency_ms": statistics.mean(self.latencies),
            "median_latency_ms": statistics.median(self.latencies),
            "stdev_latency_ms": statistics.stdev(self.latencies) if n > 1 else 0,
            "min_latency_ms": min(self.latencies),
            "max_latency_ms": max(self.latencies),
            "q1_mean_latency_ms": q1_mean,
            "q4_mean_latency_ms": q4_mean,
            "latency_degradation_pct": latency_degradation,
            # Memory stats
            "initial_memory_mb": initial_mem,
            "final_memory_mb": final_mem,
            "memory_growth_mb": memory_growth_mb,
            "memory_growth_pct": memory_growth_pct,
            "memory_samples": len(self.memory_samples),
            # Verdicts
            "has_performance_degradation": has_degradation,
            "has_memory_leak": has_memory_leak,
            "is_stable": not has_degradation and not has_memory_leak and len(self.errors) == 0,
            # Raw data for analysis
            "raw_errors": self.errors,
        }


@pytest.mark.asyncio
async def test_no_degradation_under_sustained_load():
    """
    TESTE DE ESTRESSE: 100 prompts consecutivos.

    CRITÉRIOS DE SUCESSO:
    - Latência Q4 não degrada > 50% vs Q1
    - Memória não cresce > 100MB
    - Zero erros
    - Zero crashes
    """
    stress_test = SustainedLoadStressTest()
    results = await stress_test.run_stress_test(iterations=100)

    # Print detailed report
    print("\n" + "=" * 70)
    print("STRESS TEST REPORT: 100 Consecutive Operations")
    print("=" * 70)
    print(f"Iterations:            {results['iterations']}")
    print(f"Errors:                {results['errors']}")
    print(f"Error rate:            {results['error_rate'] * 100:.2f}%")
    print("-" * 70)
    print("LATENCY ANALYSIS:")
    print(f"  Mean:                {results['mean_latency_ms']:.3f}ms")
    print(f"  Median:              {results['median_latency_ms']:.3f}ms")
    print(f"  Std Dev:             {results['stdev_latency_ms']:.3f}ms")
    print(f"  Min:                 {results['min_latency_ms']:.3f}ms")
    print(f"  Max:                 {results['max_latency_ms']:.3f}ms")
    print(f"  Q1 mean (first 25):  {results['q1_mean_latency_ms']:.3f}ms")
    print(f"  Q4 mean (last 25):   {results['q4_mean_latency_ms']:.3f}ms")
    print(
        f"  Degradation:         {results['latency_degradation_pct']:+.1f}% {'✅' if not results['has_performance_degradation'] else '❌'}"
    )
    print("-" * 70)
    print("MEMORY ANALYSIS:")
    print(f"  Initial:             {results['initial_memory_mb']:.1f}MB")
    print(f"  Final:               {results['final_memory_mb']:.1f}MB")
    print(
        f"  Growth:              {results['memory_growth_mb']:+.1f}MB ({results['memory_growth_pct']:+.1f}%)"
    )
    print(f"  Memory leak:         {'❌ YES' if results['has_memory_leak'] else '✅ NO'}")
    print("-" * 70)
    print(f"STABILITY:             {'✅ STABLE' if results['is_stable'] else '❌ UNSTABLE'}")
    print("=" * 70)

    # Assertions
    assert results["errors"] == 0, f"Errors occurred: {results['raw_errors']}"
    assert not results[
        "has_performance_degradation"
    ], f"Performance degraded {results['latency_degradation_pct']:.1f}% (Q1={results['q1_mean_latency_ms']:.2f}ms → Q4={results['q4_mean_latency_ms']:.2f}ms)"
    assert not results[
        "has_memory_leak"
    ], f"Memory leak detected: +{results['memory_growth_mb']:.1f}MB"
    assert results["is_stable"], "System is not stable under load"

    print("\n✅ STABLE UNDER SUSTAINED LOAD - No degradation or leaks")


@pytest.mark.asyncio
async def test_rapid_fire_commands():
    """
    TESTE DE RAJADA: 50 comandos em rápida sucessão (sem delay).

    Tests concurrent handling when commands arrive faster than disk can write.
    The async lock should serialize writes correctly.
    """
    from vertice_tui.core.history_manager import HistoryManager

    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "rapid_fire_test"
        hm = HistoryManager(history_file=history_file)

        start = time.perf_counter()

        # Fire 50 commands as fast as possible
        tasks = [hm.add_command_async(f"rapid_{i}") for i in range(50)]

        await asyncio.gather(*tasks)

        elapsed_ms = (time.perf_counter() - start) * 1000

        if hasattr(hm, "flush_history_async"):
            await hm.flush_history_async()

        # Verify all were saved
        content = history_file.read_text()
        lines = [line for line in content.split("\n") if line.strip()]

        print("\n" + "=" * 70)
        print("RAPID FIRE TEST: 50 Concurrent Commands")
        print("=" * 70)
        print(f"Total time:            {elapsed_ms:.1f}ms")
        print("Commands sent:         50")
        print(f"Commands saved:        {len(lines)}")
        print(f"Integrity:             {'✅ OK' if len(lines) == 50 else '❌ LOST COMMANDS'}")
        print("=" * 70)

        assert len(lines) == 50, f"Lost commands: expected 50, got {len(lines)}"

        print("\n✅ RAPID FIRE HANDLED - No lost commands")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--asyncio-mode=auto"])
