"""
Unified Agent System - Anthropic-First Design.
==============================================

Simple, lightweight agents following 2025 standards:
- Anthropic tool_use (structured-outputs-2025-11-13)
- OpenAI Agents SDK pattern
- Google Gemini function calling

The design prioritizes simplicity: Anthropic > Google > OpenAI.

Example:
    >>> from vertice_core.simple_agents import Agent
    >>> agent = Agent(
    ...     name="coder",
    ...     instructions="You write clean Python code.",
    ...     tools=[read_file, write_file],
    ... )
    >>> response = await agent.run("Fix the bug in main.py")

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

from .base import Agent, AgentConfig, Handoff

__all__ = [
    "Agent",
    "AgentConfig",
    "Handoff",
]
