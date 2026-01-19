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
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import diretamente do mcp_server (evita prometheus/__init__.py)
from prometheus.mcp_server.config import MCPServerConfig
from prometheus.mcp_server.server import PrometheusMCPServer
from prometheus.mcp_server.transport import MCPHTTPServer

logger = logging.getLogger(__name__)


async def run_mcp_server():
    """Run the MCP server standalone."""
    parser = argparse.ArgumentParser(description="Prometheus MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=3000, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create configuration
    config = MCPServerConfig(
        host=args.host,
        port=args.port,
        log_level=args.log_level.upper(),
    )

    logger.info(f"Starting MCP Server on {args.host}:{args.port}...")

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
        except Exception:
            pass
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
