"""
Sofia Helpers - Factory Functions and CLI Integration.

This module provides quick start helpers and CLI integration:
- create_sofia_agent: Factory function
- handle_sofia_slash_command: CLI slash command handler

Philosophy:
    "Make wisdom accessible."
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import SofiaIntegratedAgent


def create_sofia_agent(
    llm_client: Any,
    mcp_client: Any,
    auto_detect: bool = True,
    socratic_ratio: float = 0.7,
) -> "SofiaIntegratedAgent":
    """
    Quick start helper to create a Sofia agent with common settings.

    Args:
        llm_client: LLM client
        mcp_client: MCP client
        auto_detect: Enable auto-detection of ethical dilemmas
        socratic_ratio: Ratio of questions vs answers (0.0 - 1.0)

    Returns:
        SofiaIntegratedAgent ready to use

    Example:
        >>> sofia = create_sofia_agent(llm, mcp)
        >>> response = sofia.provide_counsel("Should I do X?")
    """
    from .agent import SofiaIntegratedAgent

    return SofiaIntegratedAgent(
        llm_client=llm_client,
        mcp_client=mcp_client,
        auto_detect_ethical_dilemmas=auto_detect,
        socratic_ratio=socratic_ratio,
    )


async def handle_sofia_slash_command(
    query: str,
    sofia_agent: "SofiaIntegratedAgent",
) -> str:
    """
    Handle /sofia slash command.

    Args:
        query: User query after /sofia
        sofia_agent: Sofia agent instance

    Returns:
        Formatted counsel response

    Example:
        >>> sofia = create_sofia_agent(llm, mcp)
        >>> result = await handle_sofia_slash_command("Should I refactor?", sofia)
    """
    response = await sofia_agent.provide_counsel_async(query)

    output = "\n+================================================================+\n"
    output += "|  SOFIA - Conselheiro Sabio                                   |\n"
    output += "+================================================================+\n\n"

    output += f"Query: {response.original_query}\n\n"
    output += f"Counsel Type: {response.counsel_type}\n"
    output += f"Thinking Mode: {response.thinking_mode}\n"

    if response.questions_asked:
        output += f"\nQuestions Asked ({len(response.questions_asked)}):\n"
        for i, q in enumerate(response.questions_asked, 1):
            output += f"  {i}. {q}\n"

    output += f"\n{response.counsel}\n"

    if response.requires_professional:
        output += "\n!! URGENT: This situation requires professional help.\n"

    output += f"\nConfidence: {response.confidence:.0%} | "
    output += f"Processing: {response.processing_time_ms:.1f}ms\n"

    return output


__all__ = [
    "create_sofia_agent",
    "handle_sofia_slash_command",
]
