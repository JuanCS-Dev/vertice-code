"""
Vercel AI SDK Compatible Chat Endpoint
========================================

Implements the Data Stream Protocol for compatibility with useChat hook.
Supports text streaming and tool calls in Vercel AI SDK format.

Protocol:
- 0:"text" - Text chunks
- 2:{json} - Tool calls/data
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging

from ...core.providers.vertice_router import get_router

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """Vercel AI SDK message format."""

    role: str
    content: str
    id: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Vercel AI SDK chat request."""

    messages: List[ChatMessage]
    stream: bool = True
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call structure for protocol."""

    toolCallId: str
    toolName: str
    args: Dict[str, Any]


async def stream_ai_sdk_response(messages: List[ChatMessage]) -> AsyncIterator[str]:
    """
    Stream response in Vercel AI SDK Data Stream Protocol format.

    Protocol format:
    - 0:"text_chunk"\n - Text streaming
    - 2:{json_data}\n - Tool calls and other data
    - 3:{json_data}\n - Tool results
    """
    try:
        # Get the router and prepare for streaming
        router = get_router()

        # Convert messages to internal format
        internal_messages = []
        for msg in messages:
            internal_messages.append({"role": msg.role, "content": msg.content})

        # Create streaming context with tools if available
        tools = None
        if messages and messages[-1].function_call:
            # Handle function calling
            pass

        # Stream the response
        full_response = ""
        tool_calls = []

        async for chunk in router.stream_chat(
            messages=internal_messages,
            complexity="MODERATE",  # Default complexity
            speed="NORMAL",  # Default speed
        ):
            if chunk.startswith("[TOOL_CALL:"):
                # Parse tool call from chunk
                try:
                    tool_data = json.loads(chunk[11:-1])  # Remove [TOOL_CALL: and ]
                    tool_call = ToolCall(
                        toolCallId=f"call_{len(tool_calls)}",
                        toolName=tool_data.get("name", "unknown"),
                        args=tool_data.get("arguments", {}),
                    )
                    tool_calls.append(tool_call)

                    # Stream tool call in protocol format
                    yield f"2:{json.dumps({'toolCall': tool_call.dict()})}\n"
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool call: {chunk}")
                    # Stream as regular text
                    yield f"0:{json.dumps(chunk)}\n"
            else:
                # Regular text chunk
                full_response += chunk
                yield f"0:{json.dumps(chunk)}\n"

        # If we had tool calls, stream their results
        for i, tool_call in enumerate(tool_calls):
            # Simulate tool execution (in real implementation, this would call actual tools)
            tool_result = {
                "toolCallId": tool_call.toolCallId,
                "result": f"Executed {tool_call.toolName} with args {tool_call.args}",
            }
            yield f"3:{json.dumps({'toolResult': tool_result})}\n"

        # Final response data
        final_data = {
            "finishReason": "stop",
            "usage": {
                "promptTokens": len(str(internal_messages)),
                "completionTokens": len(full_response),
                "totalTokens": len(str(internal_messages)) + len(full_response),
            },
        }
        yield f"d:{json.dumps(final_data)}\n"

    except Exception as e:
        logger.error(f"Error in AI SDK streaming: {e}")
        error_data = {"finishReason": "error", "error": str(e)}
        yield f"e:{json.dumps(error_data)}\n"


@router.post("/")
async def chat_endpoint(request: ChatRequest):
    """
    Vercel AI SDK compatible chat endpoint.

    Returns streaming response in Data Stream Protocol format.
    Compatible with useChat hook from ai/react.
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages are required")

        return StreamingResponse(
            stream_ai_sdk_response(request.messages),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream-ui")
async def stream_ui_endpoint(request: ChatRequest):
    """
    Experimental: Generative UI endpoint.

    Returns React components instead of text.
    This is a placeholder for Phase 2 implementation.
    """

    # Placeholder for streamUI functionality
    # In Phase 2, this will return ReactNode streams
    async def stream_ui():
        yield f"0:{json.dumps('Generative UI not yet implemented')}\n"
        yield f"d:{json.dumps({'finishReason': 'stop'})}\n"

    return StreamingResponse(stream_ui(), media_type="text/plain; charset=utf-8")
