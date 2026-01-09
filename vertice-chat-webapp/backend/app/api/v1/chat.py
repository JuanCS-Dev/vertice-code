"""
Chat API Endpoint - Vercel AI SDK Data Stream Protocol Implementation
Reference: https://sdk.vercel.ai/docs/reference/stream-helpers/stream-data
"""

import json
import asyncio
import logging
import time
from typing import List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "claude-3-5-sonnet"
    stream: bool = True

async def generate_data_stream(messages: List[Message]) -> AsyncGenerator[str, None]:
    """
    Generates a stream compliant with Vercel AI SDK Data Stream Protocol.
    Protocol:
    - 0: Text part
    - 2: Data part (Tool calls)
    - 3: Error part
    - d: Finish message
    """
    if not messages:
        yield '0:"No messages received."\n'
        return

    last_message = messages[-1].content
    
    # 1. Acknowledge (Thinking phase)
    yield '0:"Analyzing protocol..."\n'
    await asyncio.sleep(0.3)
    yield '0:"\n"\n'

    # 2. Simulate Tool Use (if requested)
    if any(keyword in last_message.lower() for keyword in ["artifact", "code", "ui", "component"]):
        yield '0:"Initiating manifestation sequence...\n"\n'
        
        # Simulate Tool Call (Protocol 2)
        tool_call_id = "call_" + str(int(time.time()))
        tool_call = {
            "toolCall": {
                "toolName": "create_artifact",
                "toolCallId": tool_call_id,
                "args": {"title": "Manifested Component", "language": "tsx"}
            }
        }
        yield f'2:{json.dumps([tool_call])}\n'
        
        await asyncio.sleep(0.8)
        yield '0:"Artifact generated and synced to the project nodes.\n"\n'
    
    # 3. Standard Response Streaming
    response_text = f"Sovereign node verified. I have received your request regarding: '{last_message[:50]}...'. Proceeding with high-fidelity synthesis."
    
    for word in response_text.split(" "):
        yield f'0:{json.dumps(word + " ")}\n'
        await asyncio.sleep(0.03)
    
    # 4. Finish Metadata
    finish_data = {
        "finishReason": "stop",
        "usage": {
            "promptTokens": 120,
            "completionTokens": len(response_text.split(" ")),
        }
    }
    yield f'd:{json.dumps(finish_data)}\n'

@router.post("/")
async def chat_stream(request: ChatRequest):
    """
    Chat endpoint compatible with useChat hook.
    """
    logger.info(f"Chat request: {len(request.messages)} messages using {request.model}")
    
    return StreamingResponse(
        generate_data_stream(request.messages),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Vercel-AI-Data-Stream": "v1",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )