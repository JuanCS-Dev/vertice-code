"""
Code Graph Analyzer.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Advanced AST analyzer that builds a code graph with:
- Cyclomatic & Cognitive Complexity
- Control Flow Analysis
- Data Flow Tracking
- Dependency Mapping

Author: Vertice Team
Date: 2026-01-02
"""

import ast
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

from .types import CodeGraphNode, ComplexityMetrics


class CodeGraphAnalyzer(ast.NodeVisitor):
    """
    Advanced AST analyzer that builds a code graph with:
    - Cyclomatic & Cognitive Complexity
    - Control Flow Analysis
    - Data Flow Tracking
    - Dependency Mapping
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.graph = nx.DiGraph()
        self.metrics: List[ComplexityMetrics] = []
        self.nodes: List[CodeGraphNode] = []

        # Current context
        self.current_function: Optional[str] = None
        self.complexity = 0
        self.cognitive = 0
        self.nesting_level = 0
        self.loc = 0
        self.branches = 0
        self.returns = 0
        self.args = 0
        self.line_start = 0

        # Data flow tracking
        self.variables: Dict[str, Set[int]] = {}  # var -> lines where used
        self.function_calls: List[Tuple[str, int]] = []
        # Track calls per function: {caller_func_name: [(called_name, line), ...]}
        self.calls_per_function: Dict[str, List[Tuple[str, int]]] = {}

    def analyze(
        self, tree: ast.AST
    ) -> Tuple[List[ComplexityMetrics], List[CodeGraphNode], nx.DiGraph]:
        """
        Analyze an AST and return complexity metrics, nodes, and dependency graph.

        This is the main entry point. It walks the AST, collects metrics for
        each function, builds CodeGraphNode objects, and constructs a
        dependency graph based on function calls.

        Args:
            tree: Parsed AST from ast.parse()

        Returns:
            Tuple of:
            - List[ComplexityMetrics]: Per-function complexity data
            - List[CodeGraphNode]: Graph nodes for each function/class
            - nx.DiGraph: Dependency graph with call relationships
        """
        self.visit(tree)
        self._build_dependency_edges()
        return self.metrics, self.nodes, self.graph

    def _build_dependency_edges(self):
        """Build edges in the graph based on function calls.

        Fixed: Now correctly tracks which function made which call,
        and excludes self-edges (recursive calls are not circular dependencies).
        """
        # Map function names to their graph IDs
        func_map = {node.name: node.id for node in self.nodes}

        # For each function, add edges for the calls IT made
        for caller_name, calls in self.calls_per_function.items():
            if caller_name not in func_map:
                continue

            caller_id = func_map[caller_name]

            # Add node to graph if not already there
            if caller_id not in self.graph:
                self.graph.add_node(caller_id)

            # Add edges for calls made by this function
            for called_name, line in calls:
                if called_name in func_map:
                    called_id = func_map[called_name]
                    # Skip self-edges (recursive calls are NOT circular dependencies)
                    if caller_id != called_id:
                        self.graph.add_edge(caller_id, called_id, line=line)

        # Also add any nodes not yet in the graph
        for node in self.nodes:
            if node.id not in self.graph:
                self.graph.add_node(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._enter_function(node)
        self.generic_visit(node)
        self._exit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._enter_function(node)
        self.generic_visit(node)
        self._exit_function(node)

    def _enter_function(self, node):
        self.current_function = node.name
        self.complexity = 1  # Base
        self.cognitive = 0
        self.loc = node.end_lineno - node.lineno if node.end_lineno else 0
        self.returns = 0
        self.branches = 0
        self.args = len(node.args.args)
        self.nesting_level = 0
        self.line_start = node.lineno

    def _exit_function(self, node):
        if self.current_function:
            # Store metrics
            metric = ComplexityMetrics(
                function_name=self.current_function,
                cyclomatic=self.complexity,
                cognitive=self.cognitive,
                loc=self.loc,
                args_count=self.args,
                returns_count=self.returns,
                nesting_depth=self.nesting_level,
                branch_count=self.branches,
            )
            self.metrics.append(metric)

            # Store graph node
            graph_node = CodeGraphNode(
                id=f"{self.file_path}::{self.current_function}",
                type="function",
                name=self.current_function,
                file_path=self.file_path,
                line_start=self.line_start,
                line_end=node.end_lineno or self.line_start,
                complexity=self.complexity,
                metadata={"cognitive": self.cognitive, "loc": self.loc},
            )
            self.nodes.append(graph_node)

            self.current_function = None

    # Cyclomatic Complexity
    def visit_If(self, node):
        self.complexity += 1
        self.branches += 1
        self.nesting_level += 1
        self.cognitive += self.nesting_level  # Cognitive: deeper = harder
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_For(self, node):
        self.complexity += 1
        self.nesting_level += 1
        self.cognitive += self.nesting_level
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_While(self, node):
        self.complexity += 1
        self.nesting_level += 1
        self.cognitive += self.nesting_level
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_Try(self, node):
        self.complexity += len(node.handlers)
        self.cognitive += len(node.handlers)
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds complexity
        self.complexity += len(node.values) - 1
        self.cognitive += 1
        self.generic_visit(node)

    def visit_Return(self, node):
        self.returns += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        """Track function calls for dependency graph."""
        called_name = None
        if isinstance(node.func, ast.Name):
            called_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr

        if called_name:
            self.function_calls.append((called_name, node.lineno))
            # Track which function made this call
            if self.current_function:
                if self.current_function not in self.calls_per_function:
                    self.calls_per_function[self.current_function] = []
                self.calls_per_function[self.current_function].append((called_name, node.lineno))

        self.generic_visit(node)


__all__ = ["CodeGraphAnalyzer"]
