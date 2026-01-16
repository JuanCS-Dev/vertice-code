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
import time
from collections import defaultdict

import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
import firebase_admin
from firebase_admin import auth, credentials

from app.core.stream_protocol import (
    format_text_chunk,
    format_finish,
    format_error,
    # Open Responses functions
    format_response_created,
    format_response_in_progress,
    format_output_item_added,
    format_content_part_added,
    format_output_text_delta,
    format_output_text_done,
    format_content_part_done,
    format_output_item_done,
    format_response_completed,
    format_response_failed,
    format_done,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
STREAM_TIMEOUT_SECONDS = 120
DEFAULT_MODEL = "gemini-3-pro-preview"
FALLBACK_MODEL = "gemini-3-flash-preview"

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_BURST = 3  # burst allowance

# In-memory rate limiting store (use Redis in production)
rate_limit_store = defaultdict(list)

# Circuit breaker for Vertex AI
circuit_breaker_state = {
    "failures": 0,
    "last_failure": 0,
    "state": "closed",  # closed, open, half-open
}
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds


def check_circuit_breaker() -> bool:
    """
    Check circuit breaker state.
    Returns True if request should proceed, False if circuit is open.
    """
    now = time.time()
    state = circuit_breaker_state

    if state["state"] == "open":
        if now - state["last_failure"] > CIRCUIT_BREAKER_TIMEOUT:
            # Try half-open
            state["state"] = "half-open"
            logger.info("Circuit breaker: trying half-open")
            return True
        return False

    return True


def record_circuit_breaker_success():
    """Record successful request."""
    if circuit_breaker_state["state"] == "half-open":
        circuit_breaker_state["state"] = "closed"
        circuit_breaker_state["failures"] = 0
        logger.info("Circuit breaker: closed (success)")


def record_circuit_breaker_failure():
    """Record failed request."""
    circuit_breaker_state["failures"] += 1
    circuit_breaker_state["last_failure"] = time.time()

    if circuit_breaker_state["failures"] >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
        circuit_breaker_state["state"] = "open"
        logger.error(f"Circuit breaker: opened after {circuit_breaker_state['failures']} failures")


logger.info("Loading Vercel AI SDK compatible chat.py (PRODUCTION - GEMINI 3.0)")


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


def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limits.
    Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    user_requests = rate_limit_store[user_id]

    # Remove old requests outside the window
    user_requests[:] = [
        req_time for req_time in user_requests if now - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if under limit
    if len(user_requests) >= RATE_LIMIT_REQUESTS:
        # Allow burst requests
        recent_requests = [
            req_time for req_time in user_requests if now - req_time < 10
        ]  # 10 second burst window
        if len(recent_requests) >= RATE_LIMIT_BURST:
            return False

    # Add current request
    user_requests.append(now)
    return True


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    messages: List[Any] = Field(..., min_length=1, description="Chat messages array")
    stream: bool = Field(default=True, description="Enable streaming response")
    model: str = Field(default=DEFAULT_MODEL, description="Model to use")
    session_id: Optional[str] = Field(default=None, description="Existing session ID")


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
            vertex_history.append(
                Content(role="user", parts=[Part.from_text(f"[System]: {content}")])
            )

    return vertex_history


async def stream_vertex_response(request: ChatRequest, session_id: Optional[str] = None):
    """
    Stream Vertex AI response using Vercel AI SDK Data Stream Protocol.

    Protocol format:
    - 0:"text" for text chunks
    - d:{"finishReason":"stop"} for completion
    - 3:"error" for errors
    """
    # Circuit breaker check
    if not check_circuit_breaker():
        logger.warning("Circuit breaker open - rejecting request")
        yield format_error("Service temporarily unavailable. Please try again later.")
        yield format_finish("error")
        return

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    # Gemini 3.0 Preview models require 'global' or specific regions like 'us-central1'
    # For now, 'global' is the safest bet for Preview access.
    location = os.getenv("VERTEX_AI_LOCATION", "global")

    if location != "global":
        logger.warning(
            f"Using non-global location '{location}' for Gemini 3 Preview. This might fail."
        )

    try:
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        logger.info(f"Vertex AI initialized: project={project_id}, location={location}")
        record_circuit_breaker_success()

    except Exception as init_err:
        logger.error(f"Vertex AI init failed: {init_err}")
        record_circuit_breaker_failure()
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
            chat.send_message_async(user_message, stream=True), timeout=STREAM_TIMEOUT_SECONDS
        )

        total_chars = 0
        full_response_text = ""

        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    # Yield in Vercel AI SDK format: 0:"text"\n
                    yield format_text_chunk(text_content)
                    total_chars += len(text_content)
                    full_response_text += text_content
            except ValueError:
                # Empty chunk, continue
                continue
            except Exception as chunk_err:
                logger.warning(f"Chunk processing error (continuing): {chunk_err}")
                continue

        # Finish signal
        logger.info(f"Stream completed: {total_chars} characters")
        yield format_finish("stop")

        # ---------------------------------------------------------------------
        # SAVE ASSISTANT RESPONSE
        # ---------------------------------------------------------------------
        if session_id and full_response_text:
            try:
                from app.core.database import get_db_session
                from app.models.database import ChatMessage
                import uuid

                async with get_db_session() as db_session:
                    ai_msg = ChatMessage(
                        session_id=uuid.UUID(session_id),
                        role="assistant",
                        content=full_response_text,
                    )
                    db_session.add(ai_msg)
                    await db_session.commit()
                    logger.info(f"Saved AI response to session {session_id}")
            except Exception as save_err:
                logger.error(f"Failed to save AI response: {save_err}")

    except asyncio.TimeoutError:
        logger.error("Response generation timed out")
        yield format_error("Response timed out. Please try a shorter query.")
        yield format_finish("error")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Stream error: {error_msg}\n{traceback.format_exc()}")
        record_circuit_breaker_failure()
        yield format_error(f"An error occurred: {error_msg}")
        yield format_finish("error")


async def stream_vertex_response_open_responses(
    request: ChatRequest, session_id: Optional[str] = None
):
    """
    Stream Vertex AI response using Open Responses protocol.

    Alternative to Vercel AI SDK protocol for Open Responses compatibility.

    Events emitted:
    - response.created
    - response.in_progress
    - response.output_item.added
    - response.content_part.added
    - response.output_text.delta (repeated)
    - response.output_text.done
    - response.content_part.done
    - response.output_item.done
    - response.completed
    - [DONE]
    """
    # Circuit breaker check
    if not check_circuit_breaker():
        logger.warning("Circuit breaker open - rejecting Open Responses request")
        error_data = {
            "type": "server_error",
            "code": "service_unavailable",
            "message": "Service temporarily unavailable. Please try again later.",
        }
        yield format_response_failed(str(uuid.uuid4()), error_data, 1)
        yield format_done()
        return

    from app.core.stream_protocol import (
        format_response_created,
        format_response_in_progress,
        format_output_item_added,
        format_content_part_added,
        format_output_text_delta,
        format_output_text_done,
        format_content_part_done,
        format_output_item_done,
        format_response_completed,
        format_response_failed,
        format_done,
    )

    import uuid

    response_id = str(uuid.uuid4())
    sequence_num = 1

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "global")

    try:
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        record_circuit_breaker_success()

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
            error_data = {
                "type": "invalid_request_error",
                "code": "model_not_found",
                "message": "No AI models available.",
            }
            yield format_response_failed(response_id, error_data, sequence_num)
            yield format_done()
            return

        # Prepare conversation
        if len(request.messages) < 1:
            error_data = {
                "type": "invalid_request_error",
                "code": "invalid_request",
                "message": "No messages provided",
            }
            yield format_response_failed(response_id, error_data, sequence_num)
            yield format_done()
            return

        # Split: history and current message
        history = convert_messages_to_vertex(request.messages[:-1])
        last_msg = request.messages[-1]
        user_message = last_msg.get("content", "")

        if not user_message.strip():
            error_data = {
                "type": "invalid_request_error",
                "code": "invalid_request",
                "message": "Empty message",
            }
            yield format_response_failed(response_id, error_data, sequence_num)
            yield format_done()
            return

        # Emit initial events
        yield format_response_created(response_id, model_name)
        sequence_num += 1

        yield format_response_in_progress(response_id)
        sequence_num += 1

        # Create message item
        item_id = str(uuid.uuid4())
        yield format_output_item_added(item_id)
        sequence_num += 1

        yield format_content_part_added(item_id)
        sequence_num += 1

        # Start chat session and stream
        chat = model.start_chat(history=history)

        response_stream = await asyncio.wait_for(
            chat.send_message_async(user_message, stream=True), timeout=STREAM_TIMEOUT_SECONDS
        )

        full_response_text = ""
        chunk_count = 0

        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    sequence_num += 1
                    chunk_count += 1
                    yield format_output_text_delta(item_id, text_content, sequence_num)
                    full_response_text += text_content
            except ValueError:
                continue
            except Exception as chunk_err:
                logger.warning(f"Chunk processing error: {chunk_err}")
                continue

        # Emit completion events
        sequence_num += 1
        yield format_output_text_done(item_id, full_response_text, sequence_num)

        sequence_num += 1
        yield format_content_part_done(item_id, sequence_num)

        sequence_num += 1
        yield format_output_item_done(item_id, sequence_num)

        # Final completion
        usage = {
            "input_tokens": len(user_message) // 4,  # Rough estimate
            "output_tokens": len(full_response_text) // 4,
            "total_tokens": (len(user_message) + len(full_response_text)) // 4,
        }

        sequence_num += 1
        yield format_response_completed(response_id, usage, sequence_num)

        yield format_done()

        logger.info(
            f"Open Responses stream completed: {len(full_response_text)} chars, {chunk_count} chunks"
        )

    except asyncio.TimeoutError:
        error_data = {
            "type": "server_error",
            "code": "timeout",
            "message": "Response generation timed out",
        }
        yield format_response_failed(response_id, error_data, sequence_num)
        yield format_done()

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Open Responses stream error: {error_msg}\n{traceback.format_exc()}")
        record_circuit_breaker_failure()

        error_data = {
            "type": "server_error",
            "code": "internal_error",
            "message": f"An error occurred: {error_msg}",
        }
        yield format_response_failed(response_id, error_data, sequence_num)
        yield format_done()


