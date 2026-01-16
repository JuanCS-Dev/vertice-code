"""
Agents Bridge - Backward Compatibility Shim.

DEPRECATED: Use tui.core.agents module directly.

This module re-exports from the new agents/ package for
backward compatibility. All functionality has been moved to:

- tui.core.agents.types      → AgentInfo
- tui.core.agents.registry   → AGENT_REGISTRY
- tui.core.agents.router     → AgentRouter
- tui.core.agents.manager    → AgentManager
- tui.core.agents.streaming  → normalize_streaming_chunk

Migration:
    # Old:
    from vertice_tui.core.agents_bridge import AgentManager, AGENT_REGISTRY

    # New:
    from vertice_tui.core.agents import AgentManager, AGENT_REGISTRY
"""

from __future__ import annotations

import warnings

# Re-export everything from the new module
from .agents import (
    AgentInfo,
    AGENT_REGISTRY,
    AgentRouter,
    AgentManager,
    get_unified_agents,
    get_core_agents,
)

# Re-export unified Agent system
from vertice_core.simple_agents import Agent, AgentConfig, Handoff

# Emit deprecation warning on import
warnings.warn(
    "tui.core.agents_bridge is deprecated. Use tui.core.agents instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AgentInfo",
    "AGENT_REGISTRY",
    "AgentRouter",
    "AgentManager",
    # Unified Agent integration
    "Agent",
    "AgentConfig",
    "Handoff",
    "get_unified_agents",
    "get_core_agents",
]
