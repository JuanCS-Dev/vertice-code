"""
Compatibility shim for `vertice_agents.registry`.

Re-exports the unified registry from `vertice_core.agents.registry`.
"""

from __future__ import annotations

from vertice_core.agents.registry import (
    AgentInfo,
    AgentRegistry,
    AgentSource,
    get_agent,
    list_agents,
)

__all__ = [
    "AgentInfo",
    "AgentRegistry",
    "AgentSource",
    "get_agent",
    "list_agents",
]
