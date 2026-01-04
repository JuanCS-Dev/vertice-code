"""
Reviewer Sub-Agents.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Contains specialized review agents:
- PerformanceAgent: Performance analysis
- TestCoverageAgent: Test coverage checking
- CodeGraphAnalysisAgent: Graph-based code analysis

Author: Vertice Team
Date: 2026-01-02
"""

import logging
from typing import List

import networkx as nx

from .types import (
    CodeGraphNode,
    CodeIssue,
    ComplexityMetrics,
    IssueCategory,
    IssueSeverity,
)

logger = logging.getLogger(__name__)


class PerformanceAgent:
    """Specialized agent for performance analysis."""

    async def analyze(self, code: str, metrics: List[ComplexityMetrics]) -> List[CodeIssue]:
        issues = []
        for m in metrics:
            if m.cognitive > 15:
                issues.append(
                    CodeIssue(
                        file="",
                        line=0,
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.PERFORMANCE,
                        message=f"Function '{m.function_name}' has high cognitive complexity ({m.cognitive})",
                        explanation="High cognitive complexity makes code hard to understand and maintain",
                        fix_suggestion="Break down into smaller functions",
                        confidence=0.95,
                    )
                )
        return issues


class TestCoverageAgent:
    """Checks test coverage and suggests missing tests."""

    async def analyze(self, files: List[str]) -> List[CodeIssue]:
        issues = []
        # Check if test files exist
        has_tests = any("test_" in f or "_test.py" in f for f in files)
        if not has_tests:
            issues.append(
                CodeIssue(
                    file="",
                    line=0,
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.TESTING,
                    message="No test files found in the changeset",
                    explanation="Code changes should include tests",
                    fix_suggestion="Add unit tests for the new functionality",
                    confidence=1.0,
                )
            )
        return issues


class CodeGraphAnalysisAgent:
    """
    Advanced graph analysis agent.

    Uses NetworkX to detect:
    - Circular dependencies (import cycles)
    - Dead code (unreachable functions)
    - High coupling (functions with too many dependencies)
    - Impact analysis (what breaks if X changes)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze(self, graph: nx.DiGraph, nodes: List[CodeGraphNode]) -> List[CodeIssue]:
        """Perform graph-based analysis."""
        issues = []

        if not graph or len(graph.nodes) == 0:
            return issues

        # 1. Detect circular dependencies
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                for cycle in cycles:
                    cycle_names = [n.split("::")[-1] for n in cycle]
                    issues.append(
                        CodeIssue(
                            file="",
                            line=0,
                            severity=IssueSeverity.HIGH,
                            category=IssueCategory.ARCHITECTURE,
                            message=f"Circular dependency detected: {' -> '.join(cycle_names)} -> {cycle_names[0]}",
                            explanation="Circular dependencies make code hard to understand, test, and maintain",
                            fix_suggestion="Refactor to break the cycle - extract shared logic or use dependency injection",
                            confidence=1.0,
                        )
                    )
        except Exception as e:
            self.logger.debug(f"Failed to detect cyclic imports: {e}")

        # 2. Detect dead code (unreachable nodes)
        if len(graph.nodes) > 0:
            entry_points = [n for n in graph.nodes if graph.in_degree(n) == 0]

            if entry_points:
                reachable = set()
                for entry in entry_points:
                    try:
                        reachable.update(nx.descendants(graph, entry))
                        reachable.add(entry)
                    except Exception as e:
                        self.logger.debug(f"Failed to find descendants for {entry}: {e}")

                dead_nodes = set(graph.nodes) - reachable
                if dead_nodes:
                    for dead_id in dead_nodes:
                        func_name = dead_id.split("::")[-1]
                        issues.append(
                            CodeIssue(
                                file="",
                                line=0,
                                severity=IssueSeverity.LOW,
                                category=IssueCategory.MAINTAINABILITY,
                                message=f"Function '{func_name}' appears to be dead code (never called)",
                                explanation="Unused code increases maintenance burden and confusion",
                                fix_suggestion="Remove if truly unused, or add tests to verify it's needed",
                                confidence=0.7,
                            )
                        )

        # 3. Detect high coupling (God functions)
        node_map = {node.id: node for node in nodes}
        for node_id in graph.nodes:
            out_degree = graph.out_degree(node_id)
            in_degree = graph.in_degree(node_id)

            # High fan-out = calls too many things
            if out_degree > 10:
                func_name = node_id.split("::")[-1]
                issues.append(
                    CodeIssue(
                        file="",
                        line=0,
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.ARCHITECTURE,
                        message=f"Function '{func_name}' has high coupling (calls {out_degree} other functions)",
                        explanation="High coupling makes code fragile and hard to change",
                        fix_suggestion="Break down into smaller, more focused functions",
                        confidence=0.85,
                    )
                )

            # High fan-in = too many things depend on it
            if in_degree > 15:
                func_name = node_id.split("::")[-1]
                node = node_map.get(node_id)
                issues.append(
                    CodeIssue(
                        file="",
                        line=0,
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.ARCHITECTURE,
                        message=f"Function '{func_name}' is a critical dependency ({in_degree} callers)",
                        explanation=f"Changes to this function impact {in_degree} other functions. Ensure it's well-tested.",
                        fix_suggestion="Add comprehensive tests and consider making it more stable/immutable",
                        confidence=1.0,
                    )
                )

        # 4. Detect long dependency chains (deep call stacks)
        if len(graph.nodes) > 0:
            entry_points = [n for n in graph.nodes if graph.in_degree(n) == 0]
            for entry in entry_points:
                try:
                    paths = nx.single_source_shortest_path_length(graph, entry)
                    max_depth = max(paths.values()) if paths else 0

                    if max_depth > 6:
                        func_name = entry.split("::")[-1]
                        issues.append(
                            CodeIssue(
                                file="",
                                line=0,
                                severity=IssueSeverity.MEDIUM,
                                category=IssueCategory.ARCHITECTURE,
                                message=f"Function '{func_name}' has a deep call chain (depth {max_depth})",
                                explanation="Deep call chains make debugging difficult and increase coupling",
                                fix_suggestion="Consider flattening the architecture or breaking into smaller modules",
                                confidence=0.8,
                            )
                        )
                except Exception as e:
                    self.logger.debug(f"Failed to calculate call chain depth for {entry}: {e}")

        return issues


__all__ = [
    "PerformanceAgent",
    "TestCoverageAgent",
    "CodeGraphAnalysisAgent",
]
