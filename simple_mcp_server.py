"""
Simple MCP Server for Cloud Run Deployment
Minimal implementation for testing Phase 2 deployment
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    print("❌ aiohttp is required. Install with: pip install aiohttp")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleMCPServer:
    """Simple MCP server for Cloud Run testing."""

    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8080"))

    async def handle_mcp_request(self, request):
        """Handle MCP JSON-RPC requests."""
        try:
            data = await request.json()
            logger.info(f"MCP Request: {data.get('method', 'unknown')}")

            # Simple echo response for testing
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "message": "Vertice MCP Server is running!",
                    "method": data.get("method", "unknown"),
                    "status": "healthy",
                    "server": "vertice-mcp-simple",
                    "version": "1.0.0",
                },
                "id": data.get("id", 1),
            }
            return web.json_response(response)

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                    "id": None,
                },
                status=400,
            )

    async def handle_health_check(self, request):
        """Handle health check requests."""
        return web.json_response(
            {
                "status": "healthy",
                "server": "vertice-mcp-simple",
                "timestamp": asyncio.get_event_loop().time(),
                "version": "1.0.0",
            }
        )

    async def handle_root(self, request):
        """Handle root requests with server info."""
        return web.Response(
            text=f"""
            <html>
            <head><title>Vertice MCP Server</title></head>
            <body>
                <h1>🌟 Vertice MCP Server (Simple)</h1>
                <p>Server is running on {self.host}:{self.port}</p>
                <h2>Endpoints:</h2>
                <ul>
                    <li><code>POST /mcp</code> - MCP JSON-RPC endpoint</li>
                    <li><code>GET /health</code> - Health check</li>
                </ul>
                <p><em>Phase 2: Development Complete - Ready for Phase 3!</em></p>
            </body>
            </html>
            """,
            content_type="text/html",
        )

    async def run_server(self):
        """Run the MCP server."""
        app = web.Application()
        app.router.add_post("/mcp", self.handle_mcp_request)
        app.router.add_get("/health", self.handle_health_check)
        app.router.add_get("/", self.handle_root)

        logger.info(f"🚀 Starting Vertice MCP Server on {self.host}:{self.port}")

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info("✅ Server is running and ready to accept requests!")
        logger.info(f"🌐 Health check: http://{self.host}:{self.port}/health")

        try:
            # Keep running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down server...")
        finally:
            await runner.cleanup()
            logger.info("👋 Server stopped.")


async def main():
    """Main entry point."""
    server = SimpleMCPServer()
    await server.run_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user.")
