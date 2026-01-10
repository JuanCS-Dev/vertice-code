"""
Vercel AI SDK Compatible Chat Endpoint (VERTEX AI REAL)
========================================
DEBUG: Loading vertice-chat-webapp/backend/app/api/v1/chat.py - REVISION 2026-01-10-REAL-AI
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part, SafetySetting

logger = logging.getLogger(__name__)
router = APIRouter()

print("DEBUG: Loading REAL VERTEX AI chat.py")


class ChatRequest(BaseModel):
    messages: List[Any]
    stream: bool = True


def convert_messages(messages):
    vertex_history = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")

        if not content:
            continue

        if role == "user":
            vertex_history.append(Content(role="user", parts=[Part.from_text(content)]))
        elif role == "assistant":
            vertex_history.append(Content(role="model", parts=[Part.from_text(content)]))
    return vertex_history


async def stream_generator(messages_payload):
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")

        # Updated to Gemini 1.5 Pro (Vertex AI / Stable Model)
        model = GenerativeModel("gemini-1.5-pro")

        # Split history and last message
        history = convert_messages(messages_payload[:-1])
        last_message_content = messages_payload[-1].get("content")

        chat = model.start_chat(history=history)

        # Send message with streaming
        response_stream = await chat.send_message_async(last_message_content, stream=True)

        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    # Vercel Data Stream Protocol: 0:"json_encoded_string"\n
                    yield f"0:{json.dumps(text_content)}\n"
            except ValueError:
                # Handle safety blocks or empty content
                continue

    except Exception as e:
        error_msg = f" Vertice System Failure: {str(e)}"
        logger.error(error_msg)
        yield f"0:{json.dumps(error_msg)}\n"


@router.post("/")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(stream_generator(request.messages), media_type="text/plain")
