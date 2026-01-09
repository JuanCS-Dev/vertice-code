"""
ReviewerAgent v5.0: Enterprise-Grade Agentic Code Review System (2025)

SCALE & SUSTAIN Phase 3.1 - Backward Compatibility Shim.

This module re-exports from vertice_cli.agents.reviewer/ for backward compatibility.
All functionality has been extracted to semantic sub-modules:

- types.py: Data models (enums, dataclasses, pydantic models)
- graph_analyzer.py: CodeGraphAnalyzer (AST analysis)
- rag_engine.py: RAGContextEngine (context retrieval)
- security_agent.py: SecurityAgent (security analysis)
- sub_agents.py: PerformanceAgent, TestCoverageAgent, CodeGraphAnalysisAgent
- agent.py: ReviewerAgent (main orchestrator)

Usage (recommended):
    from vertice_cli.agents.reviewer import ReviewerAgent

Legacy usage (still works):
    from vertice_cli.agents.reviewer import ReviewerAgent

Author: Vertice Team
Date: 2026-01-02 (Phase 3.1 refactor)
"""

# Re-export everything from the modular package
from vertice_cli.agents.reviewer import (
    # Types
    IssueSeverity,
    IssueCategory,
    CodeGraphNode,
    ComplexityMetrics,
    CodeIssue,
    RAGContext,
    ReviewReport,
    # Analyzers
    CodeGraphAnalyzer,
    RAGContextEngine,
    SecurityAgent,
    # Sub-agents
    PerformanceAgent,
    TestCoverageAgent,
    CodeGraphAnalysisAgent,
    # Main
    ReviewerAgent,
)

# Preserve module-level constant
MAX_FILE_CHARS = 8000

__all__ = [
    # Types
    "IssueSeverity",
    "IssueCategory",
    "CodeGraphNode",
    "ComplexityMetrics",
    "CodeIssue",
    "RAGContext",
    "ReviewReport",
    # Analyzers
    "CodeGraphAnalyzer",
    "RAGContextEngine",
    "SecurityAgent",
    # Sub-agents
    "PerformanceAgent",
    "TestCoverageAgent",
    "CodeGraphAnalysisAgent",
    # Main
    "ReviewerAgent",
    # Constants
    "MAX_FILE_CHARS",
]
