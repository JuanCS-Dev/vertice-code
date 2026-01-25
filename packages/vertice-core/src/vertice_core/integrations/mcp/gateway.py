"""
MCP Gateway - Unified registration of all MCP adapters.

Single source of truth for tool registration.

Registered Adapters:
- Daimon (4 tools): Passive insights
- Coder (4 tools): Code generation
- Reviewer (3 tools): Code review
- Architect (3 tools): Architecture design
- Noesis (12 tools): Consciousness
- Prometheus (8 tools): Meta-agent
- Shell (4 tools): Command execution
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vertice_core.integrations.mcp.daimon_adapter import DaimonMCPAdapter
from vertice_core.integrations.mcp.coder_adapter import CoderMCPAdapter
from vertice_core.integrations.mcp.reviewer_adapter import ReviewerMCPAdapter
from vertice_core.integrations.mcp.architect_adapter import ArchitectMCPAdapter
from vertice_core.integrations.mcp.noesis_adapter import NoesissMCPAdapter

logger = logging.getLogger(__name__)


class MCPGateway:
    """Unified MCP Gateway - Single Source of Truth.

    Centralizes registration of all MCP adapters.
    Provides health check and tool listing.
    """

    def __init__(self):
        # Core adapters (always available)
        self.daimon_adapter = DaimonMCPAdapter()
        self.coder_adapter = CoderMCPAdapter()
        self.reviewer_adapter = ReviewerMCPAdapter()
        self.architect_adapter = ArchitectMCPAdapter()
        self.noesis_adapter = NoesissMCPAdapter()

        # Optional adapters (set by caller)
        self.prometheus_adapter: Optional[Any] = None
        self.shell_adapter: Optional[Any] = None

        self._registered = False

    def set_prometheus_adapter(self, adapter) -> None:
        """Set Prometheus adapter (requires PrometheusProvider)."""
        self.prometheus_adapter = adapter

    def register_all(self, mcp_server) -> Dict[str, int]:
        """Register all tools from all adapters.

        Returns:
            Dict mapping adapter name to tool count
        """
        if self._registered:
            logger.warning("MCPGateway.register_all() called twice, skipping")
            return {}

        stats: Dict[str, int] = {}

        # 1. Daimon (passive insights)
        self.daimon_adapter.register_all(mcp_server)
        stats["daimon"] = len(self.daimon_adapter.list_registered_tools())

        # 2. Coder (code generation)
        self.coder_adapter.register_all(mcp_server)
        stats["coder"] = len(self.coder_adapter.list_registered_tools())

        # 3. Reviewer (code review)
        self.reviewer_adapter.register_all(mcp_server)
        stats["reviewer"] = len(self.reviewer_adapter.list_registered_tools())

        # 4. Architect (architecture design)
        self.architect_adapter.register_all(mcp_server)
        stats["architect"] = len(self.architect_adapter.list_registered_tools())

        # 5. Noesis (consciousness)
        self.noesis_adapter.register_all(mcp_server)
        stats["noesis"] = len(self.noesis_adapter.list_registered_tools())

        # 6. Prometheus (if available)
        if self.prometheus_adapter:
            self.prometheus_adapter.register_all(mcp_server)
            stats["prometheus"] = len(self.prometheus_adapter.list_registered_tools())

        self._registered = True

        total = sum(stats.values())
        logger.info(f"MCPGateway registered {total} tools: {stats}")

        return stats

    def list_all_tools(self) -> Dict[str, List[str]]:
        """List all registered tools by adapter."""
        result = {}

        result["daimon"] = self.daimon_adapter.list_registered_tools()
        result["coder"] = self.coder_adapter.list_registered_tools()
        result["reviewer"] = self.reviewer_adapter.list_registered_tools()
        result["architect"] = self.architect_adapter.list_registered_tools()

        if self.prometheus_adapter:
            result["prometheus"] = self.prometheus_adapter.list_registered_tools()

        return result

    def get_health(self) -> Dict[str, Any]:
        """Get gateway health status."""
        tools = self.list_all_tools()
        total_tools = sum(len(t) for t in tools.values())

        return {
            "status": "healthy" if self._registered else "not_initialized",
            "total_tools": total_tools,
            "adapters": {
                name: {"registered": len(tools_list), "tools": tools_list}
                for name, tools_list in tools.items()
            },
        }


# Singleton instance
mcp_gateway = MCPGateway()


__all__ = ["MCPGateway", "mcp_gateway"]
