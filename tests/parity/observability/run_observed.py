#!/usr/bin/env python3
"""
OBSERVED PIPELINE RUNNER

Run this directly to test the pipeline with full observability.

Usage:
    python tests/parity/observability/run_observed.py "Your prompt here"
    python tests/parity/observability/run_observed.py --interactive
    python tests/parity/observability/run_observed.py --suite basic

This is your EAGLE EYE into the Vertice pipeline.
"""

import asyncio
import argparse
import sys
import os
import time
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.parity.observability.pipeline_observer import (
    PipelineObserver,
    PipelineStage,
    get_observer,
    reset_observer,
)
from tests.parity.observability.vertice_hooks import (
    VerticeHookedClient,
    LivePipelineMonitor,
)


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))


# Test suites
TEST_SUITES = {
    "basic": [
        "What is 2 + 2?",
        "Write a hello world in Python",
        "Explain what a variable is",
    ],
    "coding": [
        "Write a function to check if a number is prime",
        "Create a class for a stack data structure",
        "Implement binary search in Python",
    ],
    "planning": [
        "Plan a REST API for user management",
        "Design a database schema for an e-commerce site",
        "Create an architecture for a chat application",
    ],
    "decomposition": [
        "Create a todo app with add, delete, list, and mark-complete features",
        "Build a user authentication system with registration, login, password reset, and sessions",
        "Implement a file manager with upload, download, rename, and delete functionality",
    ],
    "tools": [
        "Read the pyproject.toml file and tell me the project name",
        "Find where the TUIBridge class is defined",
        "List the files in the vertice_tui directory",
    ],
}


