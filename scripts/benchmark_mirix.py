#!/usr/bin/env python3
"""
MIRIX Benchmark CLI

Usage:
    python scripts/benchmark_mirix.py --queries 50 --workers 10
    python scripts/benchmark_mirix.py --compare  # Before/after comparison
"""

import argparse
import json
import asyncio
import sys
from pathlib import Path

# Add the parent directory of 'tests' to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from memory.cortex import MemoryCortex
from tests.benchmarks.utils import MIRIXBenchmark, SAMPLE_QUERIES


async def amain():
    parser = argparse.ArgumentParser(description="MIRIX Benchmark CLI")
    parser.add_argument("--queries", type=int, default=50, help="Number of queries to run.")
    parser.add_argument("--compare", action="store_true", help="Run sequential and concurrent comparison.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    args = parser.parse_args()

    cortex = MemoryCortex()
    benchmark = MIRIXBenchmark(args.queries)

    # Populate some test data first
    for i in range(100):
        cortex.remember(f"Test memory entry {i}", memory_type="episodic")

    queries = (SAMPLE_QUERIES * (args.queries // len(SAMPLE_QUERIES) + 1))[:args.queries]

    report = {}

    if args.compare:
        print("\n" + "="*70)
        print("MIRIX STRESS BENCHMARK REPORT")
        print("="*70)

        # Sequential baseline
        seq_stats = await benchmark.run_sequential(cortex, queries)
        report["sequential"] = seq_stats
        print("\n[SEQUENTIAL]")
        print(f"  p50: {seq_stats.get('p50_ms', 0):.2f}ms")
        print(f"  p95: {seq_stats.get('p95_ms', 0):.2f}ms")
        print(f"  p99: {seq_stats.get('p99_ms', 0):.2f}ms")

        # Concurrent
        conc_stats = await benchmark.run_concurrent(cortex, queries)
        report["concurrent"] = conc_stats
        print(f"\n[CONCURRENT - {args.queries} tasks]")
        print(f"  p50: {conc_stats.get('p50_ms', 0):.2f}ms")
        print(f"  p95: {conc_stats.get('p95_ms', 0):.2f}ms")
        print(f"  p99: {conc_stats.get('p99_ms', 0):.2f}ms")

        # Improvement calculation
        if seq_stats.get('p99_ms', 0) > 0 and conc_stats.get('p99_ms') is not None:
            improvement = ((seq_stats['p99_ms'] - conc_stats['p99_ms']) / seq_stats['p99_ms']) * 100
            report["improvement_p99_percent"] = improvement
            print("\n[IMPROVEMENT]")
            print(f"  p99 improved by: {improvement:.1f}%")

        print("\n" + "="*70)
    else:
        stats = await benchmark.run_concurrent(cortex, queries)
        report["concurrent"] = stats
        print(f"\n{'='*60}")
        print(f"CONCURRENT ({args.queries} queries)")
        print(f"{'='*60}")
        for k, v in stats.items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

    if args.json:
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(amain())
