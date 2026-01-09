"""
ArchitectFormatter - Format architecture decision responses.

Handles responses containing architecture approval/rejection decisions,
approach descriptions, risk assessments, and recommendations.
"""

from typing import Any, AsyncIterator


class ArchitectFormatter:
    """
    Format ArchitectAgent architecture decision responses.

    Expected data structure:
        {
            "decision": "APPROVED" | "REJECTED",
            "architecture": {
                "approach": str,
                "risks": List[str],
                "estimated_complexity": str
            },
            "recommendations": List[str]
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains architecture decision ('decision' key)."""
        return isinstance(data, dict) and "decision" in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format architecture decision with approach, risks, and recommendations."""
        decision = data.get("decision", "UNKNOWN")
        emoji = "✅" if decision == "APPROVED" else "❌"
        yield f"{emoji} **{decision}**\n\n"
        yield f"*{reasoning}*\n"

        arch = data.get("architecture", {})
        if arch.get("approach"):
            yield f"\n**Approach:** {arch['approach']}\n"
        if arch.get("risks"):
            yield f"\n**Risks:** {', '.join(arch['risks'])}\n"
        if arch.get("estimated_complexity"):
            yield f"\n**Complexity:** {arch['estimated_complexity']}\n"

        recommendations = data.get("recommendations", [])
        if recommendations:
            yield "\n**Recommendations:**\n"
            for rec in recommendations:
                yield f"- {rec}\n"
