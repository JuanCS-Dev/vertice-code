"""
Terminal API router with WebSocket support for MCP integration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import logging
import os

from app.integrations.mcp_client import MCPClient, CircuitBreakerOpenException

logger = logging.getLogger(__name__)

router = APIRouter()

# Global MCP client instance
mcp_client: MCPClient


async def get_terminal_mcp_client() -> MCPClient:
    """Get MCP client for terminal operations."""
    global mcp_client
    if mcp_client is None:
        # Get MCP server URL from environment or use default
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        mcp_client = MCPClient(base_url=mcp_server_url)
        await mcp_client.start()
    return mcp_client


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

                # Handle MCP request via HTTP client
                try:
                    client = await get_terminal_mcp_client()
                    response_data = await client.call_mcp_method(
                        mcp_request["method"], mcp_request.get("params", {})
                    )

                    # Send response back to client
                    if "result" in response_data:
                        # Extract tool result content
                        result = response_data["result"]
                        if isinstance(result, dict) and "content" in result:
                            # MCP tool response format
                            content = result["content"]
                            if isinstance(content, list) and content:
                                text_content = (
                                    content[0].get("text", "")
                                    if isinstance(content[0], dict)
                                    else str(content[0])
                                )
                                await websocket.send_json({"type": "output", "data": text_content})
                            else:
                                await websocket.send_json({"type": "output", "data": str(result)})
                        else:
                            # Other MCP responses
                            await websocket.send_json({"type": "output", "data": str(result)})
                    elif "error" in response_data:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "data": response_data["error"].get("message", "Unknown error"),
                            }
                        )

                except CircuitBreakerOpenException as e:
                    logger.warning(f"Circuit breaker open: {e}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": "MCP server temporarily unavailable. Please try again later.",
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
