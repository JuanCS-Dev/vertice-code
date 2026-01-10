"""
Vercel AI SDK Compatible Chat Endpoint (VERTEX AI REAL)
========================================
DEBUG: Loading vertice-chat-webapp/backend/app/api/v1/chat.py - REVISION 2026-01-10-REAL-AI
"""

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part, SafetySetting
import firebase_admin
from firebase_admin import auth, credentials

logger = logging.getLogger(__name__)
router = APIRouter()

print("DEBUG: Loading REAL VERTEX AI chat.py")

# Initialize Firebase Admin SDK for authentication
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)


class ChatRequest(BaseModel):
    messages: List[Any]
    stream: bool = True
    model: str = "gemini-2.5-pro"


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


async def stream_generator(request: ChatRequest):
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")

        # Updated to Gemini 2.5 Pro (Vertex AI / 2026 Standard)
        model = GenerativeModel(request.model)

        # Split history and last message
        history = convert_messages(request.messages[:-1])
        last_message_content = request.messages[-1].get("content")

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
async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    # Validate Firebase Auth token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["uid"]
        logger.info(f"Authenticated request from user {user_id}")
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return StreamingResponse(stream_generator(request), media_type="text/plain")
