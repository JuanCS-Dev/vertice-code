"""
Maestro Global State - Minimal shared context.

Singleton state for Maestro CLI components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GlobalState:
    """Minimal global state - keep it light."""

    agents: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    initialized: bool = False
    llm_client: Optional[Any] = None
    mcp_client: Optional[Any] = None
    governance: Optional[Any] = None  # MaestroGovernance instance


# Singleton instance
state = GlobalState()
