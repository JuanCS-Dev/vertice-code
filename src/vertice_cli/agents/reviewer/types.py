"""
Reviewer Data Models.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Contains:
- IssueSeverity, IssueCategory (enums)
- CodeGraphNode, ComplexityMetrics (analysis)
- CodeIssue, RAGContext, ReviewReport (reporting)

Author: Vertice Team
Date: 2026-01-02
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # Security, data loss, crashes
    HIGH = "HIGH"  # Logic bugs, performance issues
    MEDIUM = "MEDIUM"  # Code smell, maintainability
    LOW = "LOW"  # Style, minor improvements
    INFO = "INFO"  # Suggestions, best practices


class IssueCategory(str, Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    LOGIC = "LOGIC"
    COMPLEXITY = "COMPLEXITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    TESTING = "TESTING"
    DOCUMENTATION = "DOCUMENTATION"
    STYLE = "STYLE"
    ARCHITECTURE = "ARCHITECTURE"


# ============================================================================
# GRAPH NODES
# ============================================================================


@dataclass
class CodeGraphNode:
    """Represents a node in the code graph (function, class, module)."""

    id: str
    type: str  # function, class, method, module
    name: str
    file_path: str
    line_start: int
    line_end: int
    complexity: int = 0
    dependencies: Set[str] = field(default_factory=set)
    used_by: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# METRICS
# ============================================================================


class ComplexityMetrics(BaseModel):
    """Enhanced complexity metrics."""

    function_name: str
    cyclomatic: int  # McCabe
    cognitive: int  # How hard to understand
    halstead_difficulty: float = 0.0
    loc: int
    args_count: int
    returns_count: int
    nesting_depth: int = 0
    branch_count: int = 0


# ============================================================================
# ISSUES & REPORTS
# ============================================================================


class CodeIssue(BaseModel):
    """Enhanced issue reporting."""

    file: str
    line: int
    end_line: Optional[int] = None
    severity: IssueSeverity
    category: IssueCategory
    message: str
    explanation: str  # Why it's an issue
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False
    related_issues: List[str] = Field(default_factory=list)
    confidence: float = 1.0  # 0-1, how sure we are


class RAGContext(BaseModel):
    """Context retrieved from codebase."""

    related_functions: List[str] = Field(default_factory=list)
    similar_patterns: List[str] = Field(default_factory=list)
    team_standards: Dict[str, str] = Field(default_factory=dict)
    historical_issues: List[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    """Comprehensive review report."""

    approved: bool
    score: int  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    metrics: List[ComplexityMetrics]
    issues: List[CodeIssue]
    rag_context: RAGContext
    summary: str
    recommendations: List[str] = Field(default_factory=list)
    estimated_fix_time: str = "Unknown"
    requires_human_review: bool = False


__all__ = [
    "IssueSeverity",
    "IssueCategory",
    "CodeGraphNode",
    "ComplexityMetrics",
    "CodeIssue",
    "RAGContext",
    "ReviewReport",
]
