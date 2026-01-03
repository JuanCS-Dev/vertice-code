"""
DevOps Formatters - Deployment plans and responses.

Handles structured deployment plans with pre/post checks,
strategies, and infrastructure details.
"""

from typing import Any, AsyncIterator, Dict


class DevOpsFormatter:
    """
    Format DevOpsAgent deployment plan outputs.

    Expected data structure:
        {
            "plan": str | {
                "deployment_id": str,
                "strategy": str,
                "pre_checks": List[str],
                "deployment_steps": List[str],
                "post_checks": List[str]
            },
            "status": str,
            "infrastructure": Dict[str, Any],
            "configuration": Dict[str, Any]
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains a deployment plan ('plan' key)."""
        return isinstance(data, dict) and 'plan' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format deployment plan with strategy, checks, and infrastructure details."""
        yield f"## DevOps Deployment Plan\n\n"
        yield f"*{reasoning}*\n\n"

        plan = data['plan']
        if isinstance(plan, dict):
            async for chunk in DevOpsFormatter._format_plan_dict(plan):
                yield chunk
        else:
            yield str(plan)

        if data.get('status'):
            yield f"\n**Status:** {data['status']}\n"

        async for chunk in DevOpsFormatter._format_section(data, 'infrastructure', 'Infrastructure'):
            yield chunk

        async for chunk in DevOpsFormatter._format_section(data, 'configuration', 'Configuration'):
            yield chunk

    @staticmethod
    async def _format_plan_dict(plan: Dict) -> AsyncIterator[str]:
        """Format structured deployment plan dictionary."""
        if plan.get('deployment_id'):
            yield f"**Deployment ID:** {plan['deployment_id']}\n"
        if plan.get('strategy'):
            yield f"**Strategy:** {plan['strategy']}\n"

        for section, title in [
            ('pre_checks', 'Pre-Checks'),
            ('deployment_steps', 'Deployment Steps'),
            ('post_checks', 'Post-Checks')
        ]:
            items = plan.get(section, [])
            if items:
                yield f"\n**{title}:**\n"
                for item in items:
                    yield f"- {item}\n"

    @staticmethod
    async def _format_section(data: Dict, key: str, title: str) -> AsyncIterator[str]:
        """Format a generic key-value section from the data dictionary."""
        section = data.get(key)
        if not section:
            return
        yield f"\n**{title}:**\n"
        for k, v in section.items():
            yield f"- {k}: {v}\n"


class DevOpsResponseFormatter:
    """
    Format simple DevOps LLM text responses.

    Handles responses that contain 'response' but not 'plan'.
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data is a simple DevOps response (has 'response', no 'plan')."""
        return isinstance(data, dict) and 'response' in data and 'plan' not in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Output the raw response text."""
        yield data['response']