class ObservedRunner:
    """Runner for observed pipeline tests."""

    def __init__(self):
        self.observer = get_observer()
        self.client = None
        self.monitor = None
        self.results: List[Dict] = []

    async def initialize(self) -> bool:
        """Initialize the runner."""
        load_env()

        self.client = VerticeHookedClient(self.observer)
        success = await self.client.initialize()

        if success:
            self.monitor = LivePipelineMonitor(self.observer)

        return success

    async def run_single(self, prompt: str, verbose: bool = True) -> Dict:
        """Run a single observed test."""
        reset_observer()
        self.observer = get_observer()
        self.client.observer = self.observer
        self.monitor = LivePipelineMonitor(self.observer)

        print("\n" + "=" * 70)
        print("OBSERVED PIPELINE EXECUTION")
        print("=" * 70)
        print(f"Prompt: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
        print("-" * 70)
        print("STAGE EXECUTION:")

        result = await self.client.process_with_observation(prompt, verbose=verbose)

        self.results.append(result)

        return result

    async def run_suite(self, suite_name: str) -> List[Dict]:
        """Run a test suite."""
        if suite_name not in TEST_SUITES:
            print(f"Unknown suite: {suite_name}")
            print(f"Available: {', '.join(TEST_SUITES.keys())}")
            return []

        prompts = TEST_SUITES[suite_name]

        print("\n" + "=" * 70)
        print(f"RUNNING TEST SUITE: {suite_name}")
        print(f"Tests: {len(prompts)}")
        print("=" * 70)

        results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"\n[Test {i}/{len(prompts)}]")
            result = await self.run_single(prompt, verbose=False)
            results.append(result)

            # Brief summary
            success = "✓" if result.get("success") else "✗"
            duration = result.get("trace").get_total_duration() if result.get("trace") else 0
            print(f"\n{success} Completed in {duration:.0f}ms")

        # Suite summary
        self._print_suite_summary(suite_name, results)

        return results

    def _print_suite_summary(self, suite_name: str, results: List[Dict]):
        """Print summary of suite results."""
        print("\n" + "=" * 70)
        print(f"SUITE SUMMARY: {suite_name}")
        print("=" * 70)

        successful = sum(1 for r in results if r.get("success"))
        total = len(results)

        print(f"\nResults: {successful}/{total} passed ({successful/total*100:.0f}%)")

        # Failure analysis
        failures_by_stage = {}
        for result in results:
            trace = result.get("trace")
            if trace and trace.failure_point:
                stage = trace.failure_point.value
                if stage not in failures_by_stage:
                    failures_by_stage[stage] = 0
                failures_by_stage[stage] += 1

        if failures_by_stage:
            print("\nFailures by stage:")
            for stage, count in sorted(failures_by_stage.items(), key=lambda x: -x[1]):
                print(f"  {stage}: {count}")

        # Timing analysis
        all_times = []
        stage_times = {}

        for result in results:
            trace = result.get("trace")
            if trace:
                all_times.append(trace.get_total_duration())
                for obs in trace.observations:
                    if obs.stage.value not in stage_times:
                        stage_times[obs.stage.value] = []
                    stage_times[obs.stage.value].append(obs.duration_ms)

        if all_times:
            print(f"\nTiming:")
            print(f"  Average: {sum(all_times)/len(all_times):.0f}ms")
            print(f"  Min: {min(all_times):.0f}ms")
            print(f"  Max: {max(all_times):.0f}ms")

        # Bottleneck analysis
        if stage_times:
            avg_by_stage = {
                stage: sum(times)/len(times)
                for stage, times in stage_times.items()
            }
            slowest = max(avg_by_stage, key=avg_by_stage.get)
            print(f"\nBottleneck: {slowest} (avg {avg_by_stage[slowest]:.0f}ms)")

    async def run_interactive(self):
        """Run in interactive mode."""
        print("\n" + "=" * 70)
        print("INTERACTIVE OBSERVED PIPELINE")
        print("=" * 70)
        print("Type your prompts to test. Commands:")
        print("  /quit - Exit")
        print("  /report - Show last diagnostic report")
        print("  /analysis - Show failure analysis")
        print("  /suite <name> - Run a test suite")
        print("-" * 70)

        while True:
            try:
                prompt = input("\n> ").strip()

                if not prompt:
                    continue

                if prompt == "/quit":
                    break

                if prompt == "/report":
                    if self.results:
                        print(self.results[-1].get("diagnostic_report", "No report"))
                    else:
                        print("No results yet")
                    continue

                if prompt == "/analysis":
                    analysis = self.observer.get_failure_analysis()
                    print(f"\nTotal traces: {analysis['total_traces']}")
                    print(f"Success rate: {analysis['success_rate']:.1%}")
                    if analysis['failures_by_stage']:
                        print("Failures by stage:")
                        for stage, data in analysis['failures_by_stage'].items():
                            print(f"  {stage}: {data['count']}")
                    continue

                if prompt.startswith("/suite "):
                    suite_name = prompt.split(" ", 1)[1]
                    await self.run_suite(suite_name)
                    continue

                # Run observed test
                result = await self.run_single(prompt)

                # Show brief diagnostic
                trace = result.get("trace")
                if trace:
                    if trace.failure_point:
                        print(f"\n⚠ Failed at: {trace.failure_point.value}")
                        print(f"  Reason: {trace.failure_reason}")

            except KeyboardInterrupt:
                print("\nInterrupted")
                break
            except EOFError:
                break

    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Vertice pipeline with full observability"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt to test",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--suite", "-s",
        help="Run a test suite",
        choices=list(TEST_SUITES.keys()),
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress streaming output",
    )
    parser.add_argument(
        "--export",
        help="Export trace to JSON file",
    )

    args = parser.parse_args()

    # Initialize runner
    runner = ObservedRunner()

    if not await runner.initialize():
        print("Failed to initialize Vertice")
        print("Make sure you have valid API keys in .env")
        return 1

    try:
        if args.interactive:
            await runner.run_interactive()

        elif args.suite:
            await runner.run_suite(args.suite)

        elif args.prompt:
            result = await runner.run_single(args.prompt, verbose=not args.quiet)

            # Print report
            print("\n" + result.get("diagnostic_report", ""))

            # Export if requested
            if args.export and result.get("trace"):
                result["trace"].export_trace(args.export)
                print(f"\nTrace exported to: {args.export}")

        else:
            # Default: run basic suite
            await runner.run_suite("basic")

    finally:
        await runner.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
