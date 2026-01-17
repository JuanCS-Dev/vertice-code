"""
Agent Execution API - Execute agents via MCP Server
WebSocket streaming endpoint for real-time agent execution

Features:
- WebSocket streaming for agent execution progress
- MCP server integration for tool access
- Agent selection and routing
- Real-time status updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any, Optional
import json
import logging
import uuid

from app.integrations.mcp_client import get_mcp_client, CircuitBreakerOpenException

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentExecutionRequest:
    """Request model for agent execution."""

    def __init__(
        self, task: str, agent: str = "architect", context: Optional[Dict[str, Any]] = None
    ):
        self.task = task
        self.agent = agent
        self.context = context or {}


@router.websocket("/execute")
async def execute_agent_websocket(
    websocket: WebSocket,
    # current_user: FirebaseUser = Depends(get_current_user)  # TODO: Enable when auth is ready
):
    """
    Execute agent via WebSocket with real-time streaming.

    Expected message format:
    {
        "type": "execute",
        "data": {
            "task": "Analyze the codebase",
            "agent": "architect",  // optional, defaults to "architect"
            "context": {...}       // optional context
        }
    }

    Streaming response format:
    {
        "type": "progress",
        "data": {
            "stage": "analyzing",
            "message": "Reading files...",
            "progress": 0.3
        }
    }
    {
        "type": "result",
        "data": {
            "success": true,
            "result": "...",
            "execution_time": 5.2
        }
    }
    """
    await websocket.accept()
    logger.info("Agent execution WebSocket connection established")

    try:
        # Get MCP client
        mcp_client = await get_mcp_client()
        await mcp_client.start()

        while True:
            # Receive execution request
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") != "execute":
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": f"Unknown message type: {message.get('type')}. Expected 'execute'.",
                    }
                )
                continue

            execution_data = message.get("data", {})
            task = execution_data.get("task")
            agent_name = execution_data.get("agent", "architect")
            context = execution_data.get("context", {})

            if not task:
                await websocket.send_json({"type": "error", "data": "Task is required"})
                continue

            # Start agent execution
            execution_id = f"exec-{uuid.uuid4().hex[:8]}"

            try:
                # Send initial progress
                await websocket.send_json(
                    {
                        "type": "progress",
                        "data": {
                            "execution_id": execution_id,
                            "stage": "initializing",
                            "message": f"Starting {agent_name} agent...",
                            "progress": 0.0,
                        },
                    }
                )

                # Map agent names to MCP tool names
                agent_tool_map = {
                    "architect": "execute_with_architect",
                    "executor": "execute_with_executor",
                    "reviewer": "execute_with_reviewer",
                    "planner": "execute_with_planner",
                    "researcher": "execute_with_researcher",
                    "prometheus": "prometheus_execute",
                }

                tool_name = agent_tool_map.get(agent_name, "prometheus_execute")

                # Prepare tool arguments
                tool_args = {"task": task, **context}

                # Progress: Calling MCP tool
                await websocket.send_json(
                    {
                        "type": "progress",
                        "data": {
                            "execution_id": execution_id,
                            "stage": "executing",
                            "message": f"Executing via {tool_name}...",
                            "progress": 0.3,
                        },
                    }
                )

                # Call the agent tool via MCP
                response = await mcp_client.call_tool(tool_name, tool_args)

                # Progress: Processing result
                await websocket.send_json(
                    {
                        "type": "progress",
                        "data": {
                            "execution_id": execution_id,
                            "stage": "processing",
                            "message": "Processing results...",
                            "progress": 0.7,
                        },
                    }
                )

                # Extract result
                if "result" in response and response["result"]:
                    result_data = response["result"]
                    if isinstance(result_data, dict) and "content" in result_data:
                        # MCP tool response format
                        content = result_data["content"]
                        if isinstance(content, list) and content:
                            result_text = (
                                content[0].get("text", "")
                                if isinstance(content[0], dict)
                                else str(content[0])
                            )
                        else:
                            result_text = str(result_data)
                    else:
                        result_text = str(result_data)

                    # Send final result
                    await websocket.send_json(
                        {
                            "type": "result",
                            "data": {
                                "execution_id": execution_id,
                                "success": True,
                                "result": result_text,
                                "agent": agent_name,
                                "tool_used": tool_name,
                            },
                        }
                    )

                elif "error" in response:
                    # Send error result
                    await websocket.send_json(
                        {
                            "type": "result",
                            "data": {
                                "execution_id": execution_id,
                                "success": False,
                                "error": response["error"].get("message", "Unknown error"),
                                "agent": agent_name,
                                "tool_used": tool_name,
                            },
                        }
                    )
                else:
                    # Unexpected response format
                    await websocket.send_json(
                        {
                            "type": "result",
                            "data": {
                                "execution_id": execution_id,
                                "success": False,
                                "error": "Unexpected response format from MCP server",
                                "raw_response": response,
                            },
                        }
                    )

            except CircuitBreakerOpenException as e:
                logger.warning(f"Circuit breaker open during agent execution: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": "MCP server temporarily unavailable. Please try again later.",
                    }
                )

            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                await websocket.send_json(
                    {
                        "type": "result",
                        "data": {
                            "execution_id": execution_id,
                            "success": False,
                            "error": f"Agent execution failed: {str(e)}",
                        },
                    }
                )

    except WebSocketDisconnect:
        logger.info("Agent execution WebSocket connection closed")
    except Exception as e:
        logger.error(f"Agent execution WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "data": f"WebSocket error: {str(e)}"})
        except:
            pass  # Connection might be closed
    finally:
        # Cleanup MCP client
        try:
            if "mcp_client" in locals():
                await mcp_client.stop()
        except Exception as e:
            logger.warning(f"Error stopping MCP client: {e}")


@router.post("/execute")
async def execute_agent_http(
    request: Dict[str, Any],
    # current_user: FirebaseUser = Depends(get_current_user)  # TODO: Enable when auth is ready
):
    """
    Execute agent via HTTP (synchronous).

    Request body:
    {
        "task": "Analyze the codebase",
        "agent": "architect",  // optional
        "context": {...}       // optional
    }

    Response:
    {
        "execution_id": "exec-12345678",
        "success": true,
        "result": "...",
        "execution_time": 5.2
    }
    """
    task = request.get("task")
    agent_name = request.get("agent", "architect")
    context = request.get("context", {})

    if not task:
        raise HTTPException(status_code=400, detail="Task is required")

    execution_id = f"exec-{uuid.uuid4().hex[:8]}"

    try:
        # Get MCP client
        mcp_client = await get_mcp_client()
        await mcp_client.start()

        # Map agent names to MCP tool names
        agent_tool_map = {
            "architect": "execute_with_architect",
            "executor": "execute_with_executor",
            "reviewer": "execute_with_reviewer",
            "planner": "execute_with_planner",
            "researcher": "execute_with_researcher",
            "prometheus": "prometheus_execute",
        }

        tool_name = agent_tool_map.get(agent_name, "prometheus_execute")

        # Prepare tool arguments
        tool_args = {"task": task, **context}

        # Call the agent tool via MCP
        response = await mcp_client.call_tool(tool_name, tool_args)

        # Extract result
        if "result" in response and response["result"]:
            result_data = response["result"]
            if isinstance(result_data, dict) and "content" in result_data:
                # MCP tool response format
                content = result_data["content"]
                if isinstance(content, list) and content:
                    result_text = (
                        content[0].get("text", "")
                        if isinstance(content[0], dict)
                        else str(content[0])
                    )
                else:
                    result_text = str(result_data)
            else:
                result_text = str(result_data)

            return {
                "execution_id": execution_id,
                "success": True,
                "result": result_text,
                "agent": agent_name,
                "tool_used": tool_name,
            }

        elif "error" in response:
            return {
                "execution_id": execution_id,
                "success": False,
                "error": response["error"].get("message", "Unknown error"),
                "agent": agent_name,
                "tool_used": tool_name,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Unexpected response format from MCP server"
            )

    except CircuitBreakerOpenException as e:
        logger.warning(f"Circuit breaker open during agent execution: {e}")
        raise HTTPException(status_code=503, detail="MCP server temporarily unavailable")
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    finally:
        # Cleanup MCP client
        try:
            if "mcp_client" in locals():
                await mcp_client.stop()
        except Exception as e:
            logger.warning(f"Error stopping MCP client: {e}")


@router.get("/agents")
async def list_available_agents():
    """
    List available agents that can be executed.

    Returns mapping of agent names to their capabilities.
    """
    try:
        mcp_client = await get_mcp_client()
        await mcp_client.start()

        # Get available tools from MCP server
        tools_response = await mcp_client.list_tools()

        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]

            # Filter agent-related tools
            agent_tools = [
                tool
                for tool in tools
                if tool.get("name", "").startswith("execute_with_")
                or tool.get("name") in ["prometheus_execute"]
            ]

            # Map to agent descriptions
            agents = {
                "architect": {
                    "name": "Architect",
                    "description": "Design and planning agent for complex tasks",
                    "capabilities": ["analysis", "design", "planning"],
                    "tool": "execute_with_architect",
                },
                "executor": {
                    "name": "Executor",
                    "description": "Implementation agent for executing plans",
                    "capabilities": ["coding", "file_operations", "execution"],
                    "tool": "execute_with_executor",
                },
                "prometheus": {
                    "name": "Prometheus",
                    "description": "Self-evolving meta-agent with full capabilities",
                    "capabilities": ["all"],
                    "tool": "prometheus_execute",
                },
            }

            return {"agents": agents, "mcp_tools_available": len(agent_tools)}
        else:
            return {"agents": {}, "error": "Could not retrieve tools from MCP server"}

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return {"agents": {}, "error": str(e)}
    finally:
        try:
            if "mcp_client" in locals():
                await mcp_client.stop()
        except Exception as e:
            logger.warning(f"Error stopping MCP client: {e}")
