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
import logging

# Check if import works
try:
    from src.providers.vertice_router import get_router

    ROUTER_AVAILABLE = True
except ImportError:
    # Allow running without full context for basic health
    get_router = None
    ROUTER_AVAILABLE = False
    logger.warning("VerticeRouter not available. Trying direct VertexAIProvider.")

try:
    from src.providers.vertex_ai import VertexAIProvider

    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    logger.warning("VertexAIProvider not available.")

logger = logging.getLogger(__name__)
router = APIRouter()

print("DEBUG: Loading appapi/v1/chat.py - REVISION CHECK 2026-01-10-FIX-B")


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


async def stream_ai_sdk_response(messages: List[ChatMessage]):
    """
    Stream plain text for TextStreamChatTransport.
    """
    try:
        # internal message conversion
        internal_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Priority 1: Use Router if available
        if ROUTER_AVAILABLE and get_router:
            router_instance = get_router()
            async for chunk in router_instance.stream_chat(
                messages=internal_messages,
                complexity="MODERATE",
            ):
                yield chunk

        # Priority 2: Use VertexAIProvider directly (Fallback/Testing)
        elif VERTEX_AVAILABLE:
            provider = VertexAIProvider(model_name="pro")  # Gemini 2.5 Pro
            async for chunk in provider.stream_chat(messages=internal_messages):
                # Protocol formatting: 0:"chunk"
                yield f"0:{json.dumps(chunk)}\n"

        else:
            yield '0:"Error: No AI provider available (Router and VertexAI failed to load)."\n'
            return

    except Exception as e:
        logger.error(f"Error in text streaming: {e}")
        yield f"0:{json.dumps(f'Error: {str(e)}')}\n"


@router.post("/")
async def chat_endpoint(request: ChatRequest):
    """
    Vercel AI SDK compatible chat endpoint.
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
