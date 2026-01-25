"""
Compatibility package: `vertice_agents`.

This repo consolidated agent orchestration under `vertice_core.agents` while keeping
`vertice_agents.*` imports working for legacy code, tests, and documentation.
"""

from __future__ import annotations

from vertice_core.agents.coordinator import (
    AgencyCoordinator,
    CoordinationDecision,
    CoordinationResult,
    OrchestratorType,
    TaskCategory,
    get_coordinator,
)
from vertice_core.agents.registry import AgentRegistry, get_agent, list_agents

__all__ = [
    # Registry
    "AgentRegistry",
    "get_agent",
    "list_agents",
    # Coordinator
    "AgencyCoordinator",
    "OrchestratorType",
    "TaskCategory",
    "CoordinationDecision",
    "CoordinationResult",
    "get_coordinator",
]
