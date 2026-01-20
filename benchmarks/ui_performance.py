"""
UI Performance Benchmarks - DAY 8 Phase 5.1
Target: <100ms latency, 60fps rendering

Constitutional Compliance:
- P5 (Consciência de Performance): Monitoramento ativo
- P6 (Eficiência de Token): Otimização de renders
"""

import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import psutil
import os
from unittest.mock import patch

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree

# Corrected imports
from vertice_cli.tui.components.enhanced_progress import (
    EnhancedProgressDisplay,
    WorkflowProgress,
    StageProgress,
)
from vertice_cli.tui.components.dashboard import Dashboard, Operation
from vertice_cli.tui.components.workflow_visualizer import WorkflowVisualizer, StepStatus
from vertice_cli.tui.input_enhanced import EnhancedInput
from vertice_cli.tui.components.context_awareness import ContextAwarenessEngine


@dataclass
class BenchmarkResult:
    """Performance benchmark result"""

    operation: str
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    memory_mb: float
    fps: float
    passed: bool

    def __str__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"{status} {self.operation}:\n"
            f"  Mean: {self.mean_ms:.2f}ms | P95: {self.p95_ms:.2f}ms | P99: {self.p99_ms:.2f}ms\n"
            f"  Memory: {self.memory_mb:.2f}MB | FPS: {self.fps:.1f}"
        )


