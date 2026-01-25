"""MCP Server CLI entry point."""

import sys
import asyncio
import logging
from vertice_core.integrations.mcp.config import MCPConfig
from vertice_core.integrations.mcp.server import run_mcp_server
from vertice_core.tools.registry_helper import get_default_registry


def main(host: str = None, port: int = None, transport: str = None):
    """Run MCP server from command line."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = MCPConfig.from_env()
    config.enabled = True

    if host:
        config.host = host
    if port:
        config.port = port
    if transport:
        config.transport = transport

    registry = get_default_registry()

    try:
        asyncio.run(run_mcp_server(registry, config))
    except KeyboardInterrupt:
        print("\nMCP server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"MCP server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
