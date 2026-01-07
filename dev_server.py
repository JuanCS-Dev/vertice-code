#!/usr/bin/env python3
"""
Vertice MCP - Quick Development Server

A simple development server for testing the MCP implementation
without full GCP deployment. Perfect for local development and testing.

Generated with ❤️ by Vertex AI Codey
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    print("❌ aiohttp is required. Install with: pip install aiohttp")
    exit(1)

from prometheus.mcp_server.server import PrometheusMCPServer
from prometheus.mcp_server.config import MCPServerConfig
from prometheus.skills.registry import LearnedSkill

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DevelopmentMCPServer:
    """
    Development MCP server with mock data for testing.

    Provides a fully functional MCP server with sample skills
    and responses for development and testing purposes.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host: str = host or os.getenv("HOST", "0.0.0.0")
        self.port: int = port if port is not None else int(os.getenv("PORT", "3000"))

        # Initialize MCP server
        config = MCPServerConfig(instance_id="dev-mcp-server", host=host, port=self.port)
        self.mcp_server = PrometheusMCPServer(config)

        # Add some sample skills for testing
        self._load_sample_skills()

        logger.info(f"Development MCP Server initialized on {host}:{port}")

    def _load_sample_skills(self):
        """Load sample skills for development testing."""

        sample_skills = [
            LearnedSkill(
                name="sentiment_analysis",
                description="Analyze sentiment in text using advanced NLP",
                procedure_steps=[
                    "Preprocess input text",
                    "Extract linguistic features",
                    "Apply ML model for classification",
                    "Return sentiment scores",
                ],
                category="nlp",
                success_rate=0.94,
                usage_count=150,
            ),
            LearnedSkill(
                name="data_visualization",
                description="Create insightful data visualizations",
                procedure_steps=[
                    "Analyze data structure",
                    "Choose appropriate chart types",
                    "Generate visualization code",
                    "Optimize for readability",
                ],
                category="analytics",
                success_rate=0.89,
                usage_count=87,
            ),
            LearnedSkill(
                name="code_review",
                description="Perform automated code review and suggestions",
                procedure_steps=[
                    "Parse code syntax",
                    "Check style guidelines",
                    "Identify potential bugs",
                    "Suggest improvements",
                ],
                category="development",
                success_rate=0.91,
                usage_count=203,
            ),
            LearnedSkill(
                name="task_planning",
                description="Break down complex tasks into manageable steps",
                procedure_steps=[
                    "Analyze task requirements",
                    "Identify dependencies",
                    "Create execution timeline",
                    "Define success criteria",
                ],
                category="planning",
                success_rate=0.96,
                usage_count=67,
            ),
            LearnedSkill(
                name="error_diagnosis",
                description="Diagnose and troubleshoot system errors",
                procedure_steps=[
                    "Collect error logs",
                    "Analyze stack traces",
                    "Identify root causes",
                    "Recommend fixes",
                ],
                category="debugging",
                success_rate=0.88,
                usage_count=134,
            ),
        ]

        # In a real implementation, these would be stored in the registry
        # For development, we'll mock the responses
        self.sample_skills = {skill.name: skill for skill in sample_skills}
        logger.info(f"Loaded {len(sample_skills)} sample skills for development")

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests with development-friendly responses."""

        try:
            # Add some development-friendly logging
            method = request_data.get("method", "unknown")
            req_id = request_data.get("id", "unknown")
            logger.info(f"Handling {method} request (ID: {req_id})")

            # Handle special development methods
            if method == "prometheus/status":
                return await self._handle_dev_status()
            elif method == "skills/list":
                return await self._handle_dev_skills_list()
            elif (
                method == "tools/call"
                and request_data.get("params", {}).get("name") == "prometheus_get_skill"
            ):
                return await self._handle_dev_get_skill(request_data)
            elif (
                method == "tools/call"
                and request_data.get("params", {}).get("name") == "prometheus_learn_skill"
            ):
                return await self._handle_dev_learn_skill(request_data)

            # Delegate to real MCP server for standard methods
            response = await self.mcp_server.handle_request(request_data)
            return json.loads(response.to_json())

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_data.get("id"),
            }

    async def _handle_dev_status(self) -> Dict[str, Any]:
        """Handle development status requests."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "instance_id": "dev-mcp-server",
                "version": "1.0.0-dev",
                "status": "running",
                "uptime_seconds": 0,  # Would track in real implementation
                "requests_processed": 0,
                "errors_count": 0,
                "skills_count": len(self.sample_skills),
                "environment": "development",
                "sample_data": True,
            },
            "id": "dev-status",
        }

    async def _handle_dev_skills_list(self) -> Dict[str, Any]:
        """Handle skills list for development."""
        skills_data = []
        for skill in self.sample_skills.values():
            skills_data.append(skill.to_dict())

        return {"jsonrpc": "2.0", "result": {"skills": skills_data}, "id": "dev-skills-list"}

    async def _handle_dev_get_skill(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get skill requests for development."""
        skill_name = request.get("params", {}).get("arguments", {}).get("skill_name")

        if skill_name in self.sample_skills:
            skill = self.sample_skills[skill_name]
            return {
                "jsonrpc": "2.0",
                "result": {"found": True, "skill": skill.to_dict()},
                "id": request.get("id"),
            }
        else:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "found": False,
                    "message": f"Skill '{skill_name}' not found in development data",
                },
                "id": request.get("id"),
            }

    async def _handle_dev_learn_skill(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle learn skill requests for development."""
        args = request.get("params", {}).get("arguments", {})

        skill_name = args.get("name")
        if not skill_name:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Missing skill name"},
                "id": request.get("id"),
            }

        # Create new skill from arguments
        new_skill = LearnedSkill(
            name=skill_name,
            description=args.get("description", ""),
            procedure_steps=args.get("procedure_steps", []),
            category=args.get("category", "general"),
            success_rate=0.85,  # Default for new skills
            usage_count=0,
        )

        # Add to sample skills
        self.sample_skills[skill_name] = new_skill

        logger.info(f"Learned new skill in development: {skill_name}")

        return {
            "jsonrpc": "2.0",
            "result": {
                "success": True,
                "message": f"Skill '{skill_name}' learned successfully in development mode",
            },
            "id": request.get("id"),
        }


