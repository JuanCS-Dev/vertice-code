"""MCP Server - FastMCP-based server for Claude Desktop integration."""

import asyncio
import logging
from typing import Optional
from vertice_core.tools.base import ToolRegistry
from vertice_core.tools.registry_helper import get_default_registry
from vertice_core.integrations.mcp.config import MCPConfig
from vertice_core.integrations.mcp.shell_handler import ShellManager
from vertice_core.integrations.mcp.tools import MCPToolsAdapter
from vertice_core.integrations.mcp.gateway import mcp_gateway

logger = logging.getLogger(__name__)


class QwenMCPServer:
    """MCP Server for Qwen Dev CLI."""

    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or MCPConfig.from_env()
        self.mcp = None
        self._init_error: str | None = None
        try:
            # Lazy import: fastmcp currently configures logging on import and may break
            # if the local rich version is incompatible. Keep the rest of the app usable.
            from fastmcp import FastMCP  # type: ignore

            self.mcp = FastMCP("Qwen Dev CLI")
        except Exception as e:
            self._init_error = str(e)
            logger.warning(f"fastmcp unavailable/incompatible: {e}")

        self.shell_manager = ShellManager()
        self.tools_adapter: Optional[MCPToolsAdapter] = None
        self._running = False

    def initialize(self, registry: ToolRegistry, prometheus_provider=None):
        """Initialize server with tool registry."""
        if self.mcp is None:
            raise RuntimeError(
                "MCP server cannot initialize because fastmcp is unavailable/incompatible. "
                f"Details: {self._init_error}"
            )

        # 1. Initialize MCPToolsAdapter (Shell + CLI Tools)
        self.tools_adapter = MCPToolsAdapter(registry, self.shell_manager)

        # 2. Configure Gateway (Agents + Prometheus)
        if prometheus_provider:
            try:
                from prometheus.integrations.mcp_adapter import PrometheusMCPAdapter

                # Initialize Prometheus Adapter
                prom_adapter = PrometheusMCPAdapter(prometheus_provider, self.shell_manager)
                # Register with Gateway
                mcp_gateway.set_prometheus_adapter(prom_adapter)
                # Also link to tools_adapter for backward compatibility if needed
                self.tools_adapter.prometheus_adapter = prom_adapter
            except Exception as e:
                logger.warning(f"Prometheus MCP adapter unavailable: {e}")

        # 3. Register EVERYTHING via Gateway
        # Note: MCPToolsAdapter (Shell) is manually registered first
        self.tools_adapter.register_all(self.mcp)

        # Then all agents via Gateway
        gateway_stats = mcp_gateway.register_all(self.mcp)

        total_cli = len(self.tools_adapter._mcp_tools)
        total_gateway = sum(gateway_stats.values())

        logger.info(
            f"MCP Server initialized with {total_cli} CLI/Shell tools + {total_gateway} Agent tools. "
            f"Details: {gateway_stats}"
        )

    async def start(self):
        """Start MCP server."""
        if not self.config.enabled:
            logger.info("MCP server disabled in config")
            return

        if self._running:
            logger.warning("MCP server already running")
            return

        if self.mcp is None:
            raise RuntimeError(
                "MCP server cannot start because fastmcp is unavailable/incompatible. "
                f"Details: {self._init_error}"
            )

        try:
            self._running = True
            logger.info(
                f"Starting MCP server on {self.config.host}:{self.config.port} (transport={self.config.transport})"
            )

            if self.config.transport == "sse":
                await self.mcp.run(
                    transport="sse",
                    host=self.config.host,
                    port=self.config.port,
                )
            else:
                await self.mcp.run(
                    transport="stdio",
                )

        except Exception as e:
            logger.error(f"MCP server error: {e}")
            self._running = False
            raise

    async def stop(self):
        """Stop MCP server."""
        if not self._running:
            return

        logger.info("Stopping MCP server...")
        self._running = False

        await self.shell_manager.close_all()
        logger.info("MCP server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


async def run_mcp_server(registry: ToolRegistry, config: Optional[MCPConfig] = None):
    """Run MCP server (entry point for standalone mode)."""
    server = QwenMCPServer(config)
    server.initialize(registry)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = MCPConfig.from_env()
    config.enabled = True

    registry = get_default_registry()

    asyncio.run(run_mcp_server(registry, config))
