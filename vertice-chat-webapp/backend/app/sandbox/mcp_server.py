"""
MCP Server for Secure Code Execution

Provides tools for running Python code in sandboxed environments.
Integrates with the SandboxExecutor for secure execution.

References:
- MCP Specification: https://modelcontextprotocol.io/specification/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Sequence
import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

from app.sandbox.executor import SandboxExecutor, SandboxConfig

logger = logging.getLogger(__name__)


class CodeExecutionServer:
    """
    MCP Server that provides secure code execution capabilities
    """

    def __init__(self) -> None:
        self.server = Server("vertice-code-executor")
        self.executor = self._create_executor()

    def _create_executor(self) -> SandboxExecutor:
        """Create sandbox executor with secure configuration"""
        config = SandboxConfig(
            allowed_read_dirs=["/tmp/workspace"],
            allowed_write_dirs=["/tmp/workspace"],
            allowed_hosts=[],  # No network access by default
            block_network=True,
            max_execution_time=30,
            max_memory_mb=512,
            max_cpu_percent=50,
        )
        return SandboxExecutor(config)

    async def handle_execute_code(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """
        Execute Python code in sandbox

        Args:
            arguments: Tool arguments containing 'code' and optional parameters

        Returns:
            Execution results as text content
        """
        try:
            code = arguments.get("code", "")
            if not code:
                return [types.TextContent(type="text", text="Error: No code provided")]

            timeout = arguments.get("timeout", 30)
            working_dir = arguments.get("working_dir")

            # Execute code in sandbox
            result = await self.executor.execute_python(
                code=code, working_dir=working_dir, timeout=float(timeout)
            )

            # Format response
            response_parts = []

            if result.stdout:
                response_parts.append(f"STDOUT:\n{result.stdout}")

            if result.stderr:
                response_parts.append(f"STDERR:\n{result.stderr}")

            response_parts.append(f"Exit Code: {result.exit_code}")
            response_parts.append(".2f")

            if result.error:
                response_parts.append(f"Error: {result.error}")

            full_response = "\n\n".join(response_parts)

            return [types.TextContent(type="text", text=full_response)]

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return [types.TextContent(type="text", text=f"Execution error: {str(e)}")]

    async def handle_list_directory(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """
        List directory contents (read-only, sandboxed)

        Args:
            arguments: Tool arguments containing 'path'

        Returns:
            Directory listing as text content
        """
        try:
            path = arguments.get("path", "/tmp/workspace")

            # Basic security: only allow access to allowed directories
            allowed = False
            for allowed_dir in self.executor.config.allowed_read_dirs:
                if path.startswith(allowed_dir):
                    allowed = True
                    break

            if not allowed:
                return [
                    types.TextContent(
                        type="text", text=f"Access denied: {path} not in allowed directories"
                    )
                ]

            if not os.path.exists(path):
                return [types.TextContent(type="text", text=f"Path does not exist: {path}")]

            if not os.path.isdir(path):
                return [types.TextContent(type="text", text=f"Not a directory: {path}")]

            # List directory contents
            try:
                items = os.listdir(path)
                files = []
                dirs = []

                for item in sorted(items):
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        dirs.append(f"{item}/")
                    else:
                        files.append(item)

                response = f"Contents of {path}:\n\n"
                if dirs:
                    response += "Directories:\n" + "\n".join(f"  {d}" for d in dirs) + "\n\n"
                if files:
                    response += "Files:\n" + "\n".join(f"  {f}" for f in files)

                return [types.TextContent(type="text", text=response)]

            except PermissionError:
                return [types.TextContent(type="text", text=f"Permission denied: {path}")]

        except Exception as e:
            logger.error(f"Directory listing failed: {e}")
            return [types.TextContent(type="text", text=f"Listing error: {str(e)}")]

    async def setup_tools(self) -> None:
        """Setup available tools"""

        @self.server.list_tools()  # type: ignore
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="execute_python",
                    description="Execute Python code in a secure sandboxed environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"},
                            "timeout": {
                                "type": "number",
                                "description": "Execution timeout in seconds (default: 30)",
                                "default": 30,
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory for execution (optional)",
                            },
                        },
                        "required": ["code"],
                    },
                ),
                types.Tool(
                    name="list_directory",
                    description="List contents of a directory (read-only, sandboxed)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path to list"}
                        },
                        "required": ["path"],
                    },
                ),
            ]

        @self.server.call_tool()  # type: ignore
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent]:
            """Handle tool calls"""
            if name == "execute_python":
                return await self.handle_execute_code(arguments)
            elif name == "list_directory":
                return await self.handle_list_directory(arguments)
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    async def run(self) -> None:
        """Run the MCP server"""
        await self.setup_tools()

        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            # Initialize with None for now (will be fixed when MCP SDK is updated)
            await self.server.run(
                read_stream,
                write_stream,
                None,  # type: ignore
            )


# For running as standalone MCP server
if __name__ == "__main__":
    import os

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run the server
    server = CodeExecutionServer()
    asyncio.run(server.run())
