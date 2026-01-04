"""
Agent Outputs - Pydantic Schemas for Structured Agent Responses.

Following Claude Code 2026 pattern:
- strict: true (extra="forbid")
- additionalProperties: false
- Required grounding fields (code_analyzed)

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# BASE SCHEMA
# =============================================================================


class AgentOutputBase(BaseModel):
    """Base schema for all agent outputs.

    All agent outputs should include:
    - success: Whether the operation succeeded
    - code_analyzed: Quote of code that was analyzed (for grounding)
    - reasoning: Step-by-step explanation
    """

    success: bool = Field(description="Whether the operation succeeded")
    code_analyzed: Optional[str] = Field(
        default=None, description="Quote of code that was analyzed (for grounding)"
    )
    reasoning: Optional[str] = Field(default=None, description="Step-by-step reasoning explanation")

    class Config:
        extra = "forbid"  # strict: true equivalent


# =============================================================================
# REVIEWER AGENT SCHEMAS
# =============================================================================


class ReviewDecision(str, Enum):
    """Possible review decisions."""

    APPROVED = "APPROVED"
    NEEDS_CHANGES = "NEEDS_CHANGES"
    REJECTED = "REJECTED"


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CodeIssue(BaseModel):
    """A single code issue found during review."""

    line: int = Field(ge=1, description="Line number where issue occurs")
    severity: Severity = Field(description="Issue severity level")
    message: str = Field(min_length=5, description="Description of the issue")
    code_quote: str = Field(min_length=1, description="Exact quote from the code (for grounding)")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix for the issue")

    class Config:
        extra = "forbid"


class ReviewOutput(AgentOutputBase):
    """Output schema for ReviewerAgent.

    Example:
        {
            "success": true,
            "decision": "NEEDS_CHANGES",
            "issues": [
                {
                    "line": 42,
                    "severity": "high",
                    "message": "SQL injection vulnerability",
                    "code_quote": "cursor.execute(f\"SELECT * FROM {table}\")",
                    "suggestion": "Use parameterized queries"
                }
            ],
            "summary": "Found 1 critical security issue",
            "code_analyzed": "def query_table(table): ..."
        }
    """

    decision: ReviewDecision = Field(description="Overall review decision")
    issues: List[CodeIssue] = Field(default_factory=list, description="List of issues found")
    summary: str = Field(description="Summary of the review")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Optional code metrics")

    @field_validator("issues")
    @classmethod
    def validate_issues(cls, v: List[CodeIssue], info) -> List[CodeIssue]:
        """Ensure issues have code_quote for grounding."""
        for issue in v:
            if not issue.code_quote:
                raise ValueError("Each issue must have code_quote for grounding")
        return v


# =============================================================================
# TESTING AGENT SCHEMAS
# =============================================================================


class TestCase(BaseModel):
    """A generated test case."""

    name: str = Field(min_length=3, description="Test function name")
    description: str = Field(description="What the test verifies")
    code: str = Field(min_length=10, description="Test code")
    test_type: str = Field(default="unit", description="Type: unit, integration, e2e")

    class Config:
        extra = "forbid"


class TestOutput(AgentOutputBase):
    """Output schema for TestingAgent.

    Example:
        {
            "success": true,
            "tests": [
                {
                    "name": "test_calculate_sum",
                    "description": "Verify sum returns correct result",
                    "code": "def test_calculate_sum(): assert sum([1,2]) == 3",
                    "test_type": "unit"
                }
            ],
            "coverage_estimate": 85.5,
            "code_analyzed": "def calculate_sum(numbers): ..."
        }
    """

    tests: List[TestCase] = Field(default_factory=list, description="Generated test cases")
    coverage_estimate: float = Field(
        ge=0, le=100, default=0, description="Estimated code coverage percentage"
    )
    test_framework: str = Field(default="pytest", description="Testing framework used")


# =============================================================================
# ARCHITECT AGENT SCHEMAS
# =============================================================================


class ArchitectDecision(str, Enum):
    """Architect decision types."""

    APPROVED = "APPROVED"
    VETOED = "VETOED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ArchitectOutput(AgentOutputBase):
    """Output schema for ArchitectAgent.

    Example:
        {
            "success": true,
            "decision": "APPROVED",
            "approach": "Use dependency injection for loose coupling",
            "risks": ["Increased complexity", "Learning curve"],
            "trade_offs": {
                "pros": ["Testability", "Flexibility"],
                "cons": ["Boilerplate code"]
            },
            "code_analyzed": "class UserService: ..."
        }
    """

    decision: ArchitectDecision = Field(description="Architect's decision")
    approach: str = Field(description="Recommended approach")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    trade_offs: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Pros and cons of the approach"
    )
    alternatives: Optional[List[str]] = Field(
        default=None, description="Alternative approaches considered"
    )


# =============================================================================
# EXPLORER AGENT SCHEMAS
# =============================================================================


class FileResult(BaseModel):
    """A file found during exploration."""

    path: str = Field(description="Relative file path")
    relevance: str = Field(default="MEDIUM", description="Relevance: HIGH, MEDIUM, LOW")
    reason: str = Field(description="Why this file is relevant")
    snippet: Optional[str] = Field(default=None, description="Content snippet for grounding")
    size: Optional[int] = Field(default=None, description="File size in bytes")

    class Config:
        extra = "forbid"


class ExplorerOutput(AgentOutputBase):
    """Output schema for ExplorerAgent.

    Example:
        {
            "success": true,
            "relevant_files": [
                {
                    "path": "vertice_cli/agents/base.py",
                    "relevance": "HIGH",
                    "reason": "Base agent class definition",
                    "snippet": "class BaseAgent: ..."
                }
            ],
            "context_summary": "Found 5 relevant files",
            "token_estimate": 1000
        }
    """

    relevant_files: List[FileResult] = Field(
        default_factory=list, description="List of relevant files found"
    )
    context_summary: str = Field(default="", description="Summary of exploration results")
    token_estimate: int = Field(default=0, description="Estimated tokens for all content")


# =============================================================================
# DOCUMENTATION AGENT SCHEMAS
# =============================================================================


class DocumentedItem(BaseModel):
    """A documented code item (function, class, etc.)."""

    name: str = Field(description="Item name")
    item_type: str = Field(description="Type: function, class, module")
    docstring: Optional[str] = Field(default=None, description="Generated docstring")
    signature: Optional[str] = Field(default=None, description="Function/method signature")

    class Config:
        extra = "forbid"


class DocumentationOutput(AgentOutputBase):
    """Output schema for DocumentationAgent.

    Example:
        {
            "success": true,
            "documentation": "# Module docs...",
            "items_documented": [
                {
                    "name": "calculate_sum",
                    "item_type": "function",
                    "docstring": "Calculate sum of numbers...",
                    "signature": "def calculate_sum(numbers: List[int]) -> int"
                }
            ],
            "code_analyzed": "def calculate_sum(numbers): ..."
        }
    """

    documentation: str = Field(description="Generated documentation text")
    items_documented: List[DocumentedItem] = Field(
        default_factory=list, description="List of documented items"
    )
    format: str = Field(default="markdown", description="Documentation format: markdown, rst, html")
    style: str = Field(default="google", description="Docstring style: google, numpy, sphinx")


# =============================================================================
# CODER AGENT SCHEMAS
# =============================================================================


class CodeChange(BaseModel):
    """A code change/implementation."""

    file_path: str = Field(description="File to modify/create")
    action: str = Field(description="Action: create, modify, delete")
    code: str = Field(description="New/modified code")
    description: str = Field(description="What this change does")

    class Config:
        extra = "forbid"


class CoderOutput(AgentOutputBase):
    """Output schema for CoderAgent.

    Example:
        {
            "success": true,
            "changes": [
                {
                    "file_path": "utils/helper.py",
                    "action": "create",
                    "code": "def helper(): pass",
                    "description": "Add helper function"
                }
            ],
            "summary": "Created 1 new file",
            "code_analyzed": "Existing codebase structure..."
        }
    """

    changes: List[CodeChange] = Field(default_factory=list, description="List of code changes")
    summary: str = Field(description="Summary of changes made")
    tests_to_run: Optional[List[str]] = Field(
        default=None, description="Tests to run to verify changes"
    )


# =============================================================================
# PLANNER AGENT SCHEMAS
# =============================================================================


class PlanStep(BaseModel):
    """A step in the execution plan."""

    step_number: int = Field(ge=1, description="Step sequence number")
    description: str = Field(description="What this step does")
    agent: str = Field(description="Which agent executes this step")
    dependencies: List[int] = Field(
        default_factory=list, description="Step numbers this depends on"
    )

    class Config:
        extra = "forbid"


class PlannerOutput(AgentOutputBase):
    """Output schema for PlannerAgent.

    Example:
        {
            "success": true,
            "plan": [
                {
                    "step_number": 1,
                    "description": "Analyze existing code",
                    "agent": "explorer",
                    "dependencies": []
                },
                {
                    "step_number": 2,
                    "description": "Implement feature",
                    "agent": "coder",
                    "dependencies": [1]
                }
            ],
            "estimated_steps": 3,
            "reasoning": "Breaking down the task..."
        }
    """

    plan: List[PlanStep] = Field(default_factory=list, description="Ordered list of plan steps")
    estimated_steps: int = Field(default=0, description="Total number of steps")
    estimated_agents: List[str] = Field(
        default_factory=list, description="Agents involved in the plan"
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base
    "AgentOutputBase",
    # Enums
    "ReviewDecision",
    "Severity",
    "ArchitectDecision",
    # Components
    "CodeIssue",
    "TestCase",
    "FileResult",
    "DocumentedItem",
    "CodeChange",
    "PlanStep",
    # Outputs
    "ReviewOutput",
    "TestOutput",
    "ArchitectOutput",
    "ExplorerOutput",
    "DocumentationOutput",
    "CoderOutput",
    "PlannerOutput",
]
