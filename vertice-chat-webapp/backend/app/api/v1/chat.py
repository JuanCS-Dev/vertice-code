"""
Vercel AI SDK Compatible Chat Endpoint (VERTEX AI - PRODUCTION)
================================================================
Implements Vercel AI SDK Data Stream Protocol for @ai-sdk/react compatibility.
Reference: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

REVISION: 2026-01-13-STREAM-PROTOCOL-FIX
"""

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Any, Optional
import asyncio
import logging
import os
import traceback

import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
import firebase_admin
from firebase_admin import auth, credentials

from app.core.stream_protocol import (
    format_text_chunk,
    format_finish,
    format_error,
    create_error_stream,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
STREAM_TIMEOUT_SECONDS = 120
DEFAULT_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-1.5-flash"

logger.info("Loading Vercel AI SDK compatible chat.py (PRODUCTION)")


# Initialize Firebase Admin SDK for authentication (once)
def _init_firebase():
    if firebase_admin._apps:
        return
    
    firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if firebase_key:
        import json
        cred = credentials.Certificate(json.loads(firebase_key))
    else:
        # Fallback to Application Default Credentials (GCP environments)
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred)


try:
    _init_firebase()
except Exception as e:
    logger.warning(f"Firebase init failed (may work later): {e}")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    messages: List[Any] = Field(..., min_length=1, description="Chat messages array")
    stream: bool = Field(default=True, description="Enable streaming response")
    model: str = Field(default=DEFAULT_MODEL, description="Model to use")


def convert_messages_to_vertex(messages: List[Any]) -> List[Content]:
    """
    Convert frontend message format to Vertex AI Content format.
    
    Handles: user, assistant, system roles
    """
    vertex_history = []
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if not content or not content.strip():
            continue
        
        # Map roles: frontend uses 'assistant', Vertex uses 'model'
        if role == "user":
            vertex_history.append(Content(role="user", parts=[Part.from_text(content)]))
        elif role in ("assistant", "model"):
            vertex_history.append(Content(role="model", parts=[Part.from_text(content)]))
        elif role == "system":
            # Prepend system message to first user message or as user context
            vertex_history.append(Content(role="user", parts=[Part.from_text(f"[System]: {content}")]))
    
    return vertex_history


async def stream_vertex_response(request: ChatRequest):
    """
    Stream Vertex AI response using Vercel AI SDK Data Stream Protocol.
    
    Protocol format:
    - 0:"text" for text chunks
    - d:{"finishReason":"stop"} for completion
    - 3:"error" for errors
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    
    # Force valid location (never use 'global')
    if location == "global":
        location = "us-central1"
    
    try:
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        logger.info(f"Vertex AI initialized: project={project_id}, location={location}")
        
    except Exception as init_err:
        logger.error(f"Vertex AI init failed: {init_err}")
        yield format_error(f"Failed to initialize AI service: {str(init_err)}")
        yield format_finish("error")
        return
    
    # Model selection with fallback
    model_name = request.model or DEFAULT_MODEL
    model = None
    
    for candidate in [model_name, DEFAULT_MODEL, FALLBACK_MODEL]:
        try:
            model = GenerativeModel(candidate)
            if candidate != model_name:
                logger.warning(f"Using fallback model: {candidate}")
            break
        except Exception as model_err:
            logger.warning(f"Model {candidate} unavailable: {model_err}")
            continue
    
    if model is None:
        yield format_error("No AI models available. Please try again later.")
        yield format_finish("error")
        return
    
    # Prepare conversation
    try:
        if len(request.messages) < 1:
            yield format_error("No messages provided")
            yield format_finish("error")
            return
        
        # Split: history (all but last) and current message (last)
        history = convert_messages_to_vertex(request.messages[:-1])
        last_msg = request.messages[-1]
        user_message = last_msg.get("content", "")
        
        if not user_message.strip():
            yield format_error("Empty message")
            yield format_finish("error")
            return
        
        # Start chat session
        chat = model.start_chat(history=history)
        
        # Stream the response with timeout protection
        logger.info(f"Streaming response for: '{user_message[:50]}...'")
        
        response_stream = await asyncio.wait_for(
            chat.send_message_async(user_message, stream=True),
            timeout=STREAM_TIMEOUT_SECONDS
        )
        
        total_chars = 0
        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    # Yield in Vercel AI SDK format: 0:"text"\n
                    yield format_text_chunk(text_content)
                    total_chars += len(text_content)
            except ValueError:
                # Empty chunk, continue
                continue
            except Exception as chunk_err:
                logger.warning(f"Chunk processing error (continuing): {chunk_err}")
                continue
        
        # Finish signal
        logger.info(f"Stream completed: {total_chars} characters")
        yield format_finish("stop")
        
    except asyncio.TimeoutError:
        logger.error("Response generation timed out")
        yield format_error("Response timed out. Please try a shorter query.")
        yield format_finish("error")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Stream error: {error_msg}\n{traceback.format_exc()}")
        yield format_error(f"An error occurred: {error_msg}")
        yield format_finish("error")


@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Chat endpoint with Firebase authentication and Vertex AI streaming.
    
    Returns: StreamingResponse with Vercel AI SDK Data Stream Protocol
    """
    # Authentication check
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in."
        )
    
    token = authorization.replace("Bearer ", "")
    user_id = "anonymous"
    
    # Validate token (with dev mode escape hatch)
    is_dev = os.getenv("ENVIRONMENT", "").lower() == "development"
    
    if is_dev and token == "dev-token":
        user_id = "dev-user"
        logger.info("Dev mode: using dev-token")
    else:
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token.get("uid", "unknown")
            logger.info(f"Authenticated user: {user_id}")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            # In production, reject invalid tokens
            if not is_dev:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired authentication token. Please sign in again."
                )
            else:
                logger.warning("Dev mode: allowing invalid token")
                user_id = "dev-unverified"
    
    # Return streaming response
    return StreamingResponse(
        stream_vertex_response(request),
        media_type="text/plain; charset=utf-8",  # Vercel AI SDK expects text/plain
        headers={
            "X-Vercel-AI-Data-Stream": "v1",
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Vertice-User": user_id,
        },
    )


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {"status": "healthy", "service": "chat", "model": DEFAULT_MODEL}
