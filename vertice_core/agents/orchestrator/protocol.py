"""
AgentProtocol - Interface that agents must implement.

Defines the protocol for agents that can be orchestrated.
"""

from typing import AsyncIterator, Protocol

from vertice_core.agents.context import UnifiedContext


class AgentProtocol(Protocol):
    """Protocol that agents must implement."""

    async def execute(
        self,
        request: str,
        context: UnifiedContext,
    ) -> AsyncIterator[str]:
        """Execute agent task, yielding progress."""
        ...
