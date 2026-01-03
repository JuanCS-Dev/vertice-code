"""
Sofia Module - Wise Counselor Integration.

This module provides comprehensive counsel capabilities:
- Socratic questioning for deep exploration
- System 2 deliberation for complex ethical dilemmas
- Virtue-based counsel
- Chat mode for continuous dialogue

Architecture:
    - models.py: CounselMetrics, CounselRequest, CounselResponse
    - agent.py: SofiaIntegratedAgent
    - chat_mode.py: SofiaChatMode
    - helpers.py: Factory and CLI helpers

Usage:
    from vertice_cli.agents.sofia import SofiaIntegratedAgent, create_sofia_agent

    sofia = create_sofia_agent(llm_client, mcp_client)
    response = sofia.provide_counsel("Should I refactor this?")

Philosophy:
    "You don't replace human wisdom - you cultivate it."
"""

# Models
from .models import (
    CounselMetrics,
    CounselRequest,
    CounselResponse,
)

# Agent
from .agent import SofiaIntegratedAgent

# Chat Mode
from .chat_mode import SofiaChatMode

# Helpers
from .helpers import (
    create_sofia_agent,
    handle_sofia_slash_command,
)

__all__ = [
    # Models
    "CounselMetrics",
    "CounselRequest",
    "CounselResponse",
    # Agent
    "SofiaIntegratedAgent",
    # Chat Mode
    "SofiaChatMode",
    # Helpers
    "create_sofia_agent",
    "handle_sofia_slash_command",
]
