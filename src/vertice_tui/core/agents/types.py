"""
Agent Types - Data structures for agent system.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_core.simple_agents import Agent


@dataclass
class AgentInfo:
    """Metadata about an agent.

    Attributes:
        name: Agent identifier
        role: Agent role/type
        description: What the agent does
        capabilities: List of capability strings
        module_path: Python module path for import
        class_name: Class name to instantiate
        is_core: Whether this is a core agent (from agents/)
    """

    name: str
    role: str
    description: str
    capabilities: List[str]
    module_path: str
    class_name: str
    is_core: bool = False

    def to_unified_agent(self) -> "Agent":
        """Convert to unified Agent instance.

        Creates a lightweight Agent wrapper for schema generation.
        """
        from vertice_core.simple_agents import Agent, AgentConfig

        return Agent(
            name=self.name,
            instructions=self.description,
            tools=[],
            config=AgentConfig(enable_tracing=True),
        )