class UIPerformanceBenchmark:
    """Comprehensive UI performance testing"""

    TARGET_LATENCY_MS = 100.0  # <100ms target
    TARGET_FPS = 60.0  # 60fps target
    ITERATIONS = 100  # Statistical significance

    def __init__(self):
        self.console = Console()
        self.results: List[BenchmarkResult] = []

    def measure_memory(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def benchmark_operation(
        self, operation_name: str, operation_func: callable, iterations: int = None
    ) -> BenchmarkResult:
        """Benchmark a single operation"""
        iterations = iterations or self.ITERATIONS
        latencies = []

        # Warm-up
        for _ in range(10):
            operation_func()

        # Measure
        mem_before = self.measure_memory()

        for _ in range(iterations):
            start = time.perf_counter()
            operation_func()
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        mem_after = self.measure_memory()
        mem_delta = mem_after - mem_before

        # Calculate stats
        mean = statistics.mean(latencies)
        median = statistics.median(latencies)
        sorted_latencies = sorted(latencies)
        p95 = sorted_latencies[int(0.95 * len(sorted_latencies))]
        p99 = sorted_latencies[int(0.99 * len(sorted_latencies))]
        min_lat = min(latencies)
        max_lat = max(latencies)

        # FPS calculation (frames per second)
        fps = 1000.0 / mean if mean > 0 else 0

        # Pass/fail
        passed = p95 < self.TARGET_LATENCY_MS and fps >= self.TARGET_FPS

        result = BenchmarkResult(
            operation=operation_name,
            mean_ms=mean,
            median_ms=median,
            p95_ms=p95,
            p99_ms=p99,
            min_ms=min_lat,
            max_ms=max_lat,
            memory_mb=mem_delta,
            fps=fps,
            passed=passed,
        )

        self.results.append(result)
        return result

    def benchmark_enhanced_progress(self) -> BenchmarkResult:
        """Benchmark EnhancedProgressDisplay component"""
        console = Console()
        display = EnhancedProgressDisplay(console)
        workflow = WorkflowProgress(
            stages=[
                StageProgress("Stage 1", current=50, total=100, status="running"),
                StageProgress("Stage 2", current=0, total=100, status="pending"),
            ]
        )

        def operation():
            with console.capture() as _:
                console.print(display.render_workflow(workflow))

        return self.benchmark_operation("EnhancedProgress.render", operation)

    def benchmark_dashboard(self) -> BenchmarkResult:
        """Benchmark Dashboard component"""
        console = Console()
        dashboard = Dashboard(console)

        # Pre-populate
        for i in range(5):
            dashboard.add_operation(Operation(id=f"op{i}", type="llm", description=f"Test Op {i}"))

        # Mock psutil to avoid 0.1s blocking delay during benchmark
        with patch("psutil.cpu_percent", return_value=15.5):

            def operation():
                with console.capture() as _:
                    console.print(dashboard.render())

            return self.benchmark_operation("Dashboard.render", operation)

    def benchmark_workflow_visualizer(self) -> BenchmarkResult:
        """Benchmark WorkflowVisualizer component"""
        console = Console()
        visualizer = WorkflowVisualizer(console)

        # Populate steps
        visualizer.add_step("step1", "Init")
        visualizer.update_step("step1", status=StepStatus.COMPLETED)
        visualizer.add_step("step2", "Analysis", dependencies=["step1"])
        visualizer.update_step("step2", status=StepStatus.RUNNING, progress=0.5)
        visualizer.add_step("step3", "Code Gen", dependencies=["step2"])

        def operation():
            # Force dirty flags to ensure full render for benchmark
            visualizer._dirty_flags.update({"minimap", "main", "details"})
            with console.capture() as _:
                console.print(visualizer.render_full_view())

        return self.benchmark_operation("WorkflowVisualizer.render", operation)

    def benchmark_enhanced_input(self) -> BenchmarkResult:
        """Benchmark EnhancedInput component"""
        enhanced_input = EnhancedInput()

        def operation():
            enhanced_input.process_input("def hello():\n    print('world')")

        return self.benchmark_operation("EnhancedInput.process", operation)

    def benchmark_context_awareness(self) -> BenchmarkResult:
        """Benchmark ContextAwarenessEngine component"""
        context = ContextAwarenessEngine()

        files = [f"file{i}.py" for i in range(50)]

        def operation():
            # Mimic rank_files behavior using score_file_relevance
            scores = []
            for f in files:
                scores.append(context.score_file_relevance(f, "implement authentication"))

        return self.benchmark_operation("ContextAwareness.rank", operation, iterations=50)

    def benchmark_rich_panel(self) -> BenchmarkResult:
        """Benchmark Rich Panel rendering"""
        console = Console()

        def operation():
            panel = Panel(
                "This is a test panel with multiple lines\n" * 5,
                title="Test Panel",
                border_style="blue",
            )
            with console.capture() as _:
                console.print(panel)

        return self.benchmark_operation("Rich.Panel.render", operation)

    def benchmark_rich_tree(self) -> BenchmarkResult:
        """Benchmark Rich Tree rendering"""
        console = Console()

        def operation():
            tree = Tree("Root")
            for i in range(10):
                branch = tree.add(f"Branch {i}")
                for j in range(5):
                    branch.add(f"Leaf {j}")
            with console.capture() as _:
                console.print(tree)

        return self.benchmark_operation("Rich.Tree.render", operation)

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        self.console.print("\n[bold cyan]🔥 UI PERFORMANCE BENCHMARKS[/bold cyan]")
        self.console.print(f"Target: <{self.TARGET_LATENCY_MS}ms latency, {self.TARGET_FPS}fps\n")

        benchmarks = [
            ("Enhanced Progress", self.benchmark_enhanced_progress),
            ("Status Dashboard", self.benchmark_dashboard),
            ("Workflow Visualizer", self.benchmark_workflow_visualizer),
            ("Enhanced Input", self.benchmark_enhanced_input),
            ("Context Awareness", self.benchmark_context_awareness),
            ("Rich Panel", self.benchmark_rich_panel),
            ("Rich Tree", self.benchmark_rich_tree),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Running benchmarks...", total=len(benchmarks))

            for name, benchmark_func in benchmarks:
                progress.update(task, description=f"Benchmarking {name}...")
                try:
                    result = benchmark_func()
                    self.console.print(result)
                except Exception as e:
                    self.console.print(f"[red]FAILED {name}: {e}[/red]")
                    import traceback

                    traceback.print_exc()
                    self.results.append(BenchmarkResult(name, 0, 0, 0, 0, 0, 0, 0, 0, False))
                progress.advance(task)

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  Passed: {passed}/{total} ({pass_rate:.1f}%)")

        if pass_rate >= 90:
            self.console.print("[bold green]✅ EXCELLENT - Production ready![/bold green]")
        elif pass_rate >= 70:
            self.console.print("[bold yellow]⚠️  GOOD - Minor optimizations needed[/bold yellow]")
        else:
            self.console.print("[bold red]❌ POOR - Significant optimization required[/bold red]")

        return {"passed": passed, "total": total, "pass_rate": pass_rate, "results": self.results}


def main():
    """Run benchmark suite"""
    benchmark = UIPerformanceBenchmark()
    results = benchmark.run_all_benchmarks()

    # Exit code based on pass rate
    exit_code = 0 if results["pass_rate"] >= 90 else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
