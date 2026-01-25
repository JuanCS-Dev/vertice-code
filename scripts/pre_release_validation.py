#!/usr/bin/env python3
"""
Pre-Release Validation Script for Vertice-Code
===============================================

A comprehensive, resilient validation system that checks every aspect
of the codebase before release. Designed for Jules automation.

Philosophy: NEVER BLOCK. Document failures and continue.

Usage:
    python scripts/pre_release_validation.py
    python scripts/pre_release_validation.py --quick  # Fast mode
    python scripts/pre_release_validation.py --fix    # Auto-fix when possible

Output:
    - Console: Real-time progress
    - File: PRE_RELEASE_REPORT.md (detailed report)
    - Exit code: 0 (success with warnings) or 1 (critical failures only)
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
REPORT_PATH = PROJECT_ROOT / "PRE_RELEASE_REPORT.md"

PACKAGES = [
    "vertice_core",
    "vertice_tui",
    "vertice_core",
    "prometheus",
    "core",
    "agents",
    "providers",
    "memory",
]

CRITICAL_MODULES = [
    "vertice_core.main",
    "vertice_core.cli_app",
    "vertice_tui.__init__",
    "vertice_core.types",
]

ENTRY_POINTS = [
    ("vtc", "vertice_core.main:cli_main"),
    ("vertice", "vertice_core.main:cli_main"),
    ("vertice-cli", "vertice_core.main:cli_main"),
]

TEST_CATEGORIES = [
    ("unit", "tests/unit/", 60),
    ("integration", "tests/integration/", 120),
    ("e2e_quick", "tests/e2e/test_e2e_shell_integration.py", 180),
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================


class Severity(Enum):
    """Issue severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    category: str
    severity: Severity
    message: str
    file: str | None = None
    line: int | None = None
    suggestion: str | None = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    duration: float
    issues: list[ValidationIssue] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class ValidationReport:
    """Complete validation report."""

    started_at: datetime
    finished_at: datetime | None = None
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def critical_issues(self) -> int:
        return sum(1 for r in self.results for i in r.issues if i.severity == Severity.CRITICAL)

    @property
    def passed_checks(self) -> int:
        return sum(1 for r in self.results if r.passed and not r.skipped)

    @property
    def failed_checks(self) -> int:
        return sum(1 for r in self.results if not r.passed and not r.skipped)

    @property
    def skipped_checks(self) -> int:
        return sum(1 for r in self.results if r.skipped)


# =============================================================================
# UTILITIES
# =============================================================================


def run_command(
    cmd: list[str],
    timeout: int = 60,
    capture: bool = True,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    """Run a command safely with timeout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd or PROJECT_ROOT,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -3, "", f"Command failed: {e}"


def safe_import(module_name: str) -> tuple[bool, str | None]:
    """Safely try to import a module."""
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in a directory."""
    if not directory.exists():
        return []
    return list(directory.rglob("*.py"))


def parse_python_file(filepath: Path) -> tuple[ast.Module | None, str | None]:
    """Parse a Python file into AST."""
    try:
        content = filepath.read_text(encoding="utf-8")
        return ast.parse(content, filename=str(filepath)), None
    except SyntaxError as e:
        return None, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return None, f"Parse error: {e}"


# =============================================================================
# VALIDATORS
# =============================================================================


class Validator:
    """Base validator with resilient execution."""

    name: str = "base"
    description: str = "Base validator"

    def __init__(self, quick_mode: bool = False, auto_fix: bool = False):
        self.quick_mode = quick_mode
        self.auto_fix = auto_fix

    def validate(self) -> ValidationResult:
        """Run validation with error handling."""
        start = time.time()
        try:
            result = self._validate()
            result.duration = time.time() - start
            return result
        except Exception as e:
            # Never crash - document and continue
            return ValidationResult(
                name=self.name,
                passed=False,
                duration=time.time() - start,
                issues=[
                    ValidationIssue(
                        category=self.name,
                        severity=Severity.ERROR,
                        message=f"Validator crashed: {e}",
                        suggestion="Check validator implementation",
                    )
                ],
                details={"traceback": traceback.format_exc()},
            )

    def _validate(self) -> ValidationResult:
        """Override in subclasses."""
        raise NotImplementedError


class ImportValidator(Validator):
    """Validate all module imports."""

    name = "imports"
    description = "Check all modules can be imported"

    def _validate(self) -> ValidationResult:
        issues = []
        imported = 0
        failed = 0

        for package in PACKAGES:
            package_dir = PROJECT_ROOT / package.replace(".", "/")
            if not package_dir.exists():
                continue

            for py_file in find_python_files(package_dir):
                # Skip test files and __pycache__
                if "__pycache__" in str(py_file) or "test_" in py_file.name:
                    continue

                # Convert path to module name
                rel_path = py_file.relative_to(PROJECT_ROOT)
                module_name = str(rel_path).replace("/", ".").replace(".py", "")
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]

                success, error = safe_import(module_name)
                if success:
                    imported += 1
                else:
                    failed += 1
                    severity = (
                        Severity.CRITICAL if module_name in CRITICAL_MODULES else Severity.ERROR
                    )
                    issues.append(
                        ValidationIssue(
                            category="imports",
                            severity=severity,
                            message=f"Failed to import {module_name}",
                            file=str(py_file),
                            suggestion=error,
                        )
                    )

                # Quick mode: stop after first error per package
                if self.quick_mode and failed > 0:
                    break

        return ValidationResult(
            name=self.name,
            passed=failed == 0,
            duration=0,
            issues=issues,
            details={"imported": imported, "failed": failed},
        )


