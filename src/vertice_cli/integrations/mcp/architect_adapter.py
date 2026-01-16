"""
Architect MCP Adapter - Expose ArchitectAgent via MCP protocol.

Tools:
- architect_design: Design architecture from requirements
- architect_diagram: Generate Mermaid diagrams
- architect_get_status: Get agent status
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ArchitectMCPAdapter:
    """Adapter to expose ArchitectAgent tools via MCP.

    REUSES existing `architect` singleton from `agents.architect.agent`.
    Does NOT create a new agent instance.
    """

    def __init__(self):
        self._mcp_tools: Dict[str, Any] = {}
        self._architect = None

    def _get_architect(self):
        """Lazy import to avoid circular dependencies."""
        if self._architect is None:
            from agents.architect.agent import architect

            self._architect = architect
        return self._architect

    def register_all(self, mcp_server) -> None:
        """Register all Architect tools as MCP tools."""

        @mcp_server.tool(name="architect_design")
        async def architect_design(
            requirements: str,
            level: str = "service",
            constraints: Optional[str] = None,
        ) -> dict:
            """Design architecture based on requirements."""
            try:
                from agents.architect.types import DesignLevel

                architect = self._get_architect()

                # Map string to DesignLevel enum
                level_map = {
                    "system": DesignLevel.SYSTEM,
                    "service": DesignLevel.SERVICE,
                    "component": DesignLevel.COMPONENT,
                }
                design_level = level_map.get(level.lower(), DesignLevel.SERVICE)
                constraints_list = constraints.split(",") if constraints else None

                result_chunks = []
                async for chunk in architect.design(
                    requirements=requirements,
                    level=design_level,
                    constraints=constraints_list,
                    stream=True,
                ):
                    result_chunks.append(chunk)

                return {
                    "success": True,
                    "tool": "architect_design",
                    "design": "".join(result_chunks),
                    "level": level,
                }
            except Exception as e:
                logger.error(f"architect_design error: {e}")
                return {"success": False, "tool": "architect_design", "error": str(e)}

        @mcp_server.tool(name="architect_diagram")
        async def architect_diagram(
            description: str,
            diagram_type: str = "flowchart",
        ) -> dict:
            """Generate Mermaid architecture diagram."""
            try:
                architect = self._get_architect()

                result_chunks = []
                async for chunk in architect.diagram(
                    description=description,
                    diagram_type=diagram_type,
                ):
                    result_chunks.append(chunk)

                return {
                    "success": True,
                    "tool": "architect_diagram",
                    "diagram": "".join(result_chunks),
                    "type": diagram_type,
                }
            except Exception as e:
                logger.error(f"architect_diagram error: {e}")
                return {"success": False, "tool": "architect_diagram", "error": str(e)}

        @mcp_server.tool(name="architect_get_status")
        async def architect_get_status() -> dict:
            """Get Architect agent status."""
            try:
                architect = self._get_architect()
                status = architect.get_status()

                return {
                    "success": True,
                    "tool": "architect_get_status",
                    "status": status,
                }
            except Exception as e:
                logger.error(f"architect_get_status error: {e}")
                return {"success": False, "tool": "architect_get_status", "error": str(e)}

        # Register all tools
        self._mcp_tools.update(
            {
                "architect_design": architect_design,
                "architect_diagram": architect_diagram,
                "architect_get_status": architect_get_status,
            }
        )

        logger.info(f"Registered {len(self._mcp_tools)} Architect MCP tools")

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())


__all__ = ["ArchitectMCPAdapter"]
