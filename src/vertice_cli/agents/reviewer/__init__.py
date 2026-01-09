"""
Reviewer Module.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Modular reviewer agent extracted from monolithic reviewer.py (1,279 lines).

Structure:
- types.py: Data models (enums, dataclasses, pydantic models)
- graph_analyzer.py: CodeGraphAnalyzer (AST analysis)
- rag_engine.py: RAGContextEngine (context retrieval)
- security_agent.py: SecurityAgent (security analysis)
- sub_agents.py: PerformanceAgent, TestCoverageAgent, CodeGraphAnalysisAgent
- agent.py: ReviewerAgent (main orchestrator)

Author: Vertice Team
Date: 2026-01-02
"""

# Types
from .types import (
    IssueSeverity,
    IssueCategory,
    CodeGraphNode,
    ComplexityMetrics,
    CodeIssue,
    RAGContext,
    ReviewReport,
)

# Analyzers
from .graph_analyzer import CodeGraphAnalyzer
from .rag_engine import RAGContextEngine
from .security_agent import SecurityAgent

# Sub-agents
from .sub_agents import (
    PerformanceAgent,
    TestCoverageAgent,
    CodeGraphAnalysisAgent,
)

# Main agent
from .agent import ReviewerAgent

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
]