class SyntaxValidator(Validator):
    """Validate Python syntax in all files."""

    name = "syntax"
    description = "Check Python syntax in all files"

    def _validate(self) -> ValidationResult:
        issues = []
        checked = 0

        for package in PACKAGES:
            package_dir = PROJECT_ROOT / package.replace(".", "/")
            if not package_dir.exists():
                continue

            for py_file in find_python_files(package_dir):
                if "__pycache__" in str(py_file):
                    continue

                checked += 1
                tree, error = parse_python_file(py_file)

                if error:
                    issues.append(
                        ValidationIssue(
                            category="syntax",
                            severity=Severity.CRITICAL,
                            message=error,
                            file=str(py_file),
                        )
                    )

        return ValidationResult(
            name=self.name,
            passed=len(issues) == 0,
            duration=0,
            issues=issues,
            details={"files_checked": checked},
        )


class TypeHintValidator(Validator):
    """Check for missing type hints in public APIs."""

    name = "type_hints"
    description = "Check type hints in public functions"

    def _validate(self) -> ValidationResult:
        issues = []
        checked = 0
        missing = 0

        for package in PACKAGES:
            package_dir = PROJECT_ROOT / package.replace(".", "/")
            if not package_dir.exists():
                continue

            for py_file in find_python_files(package_dir):
                if "__pycache__" in str(py_file) or "test_" in py_file.name:
                    continue

                tree, error = parse_python_file(py_file)
                if not tree:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private functions
                        if node.name.startswith("_"):
                            continue

                        checked += 1

                        # Check return type
                        if node.returns is None:
                            missing += 1
                            issues.append(
                                ValidationIssue(
                                    category="type_hints",
                                    severity=Severity.WARNING,
                                    message=f"Missing return type hint: {node.name}",
                                    file=str(py_file),
                                    line=node.lineno,
                                    suggestion="Add -> ReturnType annotation",
                                )
                            )

                        # Check argument types (skip self/cls)
                        for arg in node.args.args[1:] if node.args.args else []:
                            if arg.annotation is None:
                                issues.append(
                                    ValidationIssue(
                                        category="type_hints",
                                        severity=Severity.INFO,
                                        message=f"Missing type hint for arg '{arg.arg}' in {node.name}",
                                        file=str(py_file),
                                        line=node.lineno,
                                    )
                                )

                # Quick mode: limit issues per file
                if self.quick_mode and len(issues) > 50:
                    break

        return ValidationResult(
            name=self.name,
            passed=True,  # Warnings don't fail
            duration=0,
            issues=issues[:100] if self.quick_mode else issues,  # Limit output
            details={"functions_checked": checked, "missing_hints": missing},
        )


