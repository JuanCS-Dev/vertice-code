"""
MCP Server Lifecycle Manager

Manages the startup, configuration, and shutdown of the complete MCP server stack.

Created with love for robust server lifecycle management.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import logging
import signal
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager
from datetime import datetime

from .config import MCPServerConfig
from .server import PrometheusMCPServer
from .transport import MCPHTTPServer, MCPWebSocketServer

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    Lifecycle manager for the Prometheus MCP Server.

    Handles startup, configuration validation, component initialization,
    and graceful shutdown of the entire MCP server stack.
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        self.config = config or MCPServerConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.config.instance_id}")

        # Server components
        self.mcp_server: Optional[PrometheusMCPServer] = None
        self.http_server: Optional[MCPHTTPServer] = None
        self.ws_server: Optional[MCPWebSocketServer] = None

        # Lifecycle state
        self.running = False
        self.start_time: Optional[datetime] = None
        self.shutdown_event = asyncio.Event()

        # Signal handling
        self._signal_handlers = []

    async def initialize(self) -> bool:
        """
        Initialize all server components.

        Returns True if initialization successful, False otherwise.
        """
        try:
            self.logger.info("Initializing MCP Server components...")

            # Validate configuration
            validation_issues = self.config.validate()
            if validation_issues:
                self.logger.error("Configuration validation failed:")
                for issue in validation_issues:
                    self.logger.error(f"  - {issue}")
                return False

            # Initialize MCP server
            self.mcp_server = PrometheusMCPServer(self.config)
            self.logger.info("MCP Server initialized")

            # Initialize HTTP transport
            self.http_server = MCPHTTPServer(self.mcp_server, self.config)
            self.logger.info("HTTP Transport initialized")

            # Initialize WebSocket transport (optional)
            if self.config.enable_caching:  # Use this flag to enable WS for now
                self.ws_server = MCPWebSocketServer(self.mcp_server, self.config)
                self.logger.info("WebSocket Transport initialized")

            self.logger.info("All MCP Server components initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP Server: {e}")
            await self._cleanup_on_failure()
            return False

    async def start(self) -> bool:
        """
        Start the MCP server.

        Returns True if startup successful, False otherwise.
        """
        if self.running:
            self.logger.warning("Server is already running")
            return True

        try:
            self.logger.info(f"Starting MCP Server {self.config.instance_id}...")

            # Start MCP server
            await self.mcp_server.start()
            self.logger.info("MCP Server started")

            # Start HTTP server
            await self.http_server.start()
            self.logger.info("HTTP Server started")

            # Start WebSocket server if available
            if self.ws_server:
                # WebSocket would be integrated into the HTTP server
                self.logger.info("WebSocket support enabled")

            # Setup signal handlers
            self._setup_signal_handlers()

            self.running = True
            self.start_time = datetime.now()

            self.logger.info(f"🚀 MCP Server {self.config.instance_id} started successfully!")
            self.logger.info(f"   HTTP endpoint: http://{self.config.host}:{self.config.port}/mcp")
            self.logger.info(
                f"   Health check: http://{self.config.host}:{self.config.port}/health"
            )
            self.logger.info(f"   Status: http://{self.config.host}:{self.config.port}/status")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start MCP Server: {e}")
            await self._cleanup_on_failure()
            return False

    async def stop(self, grace_period: float = 5.0):
        """
        Stop the MCP server gracefully.

        Args:
            grace_period: Time in seconds to wait for graceful shutdown
        """
        if not self.running:
            self.logger.info("Server is not running")
            return

        self.logger.info(f"Stopping MCP Server {self.config.instance_id}...")

        # Signal shutdown
        self.shutdown_event.set()
        self.running = False

        try:
            # Stop components in reverse order
            if self.ws_server:
                self.logger.info("Stopping WebSocket server...")
                # WebSocket cleanup would go here

            if self.http_server:
                self.logger.info("Stopping HTTP server...")
                await asyncio.wait_for(self.http_server.stop(), timeout=grace_period)

            if self.mcp_server:
                self.logger.info("Stopping MCP server...")
                await asyncio.wait_for(self.mcp_server.stop(), timeout=grace_period)

        except asyncio.TimeoutError:
            self.logger.warning(f"Graceful shutdown timed out after {grace_period}s")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        # Cleanup signal handlers
        self._cleanup_signal_handlers()

        shutdown_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self.logger.info(f"✅ MCP Server stopped (ran for {shutdown_time:.1f}s)")

    async def run_forever(self):
        """Run the server indefinitely until shutdown signal received."""
        try:
            await self.initialize()
            if not await self.start():
                return

            self.logger.info("MCP Server running. Press Ctrl+C to stop.")

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())

        # Handle common termination signals
        signals = [signal.SIGINT, signal.SIGTERM]
        if hasattr(signal, "SIGUSR1"):
            signals.append(signal.SIGUSR1)

        for sig in signals:
            try:
                signal.signal(sig, signal_handler)
                self._signal_handlers.append(sig)
            except (ValueError, OSError):
                # Signal not available on this platform
                pass

    def _cleanup_signal_handlers(self):
        """Cleanup signal handlers."""
        for sig in self._signal_handlers:
            try:
                signal.signal(sig, signal.SIG_DFL)
            except (ValueError, OSError):
                pass
        self._signal_handlers.clear()

    async def _cleanup_on_failure(self):
        """Cleanup components on initialization/startup failure."""
        if self.ws_server:
            # Cleanup WebSocket components
            pass

        if self.http_server:
            try:
                await self.http_server.stop()
            except Exception:
                pass

        if self.mcp_server:
            try:
                await self.mcp_server.stop()
            except Exception:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive server status."""
        status = {
            "running": self.running,
            "instance_id": self.config.instance_id,
            "version": self.config.server_version,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (
                (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            ),
            "config": self.config.to_dict(),
        }

        # Add component status
        if self.mcp_server:
            status["mcp_server"] = self.mcp_server.get_stats()

        if self.http_server:
            status["http_server"] = self.http_server.get_stats()

        if self.ws_server:
            status["websocket_server"] = self.ws_server.get_stats()

        return status

    def is_healthy(self) -> bool:
        """Check if server is healthy."""
        if not self.running:
            return False

        # Check component health
        if self.mcp_server and not self.mcp_server.is_running():
            return False

        # HTTP server health check would go here
        # WebSocket health check would go here

        return True


@asynccontextmanager
async def managed_mcp_server(config: Optional[MCPServerConfig] = None):
    """
    Context manager for MCP server lifecycle.

    Usage:
        async with managed_mcp_server(config) as server:
            # Server is running
            await server.wait_for_shutdown()
    """
    manager = MCPServerManager(config)

    try:
        success = await manager.initialize()
        if not success:
            raise RuntimeError("Failed to initialize MCP server")

        success = await manager.start()
        if not success:
            raise RuntimeError("Failed to start MCP server")

        yield manager

    finally:
        await manager.stop()


def create_server_from_env() -> MCPServerManager:
    """Create MCP server manager from environment variables."""
    config = MCPServerConfig.from_env()
    return MCPServerManager(config)


def create_server_from_file(config_path: str) -> MCPServerManager:
    """Create MCP server manager from configuration file."""
    config = MCPServerConfig.from_file(config_path)
    return MCPServerManager(config)


async def run_server_cli():
    """Run MCP server from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Prometheus MCP Server")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--log-level", help="Logging level")

    args = parser.parse_args()

    # Create configuration
    if args.config:
        manager = create_server_from_file(args.config)
    else:
        config = MCPServerConfig()
        if args.host:
            config.host = args.host
        if args.port:
            config.port = args.port
        if args.log_level:
            config.log_level = args.log_level.upper()
        manager = MCPServerManager(config)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run server
    await manager.run_forever()


if __name__ == "__main__":
    # Allow running as standalone script
    asyncio.run(run_server_cli())
