"""
Schemas Module - Pydantic Schemas for Structured Agent Outputs.

Following Claude Code 2026 pattern: strict JSON schemas with additionalProperties: false.

Author: Vertice Framework
Date: 2026-01-01
"""

from .agent_outputs import (
    ReviewDecision,
    CodeIssue,
    ReviewOutput,
    TestOutput,
    ArchitectOutput,
    ExplorerOutput,
    DocumentationOutput,
    AgentOutputBase,
)

__all__ = [
    "ReviewDecision",
    "CodeIssue",
    "ReviewOutput",
    "TestOutput",
    "ArchitectOutput",
    "ExplorerOutput",
    "DocumentationOutput",
    "AgentOutputBase",
]
