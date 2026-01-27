#!/usr/bin/env python3
"""
Standalone MCP Server Runner
Entry point para executar o MCP Server sem dependencies do Prometheus main

Este módulo evita imports circulares executando o MCP Server de forma independente.
"""

import asyncio
import logging
import argparse
import sys
from typing import Optional

from .config import MCPServerConfig
from .server import PrometheusMCPServer
from .transport import MCPHTTPServer

logger = logging.getLogger(__name__)


async def run_mcp_server():
    """Run the MCP server standalone."""
    parser = argparse.ArgumentParser(description="Prometheus MCP Server")
    parser.add_argument(
        "--host",
        default=None,
        help="Server host (default: MCP_HOST/HOST env var, fallback: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Server port (default: MCP_PORT/PORT env var, fallback: 3000)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (default: MCP_LOG_LEVEL env var, fallback: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = MCPServerConfig.from_env()
    _apply_cli_overrides(config, host=args.host, port=args.port, log_level=args.log_level)

    logger.info(f"Starting MCP Server on {config.host}:{config.port}...")

    try:
        # Initialize MCP server
        mcp_server = PrometheusMCPServer(config)
        await mcp_server.start()

        # Initialize HTTP transport
        http_server = MCPHTTPServer(mcp_server, config)
        await http_server.start()

        logger.info(f"🚀 MCP Server running at http://{args.host}:{args.port}")
        logger.info(f"   Health check: http://{args.host}:{args.port}/health")
        logger.info(f"   MCP endpoint: http://{args.host}:{args.port}/mcp")
        logger.info("Press Ctrl+C to stop...")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            await http_server.stop()
            await mcp_server.stop()
        except Exception as e:
            pass
        logger.info("Server stopped")


def _apply_cli_overrides(
    config: MCPServerConfig,
    *,
    host: Optional[str],
    port: Optional[int],
    log_level: Optional[str],
) -> None:
    if host:
        config.host = host
    if port is not None:
        config.port = port
    if log_level:
        config.log_level = log_level.upper()


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