class BlackValidator(Validator):
    """Check Black formatting."""

    name = "black"
    description = "Check code formatting with Black"

    def _validate(self) -> ValidationResult:
        issues = []

        cmd = ["black", "--check", "--quiet"]
        cmd.extend(p for p in PACKAGES if (PROJECT_ROOT / p).exists())

        if self.auto_fix:
            # Remove --check to actually format
            cmd = ["black", "--quiet"]
            cmd.extend(p for p in PACKAGES if (PROJECT_ROOT / p).exists())

        code, stdout, stderr = run_command(cmd, timeout=120)

        if code == 0:
            return ValidationResult(
                name=self.name,
                passed=True,
                duration=0,
                details={"formatted": self.auto_fix},
            )

        if code == 1 and not self.auto_fix:
            # Parse which files need formatting
            check_cmd = ["black", "--check"]
            check_cmd.extend(p for p in PACKAGES if (PROJECT_ROOT / p).exists())
            _, _, check_stderr = run_command(check_cmd, timeout=120)

            for line in check_stderr.split("\n"):
                if "would reformat" in line:
                    filepath = line.replace("would reformat ", "").strip()
                    issues.append(
                        ValidationIssue(
                            category="black",
                            severity=Severity.WARNING,
                            message="File needs formatting",
                            file=filepath,
                            auto_fixable=True,
                            suggestion="Run: black <file>",
                        )
                    )

        if code < 0:
            issues.append(
                ValidationIssue(
                    category="black",
                    severity=Severity.ERROR,
                    message=stderr or "Black command failed",
                )
            )

        return ValidationResult(
            name=self.name,
            passed=code == 0,
            duration=0,
            issues=issues,
            details={"exit_code": code},
        )


class RuffValidator(Validator):
    """Check linting with Ruff."""

    name = "ruff"
    description = "Check linting with Ruff"

    def _validate(self) -> ValidationResult:
        issues = []

        cmd = ["ruff", "check", "--output-format=json"]
        if self.auto_fix:
            cmd.append("--fix")
        cmd.extend(p for p in PACKAGES if (PROJECT_ROOT / p).exists())

        code, stdout, stderr = run_command(cmd, timeout=120)

        if code < 0:
            return ValidationResult(
                name=self.name,
                passed=False,
                duration=0,
                issues=[
                    ValidationIssue(
                        category="ruff",
                        severity=Severity.ERROR,
                        message=stderr or "Ruff command failed",
                    )
                ],
            )

        # Parse JSON output
        try:
            if stdout.strip():
                ruff_issues = json.loads(stdout)
                for ri in ruff_issues[:100]:  # Limit
                    issues.append(
                        ValidationIssue(
                            category="ruff",
                            severity=Severity.WARNING,
                            message=f"[{ri.get('code', '?')}] {ri.get('message', '?')}",
                            file=ri.get("filename"),
                            line=ri.get("location", {}).get("row"),
                            auto_fixable=ri.get("fix") is not None,
                        )
                    )
        except json.JSONDecodeError:
            pass

        return ValidationResult(
            name=self.name,
            passed=len(issues) == 0,
            duration=0,
            issues=issues,
            details={"total_issues": len(issues)},
        )


class DependencyValidator(Validator):
    """Validate dependencies in pyproject.toml."""

    name = "dependencies"
    description = "Check dependencies are installable"

    def _validate(self) -> ValidationResult:
        issues = []

        pyproject = PROJECT_ROOT / "pyproject.toml"
        if not pyproject.exists():
            return ValidationResult(
                name=self.name,
                passed=False,
                duration=0,
                issues=[
                    ValidationIssue(
                        category="dependencies",
                        severity=Severity.CRITICAL,
                        message="pyproject.toml not found",
                    )
                ],
            )

        # Try pip check
        code, stdout, stderr = run_command(
            ["pip", "check"],
            timeout=30,
        )

        if code != 0:
            for line in stdout.split("\n"):
                if line.strip():
                    issues.append(
                        ValidationIssue(
                            category="dependencies",
                            severity=Severity.ERROR,
                            message=line.strip(),
                            suggestion="Run: pip install -e .",
                        )
                    )

        # Check for common missing deps
        try:
            import networkx  # noqa: F401
        except ImportError:
            issues.append(
                ValidationIssue(
                    category="dependencies",
                    severity=Severity.ERROR,
                    message="networkx not installed",
                    suggestion="Run: pip install networkx",
                )
            )

        return ValidationResult(
            name=self.name,
            passed=len(issues) == 0,
            duration=0,
            issues=issues,
        )


