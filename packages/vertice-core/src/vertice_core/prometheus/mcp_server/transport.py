"""
MCP Server HTTP Transport

HTTP transport layer for the Prometheus MCP Server.
Handles incoming HTTP requests and forwards them to the MCP server.

Created with love for reliable protocol transport.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

from aiohttp import web, WSMsgType
import aiohttp_cors

from .server import PrometheusMCPServer
from .config import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPHTTPServer:
    """
    HTTP transport for MCP server.

    Provides REST endpoints for MCP communication over HTTP.
    """

    def __init__(self, mcp_server: PrometheusMCPServer, config: MCPServerConfig):
        self.mcp_server = mcp_server
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.instance_id}")

        # Web server
        self.app = None
        self.runner = None
        self.site = None

        # Statistics
        self.http_requests = 0
        self.http_errors = 0

    def create_app(self) -> web.Application:
        """Create the aiohttp application."""
        app = web.Application()

        # CORS support
        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                )
            },
        )

        # MCP endpoints
        app.router.add_post("/mcp", self.handle_mcp_request)
        app.router.add_get("/health", self.handle_health_check)
        app.router.add_get("/status", self.handle_status)

        # Apply CORS to all routes
        for route in app.router.routes():
            cors.add(route)

        self.app = app
        return app

    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """Handle incoming MCP requests."""
        self.http_requests += 1

        try:
            # Parse JSON-RPC request
            if request.content_type != "application/json":
                return web.json_response(
                    {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}},
                    status=400,
                )

            request_data = await request.json()

            # Validate JSON-RPC format
            if not isinstance(request_data, dict):
                return web.json_response(
                    {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
                    status=400,
                )

            if "jsonrpc" not in request_data or request_data["jsonrpc"] != "2.0":
                return web.json_response(
                    {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
                    status=400,
                )

            if "method" not in request_data:
                return web.json_response(
                    {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
                    status=400,
                )

            # Check authentication if required
            if self.config.require_auth:
                auth_header = request.headers.get("Authorization", "")
                if not self._check_authentication(auth_header):
                    return web.json_response(
                        {
                            "jsonrpc": "2.0",
                            "error": {"code": -32000, "message": "Authentication required"},
                        },
                        status=401,
                    )

            # Handle the MCP request
            response = await self.mcp_server.handle_request(request_data)

            # Return JSON-RPC response
            return web.json_response(json.loads(response.to_json()), status=200)

        except json.JSONDecodeError:
            self.http_errors += 1
            return web.json_response(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status=400
            )
        except Exception as e:
            self.http_errors += 1
            self.logger.error(f"Error handling MCP request: {e}")
            return web.json_response(
                {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}},
                status=500,
            )

    async def handle_health_check(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        health_status = {
            "status": "healthy" if self.mcp_server.is_running() else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "server": self.config.instance_id,
            "version": self.config.server_version,
        }

        status_code = 200 if self.mcp_server.is_running() else 503
        return web.json_response(health_status, status=status_code)

    async def handle_status(self, request: web.Request) -> web.Response:
        """Handle status requests."""
        server_stats = self.mcp_server.get_stats()
        http_stats = {
            "http_requests": self.http_requests,
            "http_errors": self.http_errors,
            "uptime_seconds": server_stats.get("uptime_seconds", 0),
        }

        status_info = {
            **server_stats,
            "http": http_stats,
            "timestamp": datetime.now().isoformat(),
        }

        return web.json_response(status_info)

    def _check_authentication(self, auth_header: str) -> bool:
        """Check authentication header."""
        if not auth_header.startswith("Bearer "):
            return False

        token = auth_header[7:]  # Remove "Bearer " prefix
        return token in self.config.api_keys

    async def start(self):
        """Start the HTTP server."""
        if not self.app:
            self.app = self.create_app()

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.config.host, self.config.port)
        await self.site.start()

        self.logger.info(f"MCP HTTP Server started on http://{self.config.host}:{self.config.port}")

    async def stop(self):
        """Stop the HTTP server."""
        if self.site:
            await self.site.stop()

        if self.runner:
            await self.runner.cleanup()

        self.logger.info("MCP HTTP Server stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP server statistics."""
        return {
            "http_requests": self.http_requests,
            "http_errors": self.http_errors,
            "host": self.config.host,
            "port": self.config.port,
        }


class MCPWebSocketServer:
    """
    WebSocket transport for MCP server.

    Provides real-time bidirectional communication via WebSockets.
    """

    def __init__(self, mcp_server: PrometheusMCPServer, config: MCPServerConfig):
        self.mcp_server = mcp_server
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ws.{config.instance_id}")

        # WebSocket connections
        self.active_connections = set()

        # Statistics
        self.ws_connections = 0
        self.ws_messages = 0

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.active_connections.add(ws)
        self.ws_connections += 1

        self.logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        self.ws_messages += 1
                        request_data = json.loads(msg.data)

                        # Handle MCP request
                        response = await self.mcp_server.handle_request(request_data)
                        response_json = response.to_json()

                        await ws.send_str(response_json)

                    except json.JSONDecodeError:
                        await ws.send_str(
                            json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "error": {"code": -32700, "message": "Parse error"},
                                }
                            )
                        )
                    except Exception as e:
                        self.logger.error(f"WebSocket message error: {e}")
                        await ws.send_str(
                            json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "error": {"code": -32603, "message": "Internal error"},
                                }
                            )
                        )

                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")

        finally:
            self.active_connections.remove(ws)
            self.logger.info(
                f"WebSocket connection closed. Remaining: {len(self.active_connections)}"
            )

        return ws

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket server statistics."""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.ws_connections,
            "messages_processed": self.ws_messages,
        }
