"""
Agents Module - Agent Registry, Router, and Manager.

Semantic extraction from agents_bridge.py for CODE_CONSTITUTION compliance.

Components:
- types.py: AgentInfo dataclass
- registry.py: AGENT_REGISTRY with 20 agents
- router.py: AgentRouter for intent-based routing
- manager.py: AgentManager for lifecycle management
- streaming.py: Streaming chunk normalization

Following CODE_CONSTITUTION: <500 lines per file, 100% type hints
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from .types import AgentInfo
from .registry import AGENT_REGISTRY
from .router import AgentRouter
from .manager import AgentManager
from .streaming import normalize_streaming_chunk
from .core_adapter import CoreAgentAdapter, CoreAgentContext
from .orchestrator_integration import OrchestratorIntegration, OrchestrationContext

if TYPE_CHECKING:
    from core.agents import Agent


def get_unified_agents() -> Dict[str, "Agent"]:
    """Get all agents as unified Agent instances.

    Returns:
        Dictionary mapping agent names to Agent instances
    """
    return {
        name: info.to_unified_agent()
        for name, info in AGENT_REGISTRY.items()
    }


def get_core_agents() -> Dict[str, AgentInfo]:
    """Get only core agents (from agents/).

    Returns:
        Dictionary of core agent info
    """
    return {
        name: info
        for name, info in AGENT_REGISTRY.items()
        if info.is_core
    }


__all__ = [
    # Core types
    "AgentInfo",
    "AGENT_REGISTRY",
    "AgentRouter",
    "AgentManager",
    # Core agent integration
    "CoreAgentAdapter",
    "CoreAgentContext",
    "OrchestratorIntegration",
    "OrchestrationContext",
    # Utilities
    "normalize_streaming_chunk",
    "get_unified_agents",
    "get_core_agents",
]