class EntryPointValidator(Validator):
    """Validate CLI entry points work."""

    name = "entry_points"
    description = "Check CLI entry points are functional"

    def _validate(self) -> ValidationResult:
        issues = []
        working = 0

        for name, module_path in ENTRY_POINTS:
            # Check if command exists
            code, stdout, stderr = run_command(
                [name, "--help"],
                timeout=10,
            )

            if code == 0:
                working += 1
            else:
                issues.append(
                    ValidationIssue(
                        category="entry_points",
                        severity=Severity.ERROR,
                        message=f"Entry point '{name}' failed",
                        suggestion=f"Check {module_path}",
                    )
                )

        return ValidationResult(
            name=self.name,
            passed=working == len(ENTRY_POINTS),
            duration=0,
            issues=issues,
            details={"working": working, "total": len(ENTRY_POINTS)},
        )


class TestValidator(Validator):
    """Run test suites."""

    name = "tests"
    description = "Run test suites"

    def _validate(self) -> ValidationResult:
        issues = []
        results = {}

        for category, path, timeout in TEST_CATEGORIES:
            if self.quick_mode and category != "unit":
                results[category] = "skipped (quick mode)"
                continue

            test_path = PROJECT_ROOT / path
            if not test_path.exists():
                results[category] = "skipped (not found)"
                continue

            cmd = [
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                f"--timeout={timeout}",
                "-x",  # Stop on first failure
            ]

            code, stdout, stderr = run_command(cmd, timeout=timeout + 30)

            if code == 0:
                results[category] = "passed"
            elif code == 5:
                results[category] = "no tests collected"
            else:
                results[category] = "failed"
                # Extract failure summary
                for line in (stdout + stderr).split("\n"):
                    if "FAILED" in line or "ERROR" in line:
                        issues.append(
                            ValidationIssue(
                                category="tests",
                                severity=Severity.ERROR,
                                message=f"[{category}] {line.strip()[:100]}",
                            )
                        )
                        if len(issues) > 10:
                            break

        all_passed = all(
            v in ("passed", "skipped (quick mode)", "skipped (not found)", "no tests collected")
            for v in results.values()
        )

        return ValidationResult(
            name=self.name,
            passed=all_passed,
            duration=0,
            issues=issues,
            details=results,
        )


class DocstringValidator(Validator):
    """Check for missing docstrings in public APIs."""

    name = "docstrings"
    description = "Check docstrings in public classes and functions"

    def _validate(self) -> ValidationResult:
        issues = []
        checked = 0
        missing = 0

        for package in PACKAGES[:3]:  # Only main packages
            package_dir = PROJECT_ROOT / package.replace(".", "/")
            if not package_dir.exists():
                continue

            for py_file in find_python_files(package_dir):
                if "__pycache__" in str(py_file) or "test_" in py_file.name:
                    continue

                tree, error = parse_python_file(py_file)
                if not tree:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Skip private
                        if node.name.startswith("_"):
                            continue

                        checked += 1
                        docstring = ast.get_docstring(node)

                        if not docstring:
                            missing += 1
                            issues.append(
                                ValidationIssue(
                                    category="docstrings",
                                    severity=Severity.INFO,
                                    message=f"Missing docstring: {node.name}",
                                    file=str(py_file),
                                    line=node.lineno,
                                )
                            )

                if self.quick_mode and len(issues) > 30:
                    break

        return ValidationResult(
            name=self.name,
            passed=True,  # Info only
            duration=0,
            issues=issues[:50],
            details={"checked": checked, "missing": missing},
        )


class SecurityValidator(Validator):
    """Basic security checks."""

    name = "security"
    description = "Check for common security issues"

    PATTERNS = [
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
        (r"eval\s*\(", "Use of eval()"),
        (r"exec\s*\(", "Use of exec()"),
        (r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "Shell injection risk"),
    ]

    def _validate(self) -> ValidationResult:
        import re

        issues = []

        for package in PACKAGES:
            package_dir = PROJECT_ROOT / package.replace(".", "/")
            if not package_dir.exists():
                continue

            for py_file in find_python_files(package_dir):
                if "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                for pattern, message in self.PATTERNS:
                    for i, line in enumerate(content.split("\n"), 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip if in comment or test
                            if line.strip().startswith("#") or "test" in str(py_file).lower():
                                continue
                            issues.append(
                                ValidationIssue(
                                    category="security",
                                    severity=Severity.WARNING,
                                    message=message,
                                    file=str(py_file),
                                    line=i,
                                )
                            )

        return ValidationResult(
            name=self.name,
            passed=not any(i.severity == Severity.CRITICAL for i in issues),
            duration=0,
            issues=issues[:50],
            details={"issues_found": len(issues)},
        )


class ConfigValidator(Validator):
    """Validate configuration files."""

    name = "config"
    description = "Check configuration files are valid"

    def _validate(self) -> ValidationResult:
        issues = []

        # Check pyproject.toml
        pyproject = PROJECT_ROOT / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                with open(pyproject, "rb") as f:
                    tomllib.load(f)
            except ImportError:
                pass  # Python < 3.11
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        category="config",
                        severity=Severity.CRITICAL,
                        message=f"Invalid pyproject.toml: {e}",
                        file=str(pyproject),
                    )
                )

        # Check .env.example exists
        env_example = PROJECT_ROOT / ".env.example"
        if not env_example.exists():
            issues.append(
                ValidationIssue(
                    category="config",
                    severity=Severity.INFO,
                    message=".env.example not found",
                    suggestion="Create .env.example with required variables",
                )
            )

        # Check AGENTS.md
        agents_md = PROJECT_ROOT / "AGENTS.md"
        if not agents_md.exists():
            issues.append(
                ValidationIssue(
                    category="config",
                    severity=Severity.WARNING,
                    message="AGENTS.md not found",
                )
            )

        return ValidationResult(
            name=self.name,
            passed=not any(i.severity == Severity.CRITICAL for i in issues),
            duration=0,
            issues=issues,
        )


