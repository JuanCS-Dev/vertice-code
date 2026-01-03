"""
REPL Masterpiece Agent Adapter - Agent Integration.

This module provides agent registration and output formatting
for the REPL shell.

Features:
- Agent registration with coordinator
- Beautiful output formatting
- Agent adapter protocol

Philosophy:
    "Agents should integrate seamlessly."
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from rich.console import Console
    from vertice_cli.core.llm import LLMClient
    from vertice_cli.core.integration_coordinator import Coordinator

logger = logging.getLogger(__name__)


def format_agent_output(agent_name: str, response: Any, intent_type: Any) -> str:
    """
    Format agent output beautifully (human-readable).

    Boris Cherny: "Code is read 10x more than written. So is output."

    Args:
        agent_name: Name of the agent
        response: Agent response object
        intent_type: Type of intent processed

    Returns:
        Formatted output string
    """
    # Handle errors
    if not response.success:
        return f"❌ **{agent_name} Failed**\n\n{response.error}"

    # Special formatting for ReviewerAgent v3.0
    if agent_name == "ReviewerAgent" and isinstance(response.data, dict):
        return _format_reviewer_output(response.data)

    # Generic formatting for other agents
    if isinstance(response.data, dict):
        summary = response.data.get('summary', response.data.get('result', ''))
        if summary:
            return f"**{agent_name} Result:**\n\n{summary}"

        # Fallback: format dict nicely
        import json
        formatted = json.dumps(response.data, indent=2)
        return f"**{agent_name} Result:**\n\n```json\n{formatted}\n```"

    # Plain string output
    return str(response.data)


def _format_reviewer_output(data: Dict[str, Any]) -> str:
    """Format ReviewerAgent v3.0 output with McCabe analysis."""
    # Extract report (agent wraps it in 'report' key)
    data = data.get('report', data)

    # Header
    score = data.get('score', 0)
    approved = data.get('approved', False)
    metrics = data.get('metrics', [])

    lines = [
        "# 🔍 CODE REVIEW COMPLETE (v3.0 - McCabe Analysis)\n",
        f"**Score:** {score}/100",
        f"**Status:** {'✅ APPROVED for merge' if approved else '❌ CHANGES REQUIRED'}\n",
    ]

    # Function Metrics
    if metrics:
        lines.append("## 📊 Function Complexity Analysis\n")
        for m in metrics[:10]:
            lines.append(
                f"- `{m.get('function_name')}`: Complexity={m.get('complexity')}, "
                f"Args={m.get('args_count')}, LOC={m.get('loc')}"
            )
        if len(metrics) > 10:
            lines.append(f"  ... and {len(metrics) - 10} more functions")
        lines.append("")

    # Issues
    issues = data.get('issues', [])
    if issues:
        critical = [i for i in issues if i.get('severity') == 'CRITICAL']
        high = [i for i in issues if i.get('severity') == 'HIGH']
        medium = [i for i in issues if i.get('severity') == 'MEDIUM']

        if critical:
            lines.append("## 🚨 CRITICAL Issues\n")
            for issue in critical:
                lines.append(
                    f"- **{issue.get('file')}:{issue.get('line')}** "
                    f"[{issue.get('category')}]"
                )
                lines.append(f"  {issue.get('message')}")
                if issue.get('suggestion'):
                    lines.append(f"  💡 *{issue.get('suggestion')}*")
            lines.append("")

        if high:
            lines.append("## ⚠️ HIGH Priority\n")
            for issue in high:
                lines.append(
                    f"- **{issue.get('file')}:{issue.get('line')}** - "
                    f"{issue.get('message')}"
                )
            lines.append("")

        if medium:
            lines.append("## 📝 Medium Priority\n")
            for issue in medium:
                lines.append(
                    f"- {issue.get('file')}:{issue.get('line')} - "
                    f"{issue.get('message')}"
                )
            lines.append("")

    # Summary
    summary = data.get('summary', '')
    if summary:
        lines.append("## Summary\n")
        lines.append(summary)
        lines.append("")

    # Next Steps
    next_steps = data.get('next_steps', [])
    if next_steps:
        lines.append("## 🎯 Next Steps\n")
        for step in next_steps:
            lines.append(f"- {step}")

    return "\n".join(lines)


def register_agents(
    coordinator: "Coordinator",
    llm_client: "LLMClient",
    console: "Console",
    format_output_fn: Any,
) -> None:
    """
    Register agents with coordinator (Phase 2.2).

    Creates adapter to convert between agent.execute() and coordinator.invoke().

    Args:
        coordinator: Integration coordinator
        llm_client: LLM client instance
        console: Rich console for output
        format_output_fn: Function to format agent output
    """
    from vertice_cli.core.integration_types import IntentType
    from vertice_cli.agents.base import AgentTask
    from vertice_cli.agents.reviewer import ReviewerAgent
    from vertice_cli.agents.refactorer import RefactorerAgent

    async def make_agent_adapter(agent_class, intent_type):
        """Create adapter for agent."""
        agent_instance = agent_class(
            llm_client=llm_client,
            mcp_client=None
        )

        async def adapter_invoke(request: str, context: dict) -> dict:
            """Adapt agent.execute() to coordinator protocol."""
            import re

            # Extract file paths from request
            file_matches = re.findall(r'[\w\-./]+\.[\w]+', request)

            # Enrich context
            enriched_context = dict(context) if context else {}
            if file_matches:
                enriched_context['files'] = file_matches
                enriched_context['target_files'] = file_matches

            # Create AgentTask
            task = AgentTask(
                request=request,
                context=enriched_context,
                session_id="shell_session"
            )

            # Execute agent
            response = await agent_instance.execute(task)

            # Format output
            output = format_output_fn(
                agent_class.__name__,
                response,
                intent_type
            )

            return {
                "success": response.success,
                "output": output,
                "metadata": response.metadata,
                "execution_time_ms": 0.0,
                "tokens_used": None
            }

        return adapter_invoke

    # Agent wrapper class for protocol compliance
    class AgentWrapper:
        def __init__(self, invoke_func):
            self.invoke = invoke_func

    try:
        # Register ReviewerAgent
        reviewer_adapter = asyncio.run(
            make_agent_adapter(ReviewerAgent, IntentType.REVIEW)
        )
        coordinator.register_agent(
            IntentType.REVIEW,
            AgentWrapper(reviewer_adapter)
        )
        console.print("[dim]  → ReviewerAgent registered[/dim]")

        # Register RefactorerAgent
        refactorer_adapter = asyncio.run(
            make_agent_adapter(RefactorerAgent, IntentType.REFACTOR)
        )
        coordinator.register_agent(
            IntentType.REFACTOR,
            AgentWrapper(refactorer_adapter)
        )
        console.print("[dim]  → RefactorerAgent registered[/dim]")

    except Exception as e:
        console.print(f"[yellow]⚠️  Agent registration failed: {e}[/yellow]")


__all__ = ["format_agent_output", "register_agents"]
