"""
Vertice Agency - The Unified AI Orchestra

Main entrypoint for the Vertice multi-agent system.
Coordinates all agents, memory, and providers.

Usage:
    from core.agency import Agency
    agency = Agency()
    result = await agency.execute("Build a REST API")
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgencyConfig:
    """Agency configuration."""
    name: str = "Vertice"
    version: str = "2.0.0"
    config_path: Path = field(default_factory=lambda: Path(".vertice/config.yaml"))

    # Agent settings
    default_orchestrator: str = "orchestrator"
    parallel_execution: bool = True
    max_concurrent_agents: int = 5

    # Memory settings
    memory_path: Path = field(default_factory=lambda: Path.home() / ".vertice" / "cortex")
    enable_semantic_memory: bool = True

    # Provider settings
    prefer_free_tier: bool = True
    fallback_enabled: bool = True


class Agency:
    """
    Vertice Agency - The Unified AI Orchestra

    Coordinates:
    - Multi-agent orchestration (Orchestrator, Coder, Reviewer, etc.)
    - Memory Cortex (working, episodic, semantic)
    - Provider routing (free tier priority)
    - Contribution tracking

    Implements patterns from:
    - Anthropic Claude Agent SDK
    - Google ADK
    - OpenAI Agents SDK
    """

    def __init__(self, config: Optional[AgencyConfig] = None):
        self.config = config or AgencyConfig()
        self._initialized = False

        # Lazy-loaded components
        self._orchestrator = None
        self._agents: Dict[str, Any] = {}
        self._router = None
        self._cortex = None
        self._mcp_server = None
        self._agent_cards: Dict[str, Dict] = {}

    def _lazy_init(self):
        """Lazy initialize all components."""
        if self._initialized:
            return

        logger.info(f"Initializing {self.config.name} Agency v{self.config.version}")

        # Load agent cards
        self._load_agent_cards()

        # Initialize router
        try:
            from providers.vertice_router import get_router
            self._router = get_router()
            logger.info("Router initialized")
        except Exception as e:
            logger.warning(f"Router init failed: {e}")

        # Initialize cortex
        try:
            from memory.cortex import get_cortex
            self._cortex = get_cortex()
            logger.info("Memory Cortex initialized")
        except Exception as e:
            logger.warning(f"Cortex init failed: {e}")

        # Initialize agents
        try:
            from agents import (
                orchestrator, coder, reviewer,
                architect, researcher, devops
            )
            self._orchestrator = orchestrator
            self._agents = {
                "orchestrator": orchestrator,
                "coder": coder,
                "reviewer": reviewer,
                "architect": architect,
                "researcher": researcher,
                "devops": devops,
            }
            logger.info(f"Agents initialized: {list(self._agents.keys())}")
        except Exception as e:
            logger.warning(f"Agents init failed: {e}")

        self._initialized = True

    def _load_agent_cards(self):
        """Load agent cards for A2A discovery."""
        cards_path = Path(".vertice/mesh/agent_cards")
        if not cards_path.exists():
            return

        for card_file in cards_path.glob("*.json"):
            try:
                with open(card_file) as f:
                    card = json.load(f)
                    self._agent_cards[card["agent_id"]] = card
            except Exception as e:
                logger.warning(f"Failed to load agent card {card_file}: {e}")

        logger.info(f"Loaded {len(self._agent_cards)} agent cards")

    async def execute(
        self,
        request: str,
        agent: Optional[str] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute a request through the agency.

        Args:
            request: User request
            agent: Specific agent to use (or auto-route)
            stream: Whether to stream output

        Yields:
            Execution output
        """
        self._lazy_init()

        yield f"[Agency] Processing: {request[:50]}...\n"

        # Record in episodic memory
        if self._cortex:
            self._cortex.remember(
                content=request,
                memory_type="episodic",
                event_type="user_request",
            )

        # Route to agent
        if agent and agent in self._agents:
            target = self._agents[agent]
        else:
            # Use orchestrator for routing
            target = self._orchestrator

        # Execute
        try:
            async for chunk in target.execute(request, stream=stream):
                yield chunk
        except Exception as e:
            yield f"[Agency] Error: {str(e)}\n"
            logger.error(f"Execution failed: {e}")

    async def delegate(
        self,
        task: str,
        to_agent: str,
        context: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Delegate a task to a specific agent.

        Args:
            task: Task to perform
            to_agent: Target agent
            context: Additional context

        Yields:
            Agent output
        """
        self._lazy_init()

        if to_agent not in self._agents:
            yield f"[Agency] Error: Unknown agent '{to_agent}'\n"
            return

        agent = self._agents[to_agent]
        yield f"[Agency] Delegating to {to_agent}...\n"

        async for chunk in agent.execute(task, stream=True):
            yield chunk

    def get_agent_card(self, agent_id: str) -> Optional[Dict]:
        """Get agent card for A2A discovery."""
        self._lazy_init()
        return self._agent_cards.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        self._lazy_init()

        agents = []
        for agent_id, card in self._agent_cards.items():
            agents.append({
                "id": agent_id,
                "name": card.get("name"),
                "description": card.get("description"),
                "provider": card.get("provider"),
                "capabilities": card.get("capabilities", []),
            })

        return agents

    def get_status(self) -> Dict:
        """Get agency status."""
        self._lazy_init()

        return {
            "name": self.config.name,
            "version": self.config.version,
            "initialized": self._initialized,
            "agents": list(self._agents.keys()),
            "agent_cards": len(self._agent_cards),
            "router_available": self._router is not None,
            "cortex_available": self._cortex is not None,
            "router_status": self._router.get_status_report() if self._router else "Not initialized",
            "cortex_status": self._cortex.get_status() if self._cortex else "Not initialized",
        }

    def get_router(self):
        """Get the provider router."""
        self._lazy_init()
        return self._router

    def get_cortex(self):
        """Get the memory cortex."""
        self._lazy_init()
        return self._cortex


# Global agency instance
_agency: Optional[Agency] = None


def get_agency() -> Agency:
    """Get the global agency instance."""
    global _agency
    if _agency is None:
        _agency = Agency()
    return _agency


# CLI helper
async def main():
    """Quick test of the agency."""
    agency = get_agency()

    print("Vertice Agency Status:")
    print(json.dumps(agency.get_status(), indent=2))

    print("\nAvailable Agents:")
    for agent in agency.list_agents():
        print(f"  - {agent['name']}: {agent['description'][:50]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
