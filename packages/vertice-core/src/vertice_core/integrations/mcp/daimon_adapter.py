"""
Daimon MCP Adapter - Expose passive insights via MCP protocol.

Tools:
- get_daimon_insights: Get current insights from VERTICE.md
- observe_event: Record an external event
- get_daimon_status: Get collector stats
- trigger_analysis: Force immediate pattern analysis
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DaimonMCPAdapter:
    """Adapter to expose DaimonInsightsCollector tools via MCP.

    REUSES existing `insights_collector` from `vertice_core.core`.
    Does NOT create a new collector instance.
    """

    def __init__(self):
        self._mcp_tools: Dict[str, Any] = {}
        self._insights_collector = None

    def _get_collector(self):
        """Lazy import to avoid circular dependencies."""
        if self._insights_collector is None:
            from vertice_core.core import insights_collector

            self._insights_collector = insights_collector
        return self._insights_collector

    def register_all(self, mcp_server) -> None:
        """Register all Daimon tools as MCP tools."""

        @mcp_server.tool(name="get_daimon_insights")
        async def get_daimon_insights() -> dict:
            """Get current Daimon insights from VERTICE.md."""
            try:
                collector = self._get_collector()

                # Read insights file if exists
                insights_content = ""
                if collector.insights_file.exists():
                    insights_content = collector.insights_file.read_text()

                return {
                    "success": True,
                    "tool": "get_daimon_insights",
                    "insights": insights_content,
                    "observations_count": len(collector.observations),
                }
            except Exception as e:
                logger.error(f"get_daimon_insights error: {e}")
                return {"success": False, "tool": "get_daimon_insights", "error": str(e)}

        @mcp_server.tool(name="observe_event")
        async def observe_event(
            event_type: str,
            event_data: str,
            success: bool = True,
            duration: float = 0.0,
        ) -> dict:
            """Record an external event for Daimon pattern analysis."""
            try:
                collector = self._get_collector()

                await collector.observe_command(
                    command=f"{event_type}: {event_data}",
                    duration=duration,
                    success=success,
                    context={"source": "mcp", "type": event_type},
                )

                return {
                    "success": True,
                    "tool": "observe_event",
                    "event_type": event_type,
                    "recorded": True,
                }
            except Exception as e:
                logger.error(f"observe_event error: {e}")
                return {"success": False, "tool": "observe_event", "error": str(e)}

        @mcp_server.tool(name="get_daimon_status")
        async def get_daimon_status() -> dict:
            """Get Daimon collector statistics."""
            try:
                collector = self._get_collector()

                observations = collector.observations

                return {
                    "success": True,
                    "tool": "get_daimon_status",
                    "status": {
                        "total_observations": len(observations),
                        "insights_file": str(collector.insights_file),
                        "insights_file_exists": collector.insights_file.exists(),
                        "pending_until_analysis": 50 - (len(observations) % 50),
                    },
                }
            except Exception as e:
                logger.error(f"get_daimon_status error: {e}")
                return {"success": False, "tool": "get_daimon_status", "error": str(e)}

        @mcp_server.tool(name="trigger_analysis")
        async def trigger_analysis() -> dict:
            """Force immediate Daimon pattern analysis."""
            try:
                collector = self._get_collector()

                # Force analysis regardless of observation count
                await collector._analyze_and_update_insights()

                return {
                    "success": True,
                    "tool": "trigger_analysis",
                    "message": "Analysis triggered, insights updated",
                }
            except Exception as e:
                logger.error(f"trigger_analysis error: {e}")
                return {"success": False, "tool": "trigger_analysis", "error": str(e)}

        # Register all tools
        self._mcp_tools.update(
            {
                "get_daimon_insights": get_daimon_insights,
                "observe_event": observe_event,
                "get_daimon_status": get_daimon_status,
                "trigger_analysis": trigger_analysis,
            }
        )

        logger.info(f"Registered {len(self._mcp_tools)} Daimon MCP tools")

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())


__all__ = ["DaimonMCPAdapter"]