async def run_development_server():
    """Run the development MCP server."""

    print("🚀 Starting Vertice MCP Development Server")
    print("=" * 50)

    server = DevelopmentMCPServer()

    # Simple HTTP server for testing
    async def handle_http(request):
        """Handle HTTP requests."""
        if request.method == "POST" and request.path == "/mcp":
            try:
                data = await request.json()
                response = await server.handle_request(data)
                return web.json_response(response)
            except Exception as e:
                return web.json_response(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                    },
                    status=400,
                )

        elif request.method == "GET" and request.path == "/health":
            return web.json_response(
                {
                    "status": "healthy",
                    "server": "vertice-mcp-dev",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        elif request.method == "GET" and request.path == "/":
            skills_html = "".join(
                f"<li>{skill.name}: {skill.description[:50]}...</li>"
                for skill in server.sample_skills.values()
            )
            return web.Response(
                text=f"""
            <html>
            <head><title>Vertice MCP Development Server</title></head>
            <body>
                <h1>🌟 Vertice MCP Development Server</h1>
                <p>Server is running on {server.host}:{server.port}</p>
                <h2>Available Endpoints:</h2>
                <ul>
                    <li><code>POST /mcp</code> - MCP JSON-RPC endpoint</li>
                    <li><code>GET /health</code> - Health check</li>
                </ul>
                <h2>Sample Skills Loaded:</h2>
                <ul>
                    {skills_html}
                </ul>
                <p><em>Generated with ❤️ for the evolution of collective AI</em></p>
            </body>
            </html>
            """,
                content_type="text/html",
            )

        return web.Response(status=404, text="Not found")

    # Start server
    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handle_http)

    print(f"📡 Server starting on http://{server.host}:{server.port}")
    print("📚 Sample skills loaded for testing")
    print(
        '🔗 Test with: curl -X POST http://localhost:3000/mcp -H \'Content-Type: application/json\' -d \'{"jsonrpc":"2.0","method":"prometheus/status","id":"test"}\''
    )
    print("🌐 Open http://localhost:3000 in your browser for more info")
    print("=" * 50)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, server.host, server.port)
    await site.start()

    print("✅ Development server is running!")
    print("Press Ctrl+C to stop...")

    try:
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development server...")
    finally:
        await runner.cleanup()
        print("👋 Development server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(run_development_server())
    except KeyboardInterrupt:
        print("\n👋 Development server stopped by user.")
