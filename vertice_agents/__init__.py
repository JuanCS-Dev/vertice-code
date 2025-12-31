"""
VERTICE Agents - Unified Agent Registry.

This module provides a single point of access to all VERTICE agents,
unifying the Core agents (agents/) and CLI agents (vertice_cli/agents/).

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                  vertice_agents                          │
    │                                                          │
    │   AgentRegistry (Singleton)                              │
    │   ├── Core Agents (6)    ← agents/                      │
    │   │   ├── OrchestratorAgent                             │
    │   │   ├── CoderAgent                                    │
    │   │   ├── ReviewerAgent                                 │
    │   │   ├── ArchitectAgent                                │
    │   │   ├── ResearcherAgent                               │
    │   │   └── DevOpsAgent                                   │
    │   │                                                      │
    │   └── CLI Agents (17+)   ← vertice_cli/agents/          │
    │       ├── ArchitectAgent (CLI)                          │
    │       ├── ExplorerAgent                                 │
    │       ├── PlannerAgent                                  │
    │       ├── RefactorerAgent                               │
    │       ├── ReviewerAgent (CLI)                           │
    │       ├── TesterAgent                                   │
    │       ├── SecurityAgent                                 │
    │       ├── JusticaAgent                                  │
    │       ├── SofiaAgent                                    │
    │       └── ... (more)                                    │
    └─────────────────────────────────────────────────────────┘

Usage:
    from vertice_agents import AgentRegistry, get_agent

    # Get registry singleton
    registry = AgentRegistry.instance()

    # Get an agent by name
    planner = registry.get("planner")

    # Or use convenience function
    coder = get_agent("coder")

Author: JuanCS Dev
Date: 2025-12-31
Soli Deo Gloria
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Juan Carlos de Souza"

from .registry import AgentRegistry, get_agent, list_agents

__all__ = [
    "AgentRegistry",
    "get_agent",
    "list_agents",
    "__version__",
]
