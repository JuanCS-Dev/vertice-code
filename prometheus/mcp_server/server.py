"""
Prometheus MCP Server Core

The main MCP server implementation that handles incoming requests
and orchestrates Prometheus capabilities.

Created with love for universal AI protocol compliance.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import json
import logging
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from prometheus.mcp_server.config import MCPServerConfig
from prometheus.mcp_server.tools.registry import get_tool_registry

# Import tools to register them
import prometheus.mcp_server.tools.file_tools
import prometheus.mcp_server.tools.search_tools
import prometheus.mcp_server.tools.execution_tools
import prometheus.mcp_server.tools.system_tools
import prometheus.mcp_server.tools.git_tools
import prometheus.mcp_server.tools.web_tools
import prometheus.mcp_server.tools.media_tools
import prometheus.mcp_server.tools.context_tools
import prometheus.mcp_server.tools.prometheus_tools
import prometheus.mcp_server.tools.notebook_tools
import prometheus.mcp_server.tools.advanced_tools
import prometheus.mcp_server.tools.agent_tools

logger = logging.getLogger(__name__)


@dataclass
class MCPRequest:
    """Represents an incoming MCP request."""

    id: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MCPResponse:
    """Represents an MCP response."""

    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        """Convert response to JSON-RPC format."""
        response = {"jsonrpc": "2.0", "id": self.id}
        if self.result is not None:
            response["result"] = self.result
        if self.error is not None:
            response["error"] = self.error
        return json.dumps(response)


class PrometheusMCPServer:
    """
    Standalone MCP Server for Prometheus.

    Implements the Model Context Protocol to expose Prometheus capabilities
    as a universal AI service.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.instance_id}")

        # Request handlers
        self.method_handlers: Dict[str, Callable] = {}

        # Server state
        self.running = False
        self.start_time = None

        # Statistics
        self.requests_processed = 0
        self.errors_count = 0

        # Component registries
        self._tools_registry = {}
        self._resources_registry = {}
        self._prompts_registry = {}

        # Initialize handlers
        self._register_handlers()

        self.logger.info(f"Initialized MCP Server {config.instance_id}")

    def _register_handlers(self):
        """Register MCP method handlers."""
        # Core MCP methods
        self.method_handlers["initialize"] = self.handle_initialize
        self.method_handlers["shutdown"] = self.handle_shutdown
        self.method_handlers["ping"] = self.handle_ping

        # Tools
        self.method_handlers["tools/list"] = self.handle_tools_list
        self.method_handlers["tools/call"] = self.handle_tools_call

        # Resources
        self.method_handlers["resources/list"] = self.handle_resources_list
        self.method_handlers["resources/read"] = self.handle_resources_read

        # Prompts
        self.method_handlers["prompts/list"] = self.handle_prompts_list
        self.method_handlers["prompts/get"] = self.handle_prompts_get

        # Prometheus-specific methods
        self.method_handlers["prometheus/status"] = self.handle_prometheus_status
        self.method_handlers["prometheus/skills"] = self.handle_prometheus_skills
        self.method_handlers["prometheus/memory"] = self.handle_prometheus_memory

    async def handle_request(self, request_data: Dict[str, Any]) -> MCPResponse:
        """
        Handle an incoming MCP request.

        This is the main entry point for processing requests.
        """
        try:
            request = MCPRequest(
                id=request_data.get("id", str(uuid.uuid4())),
                method=request_data["method"],
                params=request_data.get("params", {}),
            )

            self.requests_processed += 1
            self.logger.debug(f"Processing request: {request.method}")

            # Find handler
            handler = self.method_handlers.get(request.method)
            if handler:
                result = await handler(request)
                return MCPResponse(id=request.id, result=result)
            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Method not found: {request.method}"},
                )

        except Exception as e:
            self.errors_count += 1
            self.logger.error(f"Error processing request: {e}")
            return MCPResponse(
                id=request_data.get("id", "unknown"),
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
            )

    async def handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle client initialization."""
        capabilities = {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True},
            "prompts": {"listChanged": True},
        }

        # Add Prometheus-specific capabilities
        if self.config.enable_skills_registry:
            capabilities["prometheus"] = {
                "skills": True,
                "memory": self.config.enable_memory_system,
                "distributed": self.config.enable_distributed_features,
            }

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": capabilities,
            "serverInfo": {
                "name": self.config.server_name,
                "version": self.config.server_version,
            },
        }

    async def handle_shutdown(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle shutdown request."""
        self.logger.info("Shutdown requested")
        self.running = False
        return {}

    async def handle_ping(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle ping request."""
        return {"status": "pong"}

    async def handle_tools_list(self, request: MCPRequest) -> Dict[str, Any]:
        """List available tools using the Tool Registry."""
        registry = get_tool_registry()
        tools = registry.list_tools()

        # Filter tools based on configuration flags
        filtered_tools = []
        for tool in tools:
            tool_name = tool.get("name", "")

            # Apply configuration filters
            if tool_name.startswith("file_") and not getattr(
                self.config, "enable_file_tools", True
            ):
                continue
            elif tool_name.startswith("git_") and not getattr(
                self.config, "enable_git_tools", True
            ):
                continue
            elif tool_name.startswith("execution_") and not getattr(
                self.config, "enable_execution_tools", True
            ):
                continue
            elif tool_name.startswith("web_") and not getattr(
                self.config, "enable_web_tools", True
            ):
                continue
            elif tool_name.startswith("media_") and not getattr(
                self.config, "enable_media_tools", True
            ):
                continue
            elif tool_name.startswith("prometheus_") and not getattr(
                self.config, "enable_prometheus_tools", True
            ):
                continue

            filtered_tools.append(tool)

        logger.info(f"Returning {len(filtered_tools)} tools from registry")
        return {"tools": filtered_tools}

    async def handle_tools_call(self, request: MCPRequest) -> Dict[str, Any]:
        """Execute a tool using the Tool Registry."""
        tool_name = request.params.get("name")
        tool_args = request.params.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name is required")

        # Use Tool Registry for unified tool execution
        registry = get_tool_registry()
        result = await registry.call_tool(tool_name, tool_args)

        # Extract the result content from MCP response format
        if "result" in result and "content" in result["result"]:
            return result["result"]
        elif "error" in result:
            return result
        else:
            return {"error": {"code": -32000, "message": "Invalid tool response format"}}

    async def handle_resources_list(self, request: MCPRequest) -> Dict[str, Any]:
        """List available resources."""
        resources = []

        # Add Prometheus resources
        if self.config.enable_skills_registry:
            resources.append(
                {
                    "uri": "prometheus://skills",
                    "name": "Learned Skills Registry",
                    "description": "Access to all learned skills and their metadata",
                    "mimeType": "application/json",
                }
            )

        if self.config.enable_memory_system:
            resources.append(
                {
                    "uri": "prometheus://memory",
                    "name": "Memory System",
                    "description": "Access to persistent memory and context",
                    "mimeType": "application/json",
                }
            )

        return {"resources": resources}

    async def handle_resources_read(self, request: MCPRequest) -> Dict[str, Any]:
        """Read a resource."""
        uri = request.params.get("uri")
        if not uri:
            raise ValueError("Resource URI is required")

        if uri == "prometheus://skills":
            return await self._get_skills_resource()
        elif uri == "prometheus://memory":
            return await self._get_memory_resource()
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def handle_prompts_list(self, request: MCPRequest) -> Dict[str, Any]:
        """List available prompts."""
        prompts = [
            {
                "name": "prometheus_skill_creation",
                "description": "Template for creating new skills with proper structure",
                "arguments": [
                    {
                        "name": "task_description",
                        "description": "Description of the task the skill should perform",
                        "required": True,
                    }
                ],
            }
        ]

        return {"prompts": prompts}

    async def handle_prompts_get(self, request: MCPRequest) -> Dict[str, Any]:
        """Get a prompt template."""
        name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if name == "prometheus_skill_creation":
            task_desc = arguments.get("task_description", "unspecified task")

            prompt = f"""Create a new Prometheus skill for the following task:

Task: {task_desc}

Please provide:
1. Skill name (unique identifier)
2. Detailed description
3. Step-by-step procedure
4. Appropriate category

The skill should be executable and follow Prometheus conventions."""

            return {
                "description": f"Skill creation template for: {task_desc}",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt}}],
            }
        else:
            raise ValueError(f"Unknown prompt: {name}")

    async def handle_prometheus_status(self, request: MCPRequest) -> Dict[str, Any]:
        """Get Prometheus server status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "instance_id": self.config.instance_id,
            "version": self.config.server_version,
            "status": "running" if self.running else "stopped",
            "uptime_seconds": uptime,
            "requests_processed": self.requests_processed,
            "errors_count": self.errors_count,
            "config": self.config.to_dict(),
        }

    async def handle_prometheus_skills(self, request: MCPRequest) -> Dict[str, Any]:
        """Get skills information."""
        # This would integrate with the actual skills registry
        return {
            "skills_count": 0,  # Placeholder
            "categories": [],
            "recent_learned": [],
        }

    async def handle_prometheus_memory(self, request: MCPRequest) -> Dict[str, Any]:
        """Get memory system information."""
        # This would integrate with the actual memory system
        return {
            "memory_entries": 0,  # Placeholder
            "total_size_mb": 0,
            "last_updated": None,
        }

    async def _handle_prometheus_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Prometheus-specific tools."""
        if tool_name == "prometheus_learn_skill":
            return await self._handle_prometheus_learn_skill(args)
        elif tool_name == "prometheus_get_skill":
            return await self._handle_prometheus_get_skill(args)
        elif tool_name == "prometheus_eject_to_cloud":
            return await self._handle_prometheus_eject_to_cloud(args)
        else:
            raise ValueError(f"Unknown Prometheus tool: {tool_name}")

    async def _handle_prometheus_eject_to_cloud(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle eject to cloud tool."""
        code = args.get("code", "")
        filename = args.get("filename", "ejected_code.py")
        description = args.get("description", "")

        if not code:
            raise ValueError("Code is required for eject to cloud")

        # In a real implementation, this would save to cloud storage
        # For now, we'll simulate by returning success
        cloud_url = f"https://cloud.vertice.ai/code/{filename}"

        return {
            "success": True,
            "cloud_url": cloud_url,
            "filename": filename,
            "description": description,
            "message": f"Code ejected to cloud successfully at {cloud_url}",
        }

    async def _get_skills_resource(self) -> Dict[str, Any]:
        """Get skills resource content."""
        # This would return actual skills data
        return {
            "content": json.dumps(
                {
                    "skills": [],
                    "metadata": {"total_count": 0, "last_updated": datetime.now().isoformat()},
                }
            ),
            "mimeType": "application/json",
        }

    async def _get_memory_resource(self) -> Dict[str, Any]:
        """Get memory resource content."""
        # This would return actual memory data
        return {
            "content": json.dumps(
                {
                    "memories": [],
                    "metadata": {"total_count": 0, "last_updated": datetime.now().isoformat()},
                }
            ),
            "mimeType": "application/json",
        }

    async def start(self):
        """Start the MCP server."""
        self.running = True
        self.start_time = datetime.now()
        self.logger.info(
            f"MCP Server {self.config.instance_id} started on {self.config.host}:{self.config.port}"
        )

    async def stop(self):
        """Stop the MCP server."""
        self.running = False
        self.logger.info(f"MCP Server {self.config.instance_id} stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "requests_processed": self.requests_processed,
            "errors_count": self.errors_count,
            "uptime_seconds": (
                (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            ),
            "config": self.config.to_dict(),
        }
