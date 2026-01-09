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
from vertice_cli.agents.refactorer import RefactorerAgent, create_refactorer_agent
from vertice_cli.agents.reviewer import ReviewerAgent
from vertice_cli.agents.security import SecurityAgent
from vertice_cli.agents.performance import PerformanceAgent
from vertice_cli.agents.testing import TestRunnerAgent, create_testing_agent
from vertice_cli.agents.executor import NextGenExecutorAgent
from vertice_cli.agents.documentation import DocumentationAgent, create_documentation_agent
from vertice_cli.agents.devops import DevOpsAgent, create_devops_agent
from vertice_cli.agents.justica_agent import JusticaIntegratedAgent
from vertice_cli.agents.sofia import SofiaIntegratedAgent, create_sofia_agent
from vertice_cli.agents.data_agent_production import DataAgent
from vertice_cli.agents.deep_research import VertexDeepResearchAgent

# Aliases for backward compatibility
ExecutorAgent = NextGenExecutorAgent
JusticaAgent = JusticaIntegratedAgent
SofiaAgent = SofiaIntegratedAgent
# Note: PrometheusAgent available via vertice_agents.registry.get("prometheus")

__all__ = [
    # Base types
    "AgentCapability",
    "AgentRole",
    "AgentTask",
    "AgentResponse",
    "BaseAgent",
    # CLI Agents (14)
    "ArchitectAgent",
    "ExplorerAgent",
    "PlannerAgent",
    "RefactorerAgent",
    "create_refactorer_agent",
    "ReviewerAgent",
    "SecurityAgent",
    "PerformanceAgent",
    "TestRunnerAgent",
    "create_testing_agent",
    "NextGenExecutorAgent",
    "ExecutorAgent",  # Alias
    "DocumentationAgent",
    "create_documentation_agent",
    "DevOpsAgent",
    "create_devops_agent",
    "JusticaIntegratedAgent",
    "JusticaAgent",  # Alias
    "SofiaIntegratedAgent",
    "SofiaAgent",  # Alias
    "create_sofia_agent",
    "DataAgent",
    "VertexDeepResearchAgent",
    # Note: PrometheusAgent available via vertice_agents.registry.get("prometheus")
]