@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
    protocol: Optional[str] = None,  # Query param: "vercel" or "open_responses"
):
    """
    Chat endpoint with Firebase authentication and Vertex AI streaming.

    Returns: StreamingResponse with Vercel AI SDK Data Stream Protocol
    """
    # Authentication check
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")

    token = authorization.replace("Bearer ", "")
    user_id = "anonymous"

    # Rate limiting check
    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user: {user_id}")
        raise HTTPException(
            status_code=429, detail="Too many requests. Please wait before sending another message."
        )

    # Validate token (with dev mode escape hatch)
    is_dev = os.getenv("ENVIRONMENT", "").lower() == "development"

    if is_dev and token == "dev-token":
        user_id = "dev-user"
        logger.info("Dev mode: using dev-token")
    else:
        try:
            # check_revoked=True ensures revoked tokens are rejected immediately
            decoded_token = auth.verify_id_token(token, check_revoked=True)
            user_id = decoded_token.get("uid", "unknown")

            # Additional validation
            if not user_id or len(user_id) < 6:
                raise ValueError("Invalid user ID in token")

            logger.info(f"Authenticated user: {user_id}")
        except ValueError as e:
            logger.error(f"Token validation failed - invalid data: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token format. Please sign in again.",
            )
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            # In production, reject invalid tokens
            if not is_dev:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired authentication token. Please sign in again.",
                )
            else:
                logger.warning("Dev mode: allowing invalid token")
                user_id = "dev-unverified"

    # Input validation
    try:
        # Validate request structure
        if not hasattr(request, "messages") or not request.messages:
            raise HTTPException(status_code=400, detail="Messages array is required")

        if len(request.messages) > 50:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Too many messages (max 50)")

        total_content_length = 0
        for i, msg in enumerate(request.messages):
            if not isinstance(msg, dict):
                raise HTTPException(status_code=400, detail=f"Message {i} must be an object")

            if "role" not in msg or "content" not in msg:
                raise HTTPException(status_code=400, detail=f"Message {i} missing role or content")

            if msg["role"] not in ["system", "user", "assistant"]:
                raise HTTPException(status_code=400, detail=f"Message {i} has invalid role")

            if not isinstance(msg["content"], str):
                raise HTTPException(status_code=400, detail=f"Message {i} content must be string")

            if len(msg["content"]) > 10000:  # Per message limit
                raise HTTPException(
                    status_code=400, detail=f"Message {i} too long (max 10000 chars)"
                )

            total_content_length += len(msg["content"])

        if total_content_length > 50000:  # Total conversation limit
            raise HTTPException(
                status_code=400, detail="Total conversation too long (max 50000 chars)"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Input validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format")

    # -------------------------------------------------------------------------
    # PERSISTENCE LAYER: Save Chat History
    # -------------------------------------------------------------------------
    from app.core.database import get_db_session
    from app.models.database import ChatSession, ChatMessage
    import uuid

    session_id = getattr(request, "session_id", None) or str(uuid.uuid4())

    workspace_id = None  # getattr(user, "workspace_id", None) ... user is not defined here yet.

    # We need to handle DB ops here carefully to not block streaming significantly
    # but ensure user message is saved.

    async with get_db_session() as db_session:
        # 1. Create or Get Session
        if not session_id:
            new_session = ChatSession(
                user_id=uuid.UUID(user_id)
                if user_id not in ("anonymous", "dev-user", "dev-unverified")
                else None,
                workspace_id=uuid.UUID(workspace_id)
                if workspace_id and workspace_id not in ("anonymous", "dev-user")
                else None,
                title=request.messages[-1].get("content", "New Chat")[:50],
                model_used=request.model,
            )
            db_session.add(new_session)
            await db_session.flush()
            session_id = str(new_session.id)
            logger.info(f"Created new chat session: {session_id}")

        # 2. Save User Message
        user_content = request.messages[-1].get("content", "")
        if user_content:
            user_msg = ChatMessage(
                session_id=uuid.UUID(session_id), role="user", content=user_content
            )
            db_session.add(user_msg)
            await db_session.commit()

    # Choose protocol based on feature flag and client preference
    from app.core.config import settings

    use_open_responses = (settings.ENABLE_OPEN_RESPONSES and protocol == "open_responses") or (
        settings.OPEN_RESPONSES_DEFAULT and protocol != "vercel"
    )

    if use_open_responses:
        # Use Open Responses protocol
        stream_generator = stream_vertex_response_open_responses(request, session_id=session_id)
        media_type = "text/event-stream"
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Vertice-Protocol": "open_responses",
            "X-Vertice-User": user_id,
            "X-Vertice-Session-Id": session_id,
        }
    else:
        # Use Vercel AI SDK protocol (default)
        stream_generator = stream_vertex_response(request, session_id=session_id)
        media_type = "text/plain; charset=utf-8"
        headers = {
            "X-Vercel-AI-Data-Stream": "v1",
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Vertice-Protocol": "vercel",
            "X-Vertice-User": user_id,
            "X-Vertice-Session-Id": session_id,
        }

    # Return streaming response
    return StreamingResponse(
        stream_generator,
        media_type=media_type,
        headers=headers,
    )


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {"status": "healthy", "service": "chat", "model": DEFAULT_MODEL}
