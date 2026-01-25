"""
Vertice Benchmarks - Comprehensive Evaluation Suite

Phase 3 Integration:
- SWE-bench style code generation
- Terminal-Bench CLI operations
- Context-Bench RAG evaluation
- Multi-agent coordination benchmarks

Reference:
- SWE-bench (Jimenez et al., 2024)
- Terminal-Bench (2025)
- arXiv:2512.08296 (Scaling Agent Systems)
"""

from .types import (
    BenchmarkCategory,
    DifficultyLevel,
    BenchmarkStatus,
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkSuite,
    SuiteRunResult,
)
from .validators import (
    BenchmarkValidator,
    ExactMatchValidator,
    ContainsValidator,
    TestPassValidator,
)
from .runner import BenchmarkRunner
from .suites import (
    create_swe_bench_mini,
    create_terminal_bench_mini,
    create_context_bench_mini,
    create_agent_bench_mini,
)
from .mixin import BenchmarkMixin

__all__ = [
    # Types
    "BenchmarkCategory",
    "DifficultyLevel",
    "BenchmarkStatus",
    "BenchmarkTask",
    "BenchmarkResult",
    "BenchmarkSuite",
    "SuiteRunResult",
    # Validators
    "BenchmarkValidator",
    "ExactMatchValidator",
    "ContainsValidator",
    "TestPassValidator",
    # Runner
    "BenchmarkRunner",
    # Suites
    "create_swe_bench_mini",
    "create_terminal_bench_mini",
    "create_context_bench_mini",
    "create_agent_bench_mini",
    # Mixin
    "BenchmarkMixin",
]
