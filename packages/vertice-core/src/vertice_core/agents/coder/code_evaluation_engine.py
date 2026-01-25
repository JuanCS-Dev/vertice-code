"""
Code Evaluation Engine - Quality assessment and scoring logic

Extracted from CoderAgent for better modularity and maintainability.
"""

from __future__ import annotations

import ast
import logging
import tempfile
from pathlib import Path
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeQualityMetrics:
    """Comprehensive code quality metrics."""

    syntax_valid: bool = False
    has_imports: bool = False
    has_functions: bool = False
    has_classes: bool = False
    complexity_score: int = 0
    line_count: int = 0
    docstring_coverage: float = 0.0
    naming_conventions: float = 0.0
    error_messages: List[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []


@dataclass
class EvaluationResult:
    """Result of code evaluation."""

    quality_score: int  # 0-100
    metrics: CodeQualityMetrics
    recommendations: List[str]
    is_production_ready: bool


class CodeEvaluationEngine:
    """
    Engine for evaluating code quality and providing feedback.

    Separated from agent logic for better testability and maintainability.
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "vertice_code_eval"

    async def evaluate_code(self, code: str, language: str = "python") -> EvaluationResult:
        """
        Evaluate code quality comprehensively.

        Args:
            code: Source code to evaluate
            language: Programming language

        Returns:
            Detailed evaluation result
        """
        metrics = self._analyze_code_structure(code, language)
        quality_score = self._calculate_quality_score(metrics)
        recommendations = self._generate_recommendations(metrics, quality_score)

        is_production_ready = (
            metrics.syntax_valid and quality_score >= 70 and len(metrics.error_messages) == 0
        )

        return EvaluationResult(
            quality_score=quality_score,
            metrics=metrics,
            recommendations=recommendations,
            is_production_ready=is_production_ready,
        )

    def _analyze_code_structure(self, code: str, language: str) -> CodeQualityMetrics:
        """Analyze code structure and extract metrics."""
        metrics = CodeQualityMetrics()

        if language == "python":
            return self._analyze_python_code(code)
        else:
            # Basic analysis for other languages
            metrics.syntax_valid = True
            metrics.line_count = len(code.split("\n"))
            return metrics

    def _analyze_python_code(self, code: str) -> CodeQualityMetrics:
        """Analyze Python code specifically."""
        metrics = CodeQualityMetrics()
        metrics.line_count = len(code.split("\n"))

        try:
            tree = ast.parse(code)
            metrics.syntax_valid = True

            # Analyze AST
            analyzer = PythonCodeAnalyzer()
            analyzer.visit(tree)

            metrics.has_imports = analyzer.has_imports
            metrics.has_functions = analyzer.has_functions
            metrics.has_classes = analyzer.has_classes
            metrics.complexity_score = analyzer.complexity_score

            # Additional checks
            metrics.docstring_coverage = self._check_docstring_coverage(tree)
            metrics.naming_conventions = self._check_naming_conventions(tree)

        except SyntaxError as e:
            metrics.syntax_valid = False
            metrics.error_messages.append(f"Syntax error: {e}")

        return metrics

    def _calculate_quality_score(self, metrics: CodeQualityMetrics) -> int:
        """Calculate overall quality score 0-100."""
        if not metrics.syntax_valid:
            return 0

        score = 50  # Base score

        # Structure bonuses
        if metrics.has_functions:
            score += 10
        if metrics.has_classes:
            score += 10
        if metrics.has_imports:
            score += 5

        # Quality bonuses
        score += int(metrics.docstring_coverage * 10)  # 0-10 points
        score += int(metrics.naming_conventions * 5)  # 0-5 points

        # Complexity penalties
        if metrics.complexity_score > 10:
            score -= min(20, (metrics.complexity_score - 10))

        # Line count penalties (prefer focused code)
        if metrics.line_count > 100:
            score -= min(15, (metrics.line_count - 100) // 10)

        return max(0, min(100, score))

    def _generate_recommendations(self, metrics: CodeQualityMetrics, score: int) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if not metrics.syntax_valid:
            recommendations.append("Fix syntax errors before proceeding")

        if score < 50:
            recommendations.append("Consider rewriting with better structure")

        if metrics.complexity_score > 15:
            recommendations.append("Break down complex functions into smaller ones")

        if metrics.docstring_coverage < 0.5:
            recommendations.append("Add comprehensive docstrings to all public functions")

        if not metrics.has_functions and not metrics.has_classes:
            recommendations.append("Consider adding functions or classes for better organization")

        return recommendations

    def _check_docstring_coverage(self, tree: ast.AST) -> float:
        """Check what percentage of functions/classes have docstrings."""
        functions_and_classes = []
        documented = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                functions_and_classes.append(node)
                if ast.get_docstring(node):
                    documented += 1

        return documented / len(functions_and_classes) if functions_and_classes else 0.0

    def _check_naming_conventions(self, tree: ast.AST) -> float:
        """Check adherence to Python naming conventions."""
        violations = 0
        total_names = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Name)):
                total_names += 1
                name = getattr(node, "name", getattr(node, "id", None))
                if name:
                    if isinstance(node, ast.ClassDef) and not name[0].isupper():
                        violations += 1
                    elif isinstance(node, ast.FunctionDef) and not name.islower():
                        violations += 1

        return 1.0 - (violations / total_names) if total_names else 0.0


class PythonCodeAnalyzer(ast.NodeVisitor):
    """AST visitor for Python code analysis."""

    def __init__(self):
        self.has_imports = False
        self.has_functions = False
        self.has_classes = False
        self.complexity_score = 0

    def visit_Import(self, node):
        self.has_imports = True

    def visit_ImportFrom(self, node):
        self.has_imports = True

    def visit_FunctionDef(self, node):
        self.has_functions = True
        self.complexity_score += self._calculate_function_complexity(node)

    def visit_ClassDef(self, node):
        self.has_classes = True

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                complexity += len(child.values) - 1

        return complexity
