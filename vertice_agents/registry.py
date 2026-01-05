"""
Agent Registry - Unified Access Point for All VERTICE Agents.

This registry provides:
1. Lazy loading of agents (imports on first access)
2. Singleton pattern (one registry per process)
3. Clear separation between Core and CLI agents
4. Error handling with graceful fallbacks

Design Principles:
    - Non-invasive: Does NOT modify existing agent files
    - Safe: Lazy imports prevent circular dependencies
    - Clear: Explicit naming avoids confusion

Author: JuanCS Dev
Date: 2025-12-31
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class AgentSource(Enum):
    """Source of the agent."""
    CORE = auto()      # agents/ directory
    CLI = auto()       # vertice_cli/agents/ directory
    GOVERNANCE = auto()  # vertice_governance/


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    source: AgentSource
    module_path: str
    class_name: str
    description: str = ""
    _instance: Any = field(default=None, repr=False)
    _class: Any = field(default=None, repr=False)


class AgentRegistry:
    """
    Singleton registry for all VERTICE agents.

    This is the central point of access for all agents in the system.
    Agents are lazily loaded to avoid import-time issues.

    Usage:
        registry = AgentRegistry.instance()

        # Get agent class
        PlannerClass = registry.get_class("planner")

        # Get or create agent instance
        planner = registry.get("planner")

        # List available agents
        for name, info in registry.list_agents():
            print(f"{name}: {info.description}")
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the registry with known agents."""
        self._agents: Dict[str, AgentInfo] = {}
        self._initialized = False

    @classmethod
    def instance(cls) -> "AgentRegistry":
        """Get the singleton registry instance (thread-safe).

        Uses double-checked locking for performance.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check inside lock
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance._register_known_agents()
        return cls._instance

    def _register_known_agents(self) -> None:
        """Register all known agents from both systems."""
        if self._initialized:
            return

        # =================================================================
        # CORE AGENTS (agents/)
        # =================================================================
        core_agents = [
            AgentInfo(
                name="orchestrator",
                source=AgentSource.CORE,
                module_path="agents.orchestrator",
                class_name="OrchestratorAgent",
                description="Bounded autonomy orchestrator (L0-L3 levels)",
            ),
            AgentInfo(
                name="coder",
                source=AgentSource.CORE,
                module_path="agents.coder",
                class_name="CoderAgent",
                description="Code generation with Darwin-Godel reasoning",
            ),
            AgentInfo(
                name="reviewer_core",
                source=AgentSource.CORE,
                module_path="agents.reviewer",
                class_name="ReviewerAgent",
                description="Deep think code review",
            ),
            AgentInfo(
                name="architect_core",
                source=AgentSource.CORE,
                module_path="agents.architect",
                class_name="ArchitectAgent",
                description="Three loops architectural analysis",
            ),
            AgentInfo(
                name="researcher",
                source=AgentSource.CORE,
                module_path="agents.researcher",
                class_name="ResearcherAgent",
                description="Agentic RAG research",
            ),
            AgentInfo(
                name="devops",
                source=AgentSource.CORE,
                module_path="agents.devops",
                class_name="DevOpsAgent",
                description="DevOps and incident handling",
            ),
        ]

        # =================================================================
        # CLI AGENTS (vertice_cli/agents/)
        # =================================================================
        cli_agents = [
            AgentInfo(
                name="architect",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.architect",
                class_name="ArchitectAgent",
                description="DevSquad viability gate",
            ),
            AgentInfo(
                name="explorer",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.explorer",
                class_name="ExplorerAgent",
                description="Context collection and codebase exploration",
            ),
            AgentInfo(
                name="planner",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.planner",
                class_name="PlannerAgent",
                description="GOAP-based execution planning",
            ),
            AgentInfo(
                name="refactorer",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.refactorer",
                class_name="RefactorerAgent",
                description="Transactional code refactoring",
            ),
            AgentInfo(
                name="reviewer",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.reviewer",
                class_name="ReviewerAgent",
                description="Quality review and grading",
            ),
            AgentInfo(
                name="executor",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.executor",
                class_name="ExecutorAgent",
                description="Safe code execution",
            ),
            AgentInfo(
                name="tester",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.testing",
                class_name="TestingAgent",
                description="Test generation and execution",
            ),
            AgentInfo(
                name="security",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.security",
                class_name="SecurityAgent",
                description="Security vulnerability analysis",
            ),
            AgentInfo(
                name="documentation",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.documentation",
                class_name="DocumentationAgent",
                description="Documentation generation",
            ),
            AgentInfo(
                name="performance",
                source=AgentSource.CLI,
                module_path="vertice_cli.agents.performance",
                class_name="PerformanceAgent",
                description="Performance optimization",
            ),
        ]

        # =================================================================
        # GOVERNANCE AGENTS (vertice_governance/)
        # =================================================================
        governance_agents = [
            AgentInfo(
                name="justica",
                source=AgentSource.GOVERNANCE,
                module_path="vertice_cli.agents.justica_agent",
                class_name="JusticaAgent",
                description="JUSTICA 5 Principles evaluation",
            ),
            AgentInfo(
                name="sofia",
                source=AgentSource.GOVERNANCE,
                module_path="vertice_cli.agents.sofia_agent",
                class_name="SofiaAgent",
                description="SOFIA 7 Dimensions analysis",
            ),
        ]

        # Register all agents
        for agent in core_agents + cli_agents + governance_agents:
            self._agents[agent.name] = agent

        self._initialized = True
        logger.debug(f"Registered {len(self._agents)} agents")

    def get_class(self, name: str) -> Optional[Type]:
        """
        Get agent class by name (lazy import).

        Args:
            name: Agent name (e.g., "planner", "coder")

        Returns:
            Agent class or None if not found
        """
        info = self._agents.get(name)
        if info is None:
            logger.warning(f"Agent not found: {name}")
            return None

        # Return cached class if available
        if info._class is not None:
            return info._class

        # Lazy import
        try:
            import importlib
            module = importlib.import_module(info.module_path)
            info._class = getattr(module, info.class_name)
            return info._class
        except Exception as e:
            logger.error(f"Failed to import agent {name}: {e}")
            return None

    def get(self, name: str, **kwargs: Any) -> Optional[Any]:
        """
        Get or create agent instance by name.

        Args:
            name: Agent name
            **kwargs: Arguments passed to agent constructor

        Returns:
            Agent instance or None if not found
        """
        info = self._agents.get(name)
        if info is None:
            return None

        # Return cached instance if no kwargs and instance exists
        if not kwargs and info._instance is not None:
            return info._instance

        # Create new instance
        agent_class = self.get_class(name)
        if agent_class is None:
            return None

        try:
            instance = agent_class(**kwargs)
            # Cache if no kwargs
            if not kwargs:
                info._instance = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            return None

    def list_agents(
        self,
        source: Optional[AgentSource] = None
    ) -> List[tuple[str, AgentInfo]]:
        """
        List registered agents.

        Args:
            source: Filter by source (CORE, CLI, GOVERNANCE)

        Returns:
            List of (name, AgentInfo) tuples
        """
        if source is None:
            return list(self._agents.items())
        return [
            (name, info)
            for name, info in self._agents.items()
            if info.source == source
        ]

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents

    def get_info(self, name: str) -> Optional[AgentInfo]:
        """Get agent info without loading the agent."""
        return self._agents.get(name)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_agent(name: str, **kwargs: Any) -> Optional[Any]:
    """
    Get agent instance by name.

    This is the recommended way to access agents:

        from vertice_agents import get_agent

        planner = get_agent("planner")
        result = await planner.execute(task)
    """
    return AgentRegistry.instance().get(name, **kwargs)


def list_agents(source: Optional[AgentSource] = None) -> List[tuple[str, AgentInfo]]:
    """List all registered agents."""
    return AgentRegistry.instance().list_agents(source)
