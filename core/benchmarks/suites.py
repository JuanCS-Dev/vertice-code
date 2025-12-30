"""
Built-in Benchmark Suites

Pre-configured benchmark suites for common scenarios.

Reference:
- SWE-bench (Jimenez et al., 2024)
- Terminal-Bench (2025)
"""

from __future__ import annotations

from .types import (
    BenchmarkTask,
    BenchmarkSuite,
    BenchmarkCategory,
    DifficultyLevel,
)


def create_swe_bench_mini() -> BenchmarkSuite:
    """Create a mini SWE-bench style suite for testing."""
    suite = BenchmarkSuite(
        id="swe-bench-mini",
        name="SWE-bench Mini",
        description="Minimal SWE-bench style code generation tasks",
        version="1.0.0",
    )

    # Bug fix task
    suite.add_task(BenchmarkTask(
        id="swe-001",
        name="Fix off-by-one error",
        category=BenchmarkCategory.CODE_GENERATION,
        difficulty=DifficultyLevel.EASY,
        description="Fix the off-by-one error in the loop boundary",
        input_data={
            "code": "for i in range(len(items)):\n    print(items[i+1])",
            "error": "IndexError: list index out of range",
        },
        expected_output={
            "fixed_code": "for i in range(len(items) - 1):\n    print(items[i+1])",
        },
        validation_fn="contains",
        tags=["bug-fix", "python"],
    ))

    # Function implementation task
    suite.add_task(BenchmarkTask(
        id="swe-002",
        name="Implement binary search",
        category=BenchmarkCategory.CODE_GENERATION,
        difficulty=DifficultyLevel.MEDIUM,
        description="Implement binary search that returns the index or -1",
        input_data={
            "signature": "def binary_search(arr: list, target: int) -> int:",
            "test_cases": [
                {"input": [[1, 2, 3, 4, 5], 3], "expected": 2},
                {"input": [[1, 2, 3, 4, 5], 6], "expected": -1},
            ],
        },
        validation_fn="test_pass",
        tags=["implementation", "algorithm"],
    ))

    # Refactoring task
    suite.add_task(BenchmarkTask(
        id="swe-003",
        name="Extract method refactoring",
        category=BenchmarkCategory.CODE_GENERATION,
        difficulty=DifficultyLevel.MEDIUM,
        description="Extract the validation logic into a separate method",
        input_data={
            "code": """
def process_user(data):
    if not data.get('name'):
        raise ValueError('Name required')
    if not data.get('email'):
        raise ValueError('Email required')
    if '@' not in data.get('email', ''):
        raise ValueError('Invalid email')
    # Process user...
    return True
""",
        },
        validation_fn="contains",
        tags=["refactoring", "python"],
    ))

    return suite


def create_terminal_bench_mini() -> BenchmarkSuite:
    """Create a mini Terminal-bench style suite."""
    suite = BenchmarkSuite(
        id="terminal-bench-mini",
        name="Terminal-Bench Mini",
        description="Terminal and CLI operation benchmarks",
        version="1.0.0",
    )

    suite.add_task(BenchmarkTask(
        id="term-001",
        name="Find files by pattern",
        category=BenchmarkCategory.TERMINAL,
        difficulty=DifficultyLevel.EASY,
        description="Find all Python files in a directory tree",
        input_data={
            "command_description": "Find all .py files recursively",
            "working_dir": "/project",
        },
        expected_output={
            "command": "find /project -name '*.py' -type f",
        },
        tags=["find", "glob"],
    ))

    suite.add_task(BenchmarkTask(
        id="term-002",
        name="Git complex operation",
        category=BenchmarkCategory.TERMINAL,
        difficulty=DifficultyLevel.MEDIUM,
        description="Rebase interactively onto main, squashing commits",
        input_data={
            "scenario": "Squash last 3 commits and rebase onto main",
            "current_branch": "feature-x",
        },
        expected_output={
            "commands": [
                "git rebase -i HEAD~3",
                "git rebase main",
            ],
        },
        tags=["git", "rebase"],
    ))

    return suite


def create_context_bench_mini() -> BenchmarkSuite:
    """Create a mini Context-bench style suite."""
    suite = BenchmarkSuite(
        id="context-bench-mini",
        name="Context-Bench Mini",
        description="Context utilization and RAG benchmarks",
        version="1.0.0",
    )

    suite.add_task(BenchmarkTask(
        id="ctx-001",
        name="Multi-file context",
        category=BenchmarkCategory.CONTEXT,
        difficulty=DifficultyLevel.MEDIUM,
        description="Answer question requiring information from multiple files",
        input_data={
            "question": "What authentication method does the API use?",
            "context_files": [
                {"path": "auth.py", "content": "from jwt import encode, decode"},
                {"path": "config.py", "content": "AUTH_METHOD = 'JWT'"},
                {"path": "routes.py", "content": "@require_auth\ndef protected():"},
            ],
        },
        expected_output={
            "answer_contains": ["JWT", "authentication"],
        },
        validation_fn="contains",
        tags=["rag", "multi-file"],
    ))

    return suite


def create_agent_bench_mini() -> BenchmarkSuite:
    """Create a mini Agent coordination benchmark suite."""
    suite = BenchmarkSuite(
        id="agent-bench-mini",
        name="Agent-Bench Mini",
        description="Multi-agent coordination benchmarks",
        version="1.0.0",
    )

    suite.add_task(BenchmarkTask(
        id="agent-001",
        name="Task decomposition",
        category=BenchmarkCategory.MULTI_AGENT,
        difficulty=DifficultyLevel.MEDIUM,
        description="Decompose a complex task into subtasks for multiple agents",
        input_data={
            "task": "Build a REST API with authentication, database, and tests",
            "available_agents": ["architect", "coder", "tester", "reviewer"],
        },
        expected_output={
            "subtasks_count_min": 3,
            "uses_agents": ["architect", "coder", "tester"],
        },
        validation_fn="contains",
        tags=["decomposition", "coordination"],
    ))

    suite.add_task(BenchmarkTask(
        id="agent-002",
        name="Conflict resolution",
        category=BenchmarkCategory.MULTI_AGENT,
        difficulty=DifficultyLevel.HARD,
        description="Resolve conflicting recommendations from two agents",
        input_data={
            "agent_a_recommendation": "Use PostgreSQL for its ACID compliance",
            "agent_b_recommendation": "Use MongoDB for schema flexibility",
            "requirements": ["scalability", "transactions", "rapid iteration"],
        },
        validation_fn="contains",
        tags=["conflict", "decision"],
    ))

    return suite