class CircularImportValidator(Validator):
    """Check for circular imports."""

    name = "circular_imports"
    description = "Check for circular import issues"

    def _validate(self) -> ValidationResult:
        issues = []

        # Simple check: try importing main modules
        test_imports = [
            "vertice_core",
            "vertice_tui",
            "vertice_core",
        ]

        for module in test_imports:
            try:
                # Fresh import in subprocess to detect circular imports
                code, stdout, stderr = run_command(
                    [sys.executable, "-c", f"import {module}"],
                    timeout=30,
                )
                if code != 0 and "circular" in stderr.lower():
                    issues.append(
                        ValidationIssue(
                            category="circular_imports",
                            severity=Severity.ERROR,
                            message=f"Circular import in {module}",
                            suggestion=stderr[:200],
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        category="circular_imports",
                        severity=Severity.WARNING,
                        message=f"Could not check {module}: {e}",
                    )
                )

        return ValidationResult(
            name=self.name,
            passed=len(issues) == 0,
            duration=0,
            issues=issues,
        )


class UnusedCodeValidator(Validator):
    """Find potentially unused code."""

    name = "unused_code"
    description = "Find unused imports and variables"

    def _validate(self) -> ValidationResult:
        issues = []

        # Use ruff for unused imports
        cmd = [
            "ruff",
            "check",
            "--select=F401,F841",  # Unused imports, unused variables
            "--output-format=json",
        ]
        cmd.extend(p for p in PACKAGES[:3] if (PROJECT_ROOT / p).exists())

        code, stdout, stderr = run_command(cmd, timeout=60)

        if stdout.strip():
            try:
                ruff_issues = json.loads(stdout)
                for ri in ruff_issues[:30]:
                    issues.append(
                        ValidationIssue(
                            category="unused_code",
                            severity=Severity.INFO,
                            message=f"[{ri.get('code')}] {ri.get('message')}",
                            file=ri.get("filename"),
                            line=ri.get("location", {}).get("row"),
                            auto_fixable=True,
                        )
                    )
            except json.JSONDecodeError:
                pass

        return ValidationResult(
            name=self.name,
            passed=True,  # Info only
            duration=0,
            issues=issues,
            details={"unused_items": len(issues)},
        )


# =============================================================================
# REPORT GENERATOR
# =============================================================================


