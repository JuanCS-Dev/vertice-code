"""
Maestro Bootstrap - Lazy initialization system.

Handles lazy loading of LLM clients, agents, and governance.
"""

from __future__ import annotations

import logging

from .formatters import console, render_error
from .state import state

logger = logging.getLogger(__name__)


async def ensure_initialized() -> None:
    """Hydrate the Swarm - Real initialization with v6.0 agents."""
    if state.initialized:
        return

    console.print("\n[dim]Connecting to Matrix (LLM & MCP)...[/dim]")

    try:
        # 1. Core Infrastructure
        with console.status("[bold green]Bootstrapping Neural Core...[/bold green]"):
            from vertice_cli.core.llm import LLMClient
            from vertice_cli.core.mcp_client import MCPClient
            from vertice_cli.tools.base import ToolRegistry

            state.llm_client = LLMClient()

            # Initialize tool registry and MCP adapter
            registry = ToolRegistry()
            state.mcp_client = MCPClient(registry)

        # 2. Wake up the Agents v6.0
        with console.status("[bold green]Bootstrapping Neural Agents...[/bold green]"):
            from vertice_cli.agents.explorer import ExplorerAgent
            from vertice_cli.agents.planner import PlannerAgent
            from vertice_cli.agents.reviewer import ReviewerAgent

            state.agents = {
                "planner": PlannerAgent(state.llm_client, state.mcp_client),
                "explorer": ExplorerAgent(state.llm_client, state.mcp_client),
                "reviewer": ReviewerAgent(state.llm_client, state.mcp_client),
            }

            # Optional: Pre-load Explorer graph cache
            try:
                if hasattr(state.agents["explorer"], "load_graph"):
                    await state.agents["explorer"].load_graph()
            except (AttributeError, KeyError, FileNotFoundError):
                pass  # First run, no cache yet

        # 3. Initialize Constitutional Governance
        try:
            from vertice_cli.maestro_governance import MaestroGovernance

            state.governance = MaestroGovernance(
                llm_client=state.llm_client,
                mcp_client=state.mcp_client,
                enable_governance=True,
                enable_counsel=True,
                enable_observability=True,
                auto_risk_detection=True,
            )
            await state.governance.initialize()
        except Exception as e:
            logger.warning(f"Governance initialization failed: {e}")
            console.print("[yellow]Running without governance (degraded mode)[/yellow]")
            state.governance = None

        state.initialized = True
        console.print("[green]Vertice-MAXIMUS Online[/green]\n")

    except Exception as e:
        render_error("Bootstrap Failed", str(e))
        logger.exception("Initialization error details")
        raise
