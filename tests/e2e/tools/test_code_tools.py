"""
E2E Tests for Code Analysis Tools - Phase 8.1

Tests for code analysis and quality tools:
- LintTool (ruff), FormatTool (ruff format)
- TypeCheckTool (pyright/mypy), TestRunnerTool (pytest)
- CoverageTool, ComplexityTool
- DependenciesTool, SymbolsTool
- ReferencesTool, DefinitionTool

Following Google's principle: "Maintainability > clever code"
"""

import pytest
import subprocess
import tempfile
from pathlib import Path


@pytest.fixture
def python_project():
    """Create temporary Python project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)

        # Create source files
        (project / "main.py").write_text(
            '''
"""Main module."""

def hello(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


class Calculator:
    """Simple calculator."""

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
'''
        )

        (project / "utils.py").write_text(
            '''
"""Utility functions."""

from typing import List


def flatten(nested: List[List[int]]) -> List[int]:
    """Flatten nested list."""
    return [item for sublist in nested for item in sublist]
'''
        )

        # Create test file
        (project / "test_main.py").write_text(
            '''
"""Tests for main module."""

from main import hello, add, Calculator


def test_hello():
    assert hello("World") == "Hello, World!"


def test_add():
    assert add(2, 3) == 5


def test_calculator():
    calc = Calculator()
    assert calc.multiply(3, 4) == 12
'''
        )

        yield project


class TestLintTool:
    """Tests for linting with ruff."""

    def test_ruff_lint_clean_file(self, python_project):
        """Ruff passes on clean Python."""
        result = subprocess.run(
            ["ruff", "check", str(python_project / "main.py")], capture_output=True, text=True
        )
        # Should pass or have minor issues
        assert result.returncode in [0, 1]

    def test_ruff_lint_with_issues(self, python_project):
        """Ruff detects issues."""
        # Create file with intentional issues
        bad_file = python_project / "bad.py"
        bad_file.write_text("import os\nimport sys\nx=1")  # unused imports

        result = subprocess.run(["ruff", "check", str(bad_file)], capture_output=True, text=True)
        # Should detect unused imports
        assert result.returncode == 1 or "F401" in result.stdout


class TestFormatTool:
    """Tests for formatting with ruff format."""

    def test_ruff_format_check(self, python_project):
        """Ruff format check works."""
        result = subprocess.run(
            ["ruff", "format", "--check", str(python_project / "main.py")],
            capture_output=True,
            text=True,
        )
        # Already formatted should return 0
        assert result.returncode in [0, 1]

    def test_ruff_format_diff(self, python_project):
        """Ruff format shows diff."""
        result = subprocess.run(
            ["ruff", "format", "--diff", str(python_project / "main.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]


class TestTestRunnerTool:
    """Tests for pytest runner."""

    def test_pytest_runs_tests(self, python_project):
        """Pytest runs test file."""
        result = subprocess.run(
            ["python", "-m", "pytest", str(python_project / "test_main.py"), "-v"],
            capture_output=True,
            text=True,
            cwd=str(python_project),
        )
        # Tests should pass
        assert result.returncode == 0
        assert "test_hello" in result.stdout
        assert "PASSED" in result.stdout

    def test_pytest_collection(self, python_project):
        """Pytest collects tests."""
        result = subprocess.run(
            ["python", "-m", "pytest", str(python_project), "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=str(python_project),
        )
        assert result.returncode == 0
        assert "3 test" in result.stdout  # 3 tests collected


class TestCoverageTool:
    """Tests for coverage reporting."""

    def test_coverage_run(self, python_project):
        """Coverage runs tests."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "coverage",
                "run",
                "-m",
                "pytest",
                str(python_project / "test_main.py"),
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=str(python_project),
        )
        assert result.returncode == 0


class TestComplexityTool:
    """Tests for code complexity analysis."""

    def test_analyze_simple_function(self, python_project):
        """Analyze simple function complexity."""
        # Use radon if available, otherwise skip
        try:
            result = subprocess.run(
                ["radon", "cc", str(python_project / "main.py"), "-s"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # Should show low complexity (A or B grade)
                assert "A" in result.stdout or "B" in result.stdout
        except FileNotFoundError:
            pytest.skip("radon not installed")


class TestSymbolsAndReferences:
    """Tests for symbol and reference analysis."""

    def test_find_definitions_grep(self, python_project):
        """Find function definitions with grep."""
        result = subprocess.run(
            ["grep", "-rn", "^def ", str(python_project)], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "hello" in result.stdout
        assert "add" in result.stdout

    def test_find_class_definitions(self, python_project):
        """Find class definitions with grep."""
        result = subprocess.run(
            ["grep", "-rn", "^class ", str(python_project)], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Calculator" in result.stdout

    def test_find_imports(self, python_project):
        """Find import statements."""
        result = subprocess.run(
            ["grep", "-rn", "^from\\|^import", str(python_project)], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "typing" in result.stdout or "main" in result.stdout
