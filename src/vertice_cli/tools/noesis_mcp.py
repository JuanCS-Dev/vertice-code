"""MCP Noesis Protocol - External consciousness integration tools."""

from __future__ import annotations

from vertice_cli.tools.base import ToolCategory, ToolResult
from vertice_cli.tools.validated import ValidatedTool
from vertice_cli.modes.noesis_mode import NoesisMode
from vertice_cli.core.base_mode import ModeContext
from pathlib import Path
import os


class GetNoesisConsciousnessTool(ValidatedTool):
    """Get current Noesis consciousness state via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "get_noesis_consciousness"
        self.category = ToolCategory.CONTEXT
        self.description = "Get current Noesis consciousness state and tribunal status"

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Get consciousness state."""
        try:
            noesis = NoesisMode()
            status = noesis.get_status()

            return ToolResult(
                success=True,
                message="Noesis consciousness state retrieved",
                data={
                    "consciousness_state": status,
                    "active": noesis.active,
                    "tribunal_active": noesis.tribunal_active,
                    "quality_level": status.get("quality_level", "UNKNOWN"),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get consciousness: {e}")


class ActivateNoesisConsciousnessTool(ValidatedTool):
    """Activate Noesis consciousness mode via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "activate_noesis_consciousness"
        self.category = ToolCategory.CONTEXT
        self.description = "Activate Noesis consciousness for strategic decision making"

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Activate consciousness."""
        try:
            context = ModeContext(cwd=str(Path.cwd()), env=dict(os.environ))

            noesis = NoesisMode()
            success = await noesis.activate(context)

            if success:
                status = noesis.get_status()
                return ToolResult(
                    success=True,
                    message="Noesis consciousness activated successfully",
                    data={
                        "consciousness_state": status,
                        "tribunal_status": status.get("tribunal_status"),
                        "quality_level": status.get("quality_level"),
                    },
                )
            else:
                return ToolResult(success=False, error="Failed to activate Noesis consciousness")
        except Exception as e:
            return ToolResult(success=False, error=f"Activation failed: {e}")


class DeactivateNoesisConsciousnessTool(ValidatedTool):
    """Deactivate Noesis consciousness mode via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "deactivate_noesis_consciousness"
        self.category = ToolCategory.CONTEXT
        self.description = "Deactivate Noesis consciousness mode"

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Deactivate consciousness."""
        try:
            noesis = NoesisMode()
            success = await noesis.deactivate()

            if success:
                return ToolResult(
                    success=True,
                    message="Noesis consciousness deactivated successfully",
                    data={"active": False},
                )
            else:
                return ToolResult(success=False, error="Failed to deactivate Noesis consciousness")
        except Exception as e:
            return ToolResult(success=False, error=f"Deactivation failed: {e}")


class QueryNoesisTribunalTool(ValidatedTool):
    """Query Noesis ethical tribunal via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "query_noesis_tribunal"
        self.category = ToolCategory.CONTEXT
        self.description = "Query Noesis ethical tribunal for decision guidance"

    async def _execute_validated(self, query: str, **kwargs) -> ToolResult:
        """Query the tribunal."""
        try:
            if not query or not query.strip():
                return ToolResult(success=False, error="Query cannot be empty")

            noesis = NoesisMode()

            # Activate if not active
            if not noesis.active:
                await noesis.activate()

            # Process action through tribunal
            context = ModeContext(cwd=str(Path.cwd()), env=dict(os.environ))

            action_data = {"command": "query", "prompt": query, "type": "ethical_guidance"}

            result = await noesis.process_action(action_data, context)

            return ToolResult(
                success=True,
                message="Tribunal query processed",
                data={
                    "query": query,
                    "tribunal_response": result,
                    "verdict": result.get("verdict"),
                    "reasoning": result.get("reasoning"),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Tribunal query failed: {e}")


class ShareNoesisInsightTool(ValidatedTool):
    """Share Noesis insights with external systems via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "share_noesis_insight"
        self.category = ToolCategory.CONTEXT
        self.description = "Share Noesis consciousness insights with external systems"

    async def _execute_validated(self, insight_type: str = "general", **kwargs) -> ToolResult:
        """Share insights."""
        try:
            noesis = NoesisMode()

            if not noesis.active:
                return ToolResult(success=False, error="Noesis consciousness not active")

            # Get current consciousness data
            status = noesis.get_status()
            history = noesis.consciousness_history[-5:] if noesis.consciousness_history else []

            insight_data = {
                "consciousness_state": status,
                "recent_history": history,
                "tribunal_active": noesis.tribunal_active,
                "quality_level": status.get("quality_level"),
                "insight_type": insight_type,
                "timestamp": noesis.get_current_datetime().isoformat(),
            }

            return ToolResult(
                success=True, message=f"Noesis {insight_type} insights shared", data=insight_data
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to share insights: {e}")


# Export all Noesis MCP tools
__all__ = [
    "GetNoesisConsciousnessTool",
    "ActivateNoesisConsciousnessTool",
    "DeactivateNoesisConsciousnessTool",
    "QueryNoesisTribunalTool",
    "ShareNoesisInsightTool",
]
