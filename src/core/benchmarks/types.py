"""
Benchmark Types

Type definitions for the benchmark suite.

Reference:
- SWE-bench (Jimenez et al., 2024)
- Terminal-Bench (2025)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class BenchmarkCategory(str, Enum):
    """Categories of benchmarks."""
    CODE_GENERATION = "code_generation"  # SWE-bench style
    TERMINAL = "terminal"                # CLI operations
    CONTEXT = "context"                  # RAG/context utilization
    MULTI_AGENT = "multi_agent"          # Coordination patterns
    E2E_WORKFLOW = "e2e_workflow"        # End-to-end tasks


class DifficultyLevel(str, Enum):
    """Benchmark difficulty levels."""
    TRIVIAL = "trivial"    # < 5 min for expert
    EASY = "easy"          # 5-15 min
    MEDIUM = "medium"      # 15-60 min
    HARD = "hard"          # 1-4 hours
    EXPERT = "expert"      # 4+ hours


class BenchmarkStatus(str, Enum):
    """Status of a benchmark run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    id: str
    name: str
    category: BenchmarkCategory
    difficulty: DifficultyLevel
    description: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    validation_fn: Optional[str] = None  # Name of validation function
    timeout_seconds: int = 300
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "description": self.description,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "timeout_seconds": self.timeout_seconds,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    task_id: str
    status: BenchmarkStatus
    actual_output: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    tokens_used: int = 0
    error_message: Optional[str] = None
    partial_score: float = 0.0  # 0.0 to 1.0
    validation_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "actual_output": self.actual_output,
            "execution_time_ms": self.execution_time_ms,
            "memory_used_mb": self.memory_used_mb,
            "tokens_used": self.tokens_used,
            "error_message": self.error_message,
            "partial_score": self.partial_score,
            "validation_details": self.validation_details,
            "timestamp": self.timestamp,
        }


@dataclass
class BenchmarkSuite:
    """A collection of related benchmark tasks."""
    id: str
    name: str
    description: str
    version: str
    tasks: List[BenchmarkTask] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: BenchmarkTask) -> None:
        """Add a task to the suite."""
        self.tasks.append(task)

    def get_tasks_by_category(self, category: BenchmarkCategory) -> List[BenchmarkTask]:
        """Get tasks filtered by category."""
        return [t for t in self.tasks if t.category == category]

    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[BenchmarkTask]:
        """Get tasks filtered by difficulty."""
        return [t for t in self.tasks if t.difficulty == difficulty]


@dataclass
class SuiteRunResult:
    """Result of running a complete benchmark suite."""
    suite_id: str
    run_id: str
    results: List[BenchmarkResult]
    start_time: str
    end_time: str
    total_tasks: int
    passed: int
    failed: int
    errors: int
    timeouts: int
    skipped: int
    avg_execution_time_ms: float
    total_tokens: int
    pass_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suite_id": self.suite_id,
            "run_id": self.run_id,
            "results": [r.to_dict() for r in self.results],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_tasks": self.total_tasks,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "timeouts": self.timeouts,
            "skipped": self.skipped,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "total_tokens": self.total_tokens,
            "pass_rate": self.pass_rate,
            "metadata": self.metadata,
        }
