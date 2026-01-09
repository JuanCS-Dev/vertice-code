#!/usr/bin/env python3
"""
Code Quality Automation for Vertice-Code.

Automated code quality checks including:
- Linting with Ruff
- Type checking with MyPy
- Import sorting with isort
- Security scanning with Bandit
- Complexity analysis
- Coverage reporting
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class QualityResult:
    """Result of a quality check."""

    tool_name: str
    passed: bool
    score: float  # 0-100
    issues_found: int
    issues_fixed: int
    output: str
    recommendations: List[str]


class CodeQualityChecker:
    """Automated code quality checking system."""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.python_files = self._find_python_files()
        self.results: List[QualityResult] = []

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for pattern in ["**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))

        # Exclude common directories
        exclude_patterns = [
            "**/__pycache__/**",
            "**/.git/**",
            "**/node_modules/**",
            "**/build/**",
            "**/dist/**",
            "**/.venv/**",
            "**/venv/**",
        ]

        filtered_files = []
        for file_path in python_files:
            excluded = False
            for exclude in exclude_patterns:
                if file_path.match(exclude):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)

        return filtered_files

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all quality checks."""
        print("🔍 Running comprehensive code quality checks...")
        print(f"📁 Found {len(self.python_files)} Python files to analyze")
        print("=" * 60)

        # Run individual checks
        self._run_ruff_check()
        self._run_mypy_check()
        self._run_isort_check()
        self._run_bandit_check()
        self._run_complexity_check()
        self._run_coverage_check()

        # Generate summary
        summary = self._generate_summary()
        self._print_summary(summary)

        return summary

    def _run_ruff_check(self):
        """Run Ruff linter and fixer."""
        print("\n🐶 Running Ruff (Linting & Formatting)...")

        try:
            # Check for issues
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            issues_found = 0
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    issues_found = len(issues)
                except json.JSONDecodeError:
                    issues_found = result.stdout.count("\n") if result.stdout else 0

            # Try to fix issues
            fix_result = subprocess.run(
                ["ruff", "check", "--fix", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            issues_fixed = 0
            if fix_result.returncode == 0 and fix_result.stdout:
                issues_fixed = fix_result.stdout.count("Fixed")

            score = max(0, 100 - (issues_found * 2))
            passed = issues_found == 0

            recommendations = []
            if issues_found > 0:
                recommendations.append(f"Fix {issues_found} Ruff violations")
                recommendations.append("Run 'ruff check --fix .' to auto-fix issues")

            self.results.append(
                QualityResult(
                    tool_name="Ruff",
                    passed=passed,
                    score=score,
                    issues_found=issues_found,
                    issues_fixed=issues_fixed,
                    output=result.stdout + result.stderr,
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="Ruff",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"Ruff not available or timed out: {e}",
                    recommendations=["Install Ruff: pip install ruff"],
                )
            )

    def _run_mypy_check(self):
        """Run MyPy type checking."""
        print("\n🔍 Running MyPy (Type Checking)...")

        try:
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports", "--no-error-summary", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Count errors (lines that start with file path)
            issues_found = len(
                [
                    line
                    for line in result.stdout.split("\n")
                    if line.strip() and not line.startswith(" ") and ":" in line
                ]
            )

            score = max(0, 100 - (issues_found * 5))
            passed = result.returncode == 0

            recommendations = []
            if issues_found > 0:
                recommendations.append(f"Fix {issues_found} type checking errors")
                recommendations.append("Add type hints to functions and variables")

            self.results.append(
                QualityResult(
                    tool_name="MyPy",
                    passed=passed,
                    score=score,
                    issues_found=issues_found,
                    issues_fixed=0,
                    output=result.stdout + result.stderr,
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="MyPy",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"MyPy not available or timed out: {e}",
                    recommendations=["Install MyPy: pip install mypy"],
                )
            )

    def _run_isort_check(self):
        """Run isort import sorting."""
        print("\n📦 Running isort (Import Sorting)...")

        try:
            # Check for issues
            result = subprocess.run(
                ["isort", "--check-only", "--diff", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            issues_found = 1 if result.returncode != 0 else 0

            # Try to fix
            fix_result = subprocess.run(
                ["isort", "."], cwd=self.project_root, capture_output=True, text=True, timeout=300
            )

            issues_fixed = 1 if fix_result.returncode == 0 and fix_result.stdout.strip() else 0

            score = 100 if issues_found == 0 else 50
            passed = issues_found == 0

            recommendations = []
            if issues_found > 0:
                recommendations.append("Import statements need sorting")
                recommendations.append("Run 'isort .' to fix import order")

            self.results.append(
                QualityResult(
                    tool_name="isort",
                    passed=passed,
                    score=score,
                    issues_found=issues_found,
                    issues_fixed=issues_fixed,
                    output=result.stdout + result.stderr,
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="isort",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"isort not available or timed out: {e}",
                    recommendations=["Install isort: pip install isort"],
                )
            )

    def _run_bandit_check(self):
        """Run Bandit security scanning."""
        print("\n🔒 Running Bandit (Security Scanning)...")

        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-r", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            issues_found = 0
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    issues_found = len(data.get("results", []))
                except json.JSONDecodeError:
                    issues_found = result.stdout.count('"issue_severity":')

            score = max(0, 100 - (issues_found * 10))
            passed = issues_found == 0

            recommendations = []
            if issues_found > 0:
                recommendations.append(f"Fix {issues_found} security vulnerabilities")
                recommendations.append("Review Bandit report for severity levels")

            self.results.append(
                QualityResult(
                    tool_name="Bandit",
                    passed=passed,
                    score=score,
                    issues_found=issues_found,
                    issues_fixed=0,
                    output=result.stdout + result.stderr,
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="Bandit",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"Bandit not available or timed out: {e}",
                    recommendations=["Install Bandit: pip install bandit"],
                )
            )

    def _run_complexity_check(self):
        """Run complexity analysis using radon."""
        print("\n🧩 Running Complexity Analysis...")

        try:
            # Check cyclomatic complexity
            result = subprocess.run(
                ["radon", "cc", "--min", "B", "--json", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            issues_found = 0
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # Count functions with complexity > 10
                    for file_data in data.values():
                        for func_data in file_data.values():
                            if isinstance(func_data, dict) and func_data.get("complexity", 0) > 10:
                                issues_found += 1
                except json.JSONDecodeError:
                    issues_found = result.stdout.count('"complexity":')

            score = max(0, 100 - (issues_found * 5))
            passed = issues_found == 0

            recommendations = []
            if issues_found > 0:
                recommendations.append(f"Refactor {issues_found} functions with high complexity")
                recommendations.append("Break down complex functions into smaller ones")

            self.results.append(
                QualityResult(
                    tool_name="Complexity",
                    passed=passed,
                    score=score,
                    issues_found=issues_found,
                    issues_fixed=0,
                    output=result.stdout + result.stderr,
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="Complexity",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"radon not available or timed out: {e}",
                    recommendations=["Install radon: pip install radon"],
                )
            )

    def _run_coverage_check(self):
        """Run coverage analysis."""
        print("\n📊 Running Coverage Analysis...")

        try:
            # Run tests with coverage
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            coverage_percent = 0.0
            if result.returncode == 0:
                # Try to parse coverage report
                try:
                    with open(self.project_root / "coverage.json", "r") as f:
                        coverage_data = json.load(f)
                        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
                except (FileNotFoundError, json.JSONDecodeError):
                    coverage_percent = 50.0  # Default assumption

            score = coverage_percent
            passed = coverage_percent >= 80.0

            recommendations = []
            if not passed:
                recommendations.append(
                    f"Increase test coverage from {coverage_percent:.1f}% to 80%+"
                )
                recommendations.append("Add unit tests for uncovered functions")

            self.results.append(
                QualityResult(
                    tool_name="Coverage",
                    passed=passed,
                    score=score,
                    issues_found=max(0, 80 - int(coverage_percent)),
                    issues_fixed=0,
                    output=f"Coverage: {coverage_percent:.1f}%",
                    recommendations=recommendations,
                )
            )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                QualityResult(
                    tool_name="Coverage",
                    passed=False,
                    score=0,
                    issues_found=0,
                    issues_fixed=0,
                    output=f"Coverage analysis failed: {e}",
                    recommendations=["Install pytest-cov: pip install pytest-cov"],
                )
            )

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive quality summary."""
        total_score = (
            sum(result.score for result in self.results) / len(self.results) if self.results else 0
        )
        total_issues = sum(result.issues_found for result in self.results)
        total_fixed = sum(result.issues_fixed for result in self.results)

        # Count passed checks
        passed_checks = sum(1 for result in self.results if result.passed)
        total_checks = len(self.results)

        # Collect all recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)

        return {
            "overall_score": round(total_score, 1),
            "overall_grade": self._calculate_grade(total_score),
            "checks_passed": passed_checks,
            "total_checks": total_checks,
            "total_issues": total_issues,
            "issues_fixed": total_fixed,
            "recommendations": list(set(all_recommendations)),  # Remove duplicates
            "detailed_results": [
                {
                    "tool": result.tool_name,
                    "passed": result.passed,
                    "score": result.score,
                    "issues": result.issues_found,
                    "fixed": result.issues_fixed,
                    "recommendations": result.recommendations,
                }
                for result in self.results
            ],
        }

    def _calculate_grade(self, score: float) -> str:
        """Calculate quality grade based on score."""
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Very Good)"
        elif score >= 70:
            return "B (Good)"
        elif score >= 60:
            return "C (Fair)"
        elif score >= 50:
            return "D (Poor)"
        else:
            return "F (Failing)"

    def _print_summary(self, summary: Dict[str, Any]):
        """Print formatted quality summary."""
        print("\n" + "=" * 70)
        print("🎯 CODE QUALITY REPORT")
        print("=" * 70)

        print(f"Overall Score: {summary['overall_score']}/100")
        print(f"Grade: {summary['overall_grade']}")
        print(f"Checks Passed: {summary['checks_passed']}/{summary['total_checks']}")
        print(f"Total Issues: {summary['total_issues']}")
        print(f"Issues Fixed: {summary['issues_fixed']}")

        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)

        for result in summary["detailed_results"]:
            status = "✅" if result["passed"] else "❌"
            print("15")

        print("\n💡 RECOMMENDATIONS:")
        print("-" * 30)

        for rec in summary["recommendations"]:
            print(f"• {rec}")

        print("\n" + "=" * 70)

        # Final assessment
        if summary["overall_score"] >= 80:
            print("🎉 Code quality is EXCELLENT! Ready for production.")
        elif summary["overall_score"] >= 60:
            print("👍 Code quality is GOOD. Minor improvements needed.")
        else:
            print("⚠️ Code quality needs SIGNIFICANT improvement.")


def main():
    """Run code quality checks."""
    checker = CodeQualityChecker()
    summary = checker.run_all_checks()

    # Exit with appropriate code
    exit_code = 0 if summary["overall_score"] >= 70 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