def generate_report(report: ValidationReport) -> str:
    """Generate Markdown report."""
    lines = [
        "# Pre-Release Validation Report",
        "",
        f"**Generated:** {report.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Finished:** {report.finished_at.strftime('%H:%M:%S') if report.finished_at else 'N/A'}",
        f"**Duration:** {(report.finished_at - report.started_at).total_seconds():.1f}s"
        if report.finished_at
        else "",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Checks | {len(report.results)} |",
        f"| Passed | {report.passed_checks} |",
        f"| Failed | {report.failed_checks} |",
        f"| Skipped | {report.skipped_checks} |",
        f"| Total Issues | {report.total_issues} |",
        f"| Critical Issues | {report.critical_issues} |",
        "",
    ]

    # Status badge
    if report.critical_issues == 0 and report.failed_checks == 0:
        lines.append("**Status: READY FOR RELEASE** ✅")
    elif report.critical_issues == 0:
        lines.append("**Status: READY WITH WARNINGS** ⚠️")
    else:
        lines.append("**Status: NOT READY** ❌")

    lines.extend(["", "## Detailed Results", ""])

    for result in report.results:
        icon = "✅" if result.passed else ("⏭️" if result.skipped else "❌")
        lines.append(f"### {icon} {result.name}")
        lines.append("")

        if result.skipped:
            lines.append(f"*Skipped: {result.skip_reason}*")
        else:
            lines.append(f"**Duration:** {result.duration:.2f}s")

            if result.details:
                lines.append("")
                lines.append("**Details:**")
                for k, v in result.details.items():
                    lines.append(f"- {k}: {v}")

            if result.issues:
                lines.extend(["", "**Issues:**", ""])

                # Group by severity
                by_severity = defaultdict(list)
                for issue in result.issues:
                    by_severity[issue.severity].append(issue)

                for severity in [
                    Severity.CRITICAL,
                    Severity.ERROR,
                    Severity.WARNING,
                    Severity.INFO,
                ]:
                    if severity in by_severity:
                        lines.append(f"*{severity.value.upper()}:*")
                        for issue in by_severity[severity][:10]:
                            file_info = f" ({issue.file}:{issue.line})" if issue.file else ""
                            lines.append(f"- {issue.message}{file_info}")
                        if len(by_severity[severity]) > 10:
                            lines.append(f"  - ... and {len(by_severity[severity]) - 10} more")
                        lines.append("")

        lines.append("")

    # Footer
    lines.extend(
        [
            "---",
            "",
            "*Generated by pre_release_validation.py*",
            f"*Vertice-Code v1.0 | {datetime.now().strftime('%Y-%m-%d')}*",
        ]
    )

    return "\n".join(lines)


# =============================================================================
# MAIN RUNNER
# =============================================================================


def run_validation(quick_mode: bool = False, auto_fix: bool = False) -> ValidationReport:
    """Run all validators."""
    report = ValidationReport(started_at=datetime.now())

    validators: list[type[Validator]] = [
        SyntaxValidator,
        ImportValidator,
        CircularImportValidator,
        DependencyValidator,
        EntryPointValidator,
        BlackValidator,
        RuffValidator,
        TypeHintValidator,
        DocstringValidator,
        SecurityValidator,
        ConfigValidator,
        UnusedCodeValidator,
        TestValidator,  # Last - slowest
    ]

    print("=" * 60)
    print("PRE-RELEASE VALIDATION")
    print("=" * 60)
    print(f"Mode: {'QUICK' if quick_mode else 'FULL'} | Auto-fix: {auto_fix}")
    print("-" * 60)

    for validator_cls in validators:
        validator = validator_cls(quick_mode=quick_mode, auto_fix=auto_fix)
        print(f"\n▶ {validator.name}: {validator.description}...", end=" ", flush=True)

        result = validator.validate()
        report.results.append(result)

        if result.skipped:
            print(f"⏭️  SKIPPED ({result.skip_reason})")
        elif result.passed:
            print(f"✅ PASSED ({result.duration:.1f}s)")
        else:
            print(f"❌ FAILED ({len(result.issues)} issues)")

    report.finished_at = datetime.now()

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(
        f"Passed: {report.passed_checks} | Failed: {report.failed_checks} | Issues: {report.total_issues}"
    )

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pre-release validation for Vertice-Code")
    parser.add_argument("--quick", action="store_true", help="Quick mode (less thorough)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix when possible")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")
    args = parser.parse_args()

    # Change to project root
    os.chdir(PROJECT_ROOT)

    # Run validation
    report = run_validation(quick_mode=args.quick, auto_fix=args.fix)

    # Generate report
    if not args.no_report:
        report_content = generate_report(report)
        REPORT_PATH.write_text(report_content, encoding="utf-8")
        print(f"\n📄 Report saved to: {REPORT_PATH}")

    # Exit code: only fail on critical issues
    if report.critical_issues > 0:
        print("\n❌ CRITICAL ISSUES FOUND - NOT READY FOR RELEASE")
        sys.exit(1)
    elif report.failed_checks > 0:
        print("\n⚠️  WARNINGS FOUND - REVIEW BEFORE RELEASE")
        sys.exit(0)
    else:
        print("\n✅ ALL CHECKS PASSED - READY FOR RELEASE")
        sys.exit(0)


if __name__ == "__main__":
    main()
