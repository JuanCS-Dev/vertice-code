"""
DEVSQUAD: Federation of Specialists - Agent Foundation

This module provides the base abstractions for the multi-agent system where
specialized AI agents collaborate to solve complex development tasks.

Architecture:
    - BaseAgent: Abstract base class for all specialist agents
    - AgentRole: Enum defining specialist roles (Architect, Explorer, etc.)
    - AgentCapability: Enum defining what tools each agent can use
    - AgentTask: Pydantic model for task definition
    - AgentResponse: Pydantic model for agent output

Philosophy (Boris Cherny):
    "Each agent is a specialist, not a generalist."
    - Strict capability enforcement
    - Type-safe communication
    - Zero placeholders
    - Production-ready code only
"""

from vertice_cli.agents.base import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
)
from vertice_cli.agents.architect import ArchitectAgent
from vertice_cli.agents.explorer import ExplorerAgent
from vertice_cli.agents.planner import PlannerAgent
from vertice_cli.agents.refactorer import RefactorerAgent
from vertice_cli.agents.reviewer import ReviewerAgent
from vertice_cli.agents.security import SecurityAgent
from vertice_cli.agents.performance import PerformanceAgent
from vertice_cli.agents.testing import TestingAgent
from vertice_cli.agents.executor import NextGenExecutorAgent

# Alias for backward compatibility with tests
ExecutorAgent = NextGenExecutorAgent
from vertice_cli.agents.documentation import DocumentationAgent

__all__ = [
    "AgentCapability",
    "AgentRole",
    "AgentTask",
    "AgentResponse",
    "BaseAgent",
    "ArchitectAgent",
    "ExplorerAgent",
    "PlannerAgent",
    "RefactorerAgent",
    "ReviewerAgent",
    "SecurityAgent",
    "PerformanceAgent",
    "TestingAgent",
    "NextGenExecutorAgent",
    "ExecutorAgent",  # Alias for backward compatibility
    "DocumentationAgent",
]
