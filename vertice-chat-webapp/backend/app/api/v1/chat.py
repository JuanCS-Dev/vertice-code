"""
Vercel AI SDK Compatible Chat Endpoint (VERTEX AI - PRODUCTION)
================================================================
Implements Vercel AI SDK Data Stream Protocol for @ai-sdk/react compatibility.
Reference: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

REVISION: 2026-01-13-STREAM-PROTOCOL-FIX
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from collections import defaultdict
from typing import Any, List, Optional

import firebase_admin
import vertexai
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from firebase_admin import auth, credentials
from pydantic import BaseModel, Field
from vertexai.generative_models import Content, GenerativeModel, Part

from app.core.stream_protocol import (
    format_done,
    format_error,
    format_finish,
    format_response_created,
    format_response_failed,
    format_response_in_progress,
    format_text_chunk,
    format_output_text_delta,
    format_output_text_done,
    format_content_part_added,
    format_content_part_done,
    format_output_item_added,
    format_output_item_done,
    format_response_completed,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
STREAM_TIMEOUT_SECONDS = 120
DEFAULT_MODEL = "gemini-3-pro-preview"
FALLBACK_MODEL = "gemini-3-flash-preview"

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_BURST = 3

rate_limit_store = defaultdict(list)

circuit_breaker_state = {
    "failures": 0,
    "last_failure": 0,
    "state": "closed",
}
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60


def check_circuit_breaker() -> bool:
    now = time.time()
    state = circuit_breaker_state
    if state["state"] == "open":
        if now - state["last_failure"] > CIRCUIT_BREAKER_TIMEOUT:
            state["state"] = "half-open"
            return True
        return False
    return True


def record_circuit_breaker_success():
    if circuit_breaker_state["state"] == "half-open":
        circuit_breaker_state["state"] = "closed"
        circuit_breaker_state["failures"] = 0


def record_circuit_breaker_failure():
    circuit_breaker_state["failures"] += 1
    circuit_breaker_state["last_failure"] = time.time()
    if circuit_breaker_state["failures"] >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
        circuit_breaker_state["state"] = "open"


def _init_firebase():
    if firebase_admin._apps:
        return
    firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if firebase_key:
        import json

        cred = credentials.Certificate(json.loads(firebase_key))
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)


try:
    _init_firebase()
except Exception as e:
    logger.warning(f"Firebase init failed: {e}")


def check_rate_limit(user_id: str) -> bool:
    now = time.time()
    user_requests = rate_limit_store[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT_WINDOW]
    if len(user_requests) >= RATE_LIMIT_REQUESTS:
        recent = [t for t in user_requests if now - t < 10]
        if len(recent) >= RATE_LIMIT_BURST:
            return False
    user_requests.append(now)
    return True


class ChatRequest(BaseModel):
    messages: List[Any] = Field(..., min_length=1)
    stream: bool = Field(default=True)
    model: str = Field(default=DEFAULT_MODEL)
    session_id: Optional[str] = Field(default=None)


def convert_messages_to_vertex(messages: List[Any]) -> List[Content]:
    vertex_history = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not content or not content.strip():
            continue
        if role == "user":
            vertex_history.append(Content(role="user", parts=[Part.from_text(content)]))
        elif role in ("assistant", "model"):
            vertex_history.append(Content(role="model", parts=[Part.from_text(content)]))
        elif role == "system":
            vertex_history.append(
                Content(role="user", parts=[Part.from_text(f"[System]: {content}")])
            )
    return vertex_history


async def stream_vertex_response(request: ChatRequest, session_id: Optional[str] = None):
    if not check_circuit_breaker():
        yield format_error("Service temporarily unavailable.")
        yield format_finish("error")
        return

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "global")

    try:
        vertexai.init(project=project_id, location=location)
        record_circuit_breaker_success()
    except Exception as init_err:
        record_circuit_breaker_failure()
        yield format_error(f"AI Service init failed: {init_err}")
        yield format_finish("error")
        return

    model_name = request.model or DEFAULT_MODEL
    model = None
    for candidate in [model_name, DEFAULT_MODEL, FALLBACK_MODEL]:
        try:
            model = GenerativeModel(candidate)
            break
        except Exception:
            continue

    if model is None:
        yield format_error("No AI models available.")
        yield format_finish("error")
        return

    try:
        if len(request.messages) < 1:
            yield format_error("No messages provided")
            yield format_finish("error")
            return

        history = convert_messages_to_vertex(request.messages[:-1])
        last_msg = request.messages[-1]
        user_message = last_msg.get("content", "")

        if not user_message.strip():
            yield format_error("Empty message")
            yield format_finish("error")
            return

        # 🛡️ LLM GUARD - Input Shielding
        from app.core.security import get_llm_guard

        guard_cls = get_llm_guard()
        is_safe, threats = guard_cls.scan_input(user_message)

        if not is_safe:
            logger.warning(f"Security Alert for session {session_id}: {threats}")
            user_message = f"[SECURITY NOTICE: Input triggered a safety flag. Adhere to guidelines.]\n\n{user_message}"

        chat = model.start_chat(history=history)
        logger.info(f"Streaming response for session {session_id}")

        response_stream = await asyncio.wait_for(
            chat.send_message_async(user_message, stream=True), timeout=STREAM_TIMEOUT_SECONDS
        )

        total_chars = 0
        full_response_text = ""

        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    # 🛡️ LLM GUARD - Output Sanitization
                    sanitized_content = guard_cls.sanitize_output(text_content)
                    yield format_text_chunk(sanitized_content)
                    total_chars += len(sanitized_content)
                    full_response_text += sanitized_content
            except ValueError:
                continue
            except Exception:
                continue

        yield format_finish("stop")

        if session_id and full_response_text:
            try:
                from app.core.database import get_db_session
                from app.models.database import ChatMessage

                async with get_db_session() as db_session:
                    ai_msg = ChatMessage(
                        session_id=uuid.UUID(session_id),
                        role="assistant",
                        content=full_response_text,
                    )
                    db_session.add(ai_msg)
                    await db_session.commit()
            except Exception as save_err:
                logger.error(f"Failed to save AI response: {save_err}")

    except asyncio.TimeoutError:
        yield format_error("Response timed out.")
        yield format_finish("error")
    except Exception as e:
        record_circuit_breaker_failure()
        yield format_error(f"An error occurred: {str(e)}")
        yield format_finish("error")


async def stream_vertex_response_open_responses(
    request: ChatRequest,
    session_id: Optional[str] = None,
):
    if not check_circuit_breaker():
        error_data = {"type": "server_error", "message": "Service unavailable."}
        yield format_response_failed(str(uuid.uuid4()), error_data, 1)
        yield format_done()
        return

    response_id = str(uuid.uuid4())
    sequence_num = 1
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "global")

    try:
        vertexai.init(project=project_id, location=location)
        record_circuit_breaker_success()
        model_name = request.model or DEFAULT_MODEL
        model = None
        for candidate in [model_name, DEFAULT_MODEL, FALLBACK_MODEL]:
            try:
                model = GenerativeModel(candidate)
                break
            except Exception:
                continue

        if model is None:
            yield format_response_failed(response_id, {"message": "No models"}, sequence_num)
            yield format_done()
            return

        history = convert_messages_to_vertex(request.messages[:-1])
        user_message = request.messages[-1].get("content", "")

        yield format_response_created(response_id, model_name)
        sequence_num += 1
        yield format_response_in_progress(response_id)
        sequence_num += 1

        item_id = str(uuid.uuid4())
        yield format_output_item_added(item_id)
        sequence_num += 1
        yield format_content_part_added(item_id)
        sequence_num += 1

        chat = model.start_chat(history=history)
        response_stream = await asyncio.wait_for(
            chat.send_message_async(user_message, stream=True), timeout=STREAM_TIMEOUT_SECONDS
        )

        full_response_text = ""
        async for chunk in response_stream:
            try:
                text_content = chunk.text
                if text_content:
                    sequence_num += 1
                    yield format_output_text_delta(item_id, text_content, sequence_num)
                    full_response_text += text_content
            except Exception:
                continue

        sequence_num += 1
        yield format_output_text_done(item_id, full_response_text, sequence_num)
        sequence_num += 1
        yield format_content_part_done(item_id, sequence_num)
        sequence_num += 1
        yield format_output_item_done(item_id, sequence_num)
        sequence_num += 1
        yield format_response_completed(response_id, {"total_tokens": 0}, sequence_num)
        yield format_done()

    except Exception as e:
        record_circuit_breaker_failure()
        yield format_response_failed(response_id, {"message": str(e)}, sequence_num)
        yield format_done()


@router.post("")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    authorization: Optional[str] = Header(None),
    protocol: Optional[str] = None,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")

    token = authorization.replace("Bearer ", "")
    user_id = "anonymous"

    is_dev = os.getenv("ENVIRONMENT", "").lower() == "development"
    if is_dev and token == "dev-token":
        user_id = "dev-user"
    else:
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=True)
            user_id = decoded_token.get("uid", "unknown")
        except Exception:
            if not is_dev:
                raise HTTPException(status_code=401, detail="Invalid token.")
            user_id = "dev-unverified"

    if not check_rate_limit(user_id):
        raise HTTPException(status_code=429, detail="Too many requests.")

    from app.core.database import get_db_session
    from app.models.database import ChatSession, ChatMessage

    session_id = chat_request.session_id or str(uuid.uuid4())

    async with get_db_session() as db_session:
        if not chat_request.session_id:
            new_session = ChatSession(
                id=uuid.UUID(session_id),
                user_id=uuid.UUID(user_id) if len(user_id) > 20 else None,
                title=chat_request.messages[-1].get("content", "New Chat")[:50],
                model_used=chat_request.model,
            )
            db_session.add(new_session)
            await db_session.flush()

        user_content = chat_request.messages[-1].get("content", "")
        if user_content:
            user_msg = ChatMessage(
                session_id=uuid.UUID(session_id), role="user", content=user_content
            )
            db_session.add(user_msg)
            await db_session.commit()

    from app.core.config import settings

    use_open_responses = (settings.ENABLE_OPEN_RESPONSES and protocol == "open_responses") or (
        settings.OPEN_RESPONSES_DEFAULT and protocol != "vercel"
    )

    if use_open_responses:
        stream_gen = stream_vertex_response_open_responses(chat_request, session_id=session_id)
        media_type = "text/event-stream"
    else:
        stream_gen = stream_vertex_response(chat_request, session_id=session_id)
        media_type = "text/plain; charset=utf-8"

    return StreamingResponse(stream_gen, media_type=media_type)


@router.get("/health")
async def chat_health():
    return {"status": "healthy", "service": "chat", "model": DEFAULT_MODEL}
