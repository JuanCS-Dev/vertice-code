"""
Terminal API router with WebSocket support for MCP integration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


# Mock MCP server for terminal endpoint
class MockMCPServer:
    """Mock MCP server for testing and development."""

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request with mock response."""
        method = request.get("method", "")
        request_id = request.get("id", "mock")

        if method == "tools/list":
            # Return mock tools list
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {"name": "execute_shell", "description": "Execute shell commands"},
                        {"name": "read_file", "description": "Read file contents"},
                        {"name": "write_file", "description": "Write to files"},
                    ]
                },
                "id": request_id,
            }
        else:
            # Generic mock response
            return {
                "jsonrpc": "2.0",
                "result": {"output": "Mock MCP server response", "status": "success"},
                "id": request_id,
            }


# Global MCP server instance
mcp_server = MockMCPServer()


@router.websocket("/")
async def terminal_websocket(websocket: WebSocket):
    """WebSocket endpoint for terminal operations via MCP."""

    await websocket.accept()
    logger.info("Terminal WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "command":
                command = message.get("data", "")

                # Check if it's an eject command
                if command.startswith("eject "):
                    # Parse eject command: eject <filename> <description>
                    parts = command.split(" ", 2)
                    filename = parts[1] if len(parts) > 1 else "ejected_code.py"
                    description = parts[2] if len(parts) > 2 else ""

                    # For demo, use a simple code example
                    demo_code = 'print("Hello from ejected code!")'

                    mcp_request = {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "prometheus_eject_to_cloud",
                            "arguments": {
                                "code": demo_code,
                                "filename": filename,
                                "description": description,
                            },
                        },
                        "id": f"terminal-{id(message)}",
                    }
                else:
                    # Create MCP request for command execution
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "execute_command", "arguments": {"command": command}},
                        "id": f"terminal-{id(message)}",
                    }

                # Handle MCP request
                try:
                    response = await mcp_server.handle_request(mcp_request)
                    response_data = response  # Already a dict from mock server

                    # Send response back to client
                    if "result" in response_data:
                        await websocket.send_json(
                            {"type": "output", "data": response_data["result"].get("output", "")}
                        )
                    elif "error" in response_data:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "data": response_data["error"].get("message", "Unknown error"),
                            }
                        )

                except Exception as e:
                    logger.error(f"Error executing command via MCP: {e}")
                    await websocket.send_json(
                        {"type": "error", "data": f"Failed to execute command: {str(e)}"}
                    )

            else:
                # Unknown message type
                await websocket.send_json(
                    {"type": "error", "data": f"Unknown message type: {message.get('type')}"}
                )

    except WebSocketDisconnect:
        logger.info("Terminal WebSocket connection closed")
    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "data": f"WebSocket error: {str(e)}"})
        except:
            pass  # Connection might be closed


@router.get("/")
async def terminal_root() -> Dict[str, str]:
    """Terminal API root endpoint"""
    return {"message": "Terminal API with WebSocket support"}
