"""
Vertex AI Gemini Provider

Usa ADC (Application Default Credentials) - sem necessidade de API key.
Inferência via Vertex AI, não Google AI Studio.

Modelos suportados (2026, Vertex AI):
- gemini-3-pro-preview (global endpoint)
- gemini-3-flash-preview (global endpoint)
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

from vertice_core.openresponses_types import (
    TokenUsage,
    OpenResponsesError,
    ErrorType,
    JsonSchemaResponseFormat,
)
from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

# Configure Logging
logger = logging.getLogger(__name__)

# --- Google Gen AI SDK (Vertex AI) ---
HAS_GENAI_SDK = False
try:
    from google import genai
    from google.genai import types

    HAS_GENAI_SDK = True
except ImportError:
    pass


class VertexAIProvider:
    """
    Vertex AI Gemini Provider - Enterprise-grade inference.
    """

    MODELS = {
        # Gemini 3 (Preview) on Vertex AI:
        # Docs 2026: Gemini 3 Pro/Flash Preview are only available on the global endpoint.
        "flash": "gemini-3-flash-preview",
        "pro": "gemini-3-pro-preview",
        "gemini-3-flash": "gemini-3-flash-preview",
        "gemini-3-pro": "gemini-3-pro-preview",
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3-pro-preview": "gemini-3-pro-preview",
    }

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "global",
        model_name: str = "pro",
        enable_grounding: bool = False,
    ):
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        # IMPORTANT (2026): inference for top-tier models is commonly "global".
        #
        # Respect an explicit `location` argument. Use env vars only as fallback
        # (keeps legacy compatibility while allowing call-sites to force global).
        location_from_env = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION")
        self.location = location if location else (location_from_env or "global")
        self.model_alias = model_name
        self.model_id = self.MODELS.get(model_name, model_name)
        self.enable_grounding = enable_grounding

        self._genai_client = None
        self._validate_model_id()

    def _validate_model_id(self) -> None:
        allowed = {
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
        }
        if self.model_id not in allowed:
            raise ValueError(
                "Unsupported Vertex AI model_id for 2026 Google-native mode. "
                f"Got: {self.model_id!r}. Allowed: {sorted(allowed)}"
            )

    def _init_genai_client(self):
        """Lazy init for Google GenAI SDK (v3)."""
        if self._genai_client is not None:
            return
        if not HAS_GENAI_SDK:
            raise RuntimeError("google-genai SDK not installed (required for Vertex AI Gemini 3).")
        try:
            self._genai_client = genai.Client(
                vertexai=True,
                project=self.project,
                location=self.location,
            )
            logger.info(f"✅ GenAI Client active: {self.model_id} @ {self.location}")
        except Exception as e:
            logger.error(f"GenAI Init Failed: {e}")
            raise

    def is_available(self) -> bool:
        """Check if any SDK is capable."""
        return HAS_GENAI_SDK

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Single-turn generation wrapper."""
        full_text = ""
        async for chunk in self.stream_chat(
            messages=messages, max_tokens=max_tokens, temperature=temperature, **kwargs
        ):
            full_text += chunk
        return full_text

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None,
        tool_config: Optional[str] = "AUTO",
        enable_grounding: Optional[bool] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Unified streamer (Google Gen AI SDK on Vertex AI)."""
        self._init_genai_client()
        async for chunk in self._stream_v3(
            messages, system_prompt, max_tokens, temperature, tools, **kwargs
        ):
            yield chunk

    async def _stream_v3(self, messages, system_prompt, max_tokens, temperature, tools, **kwargs):
        """Native SDK v3 Implementation."""
        try:
            include_thoughts = bool(kwargs.pop("include_thoughts", False)) or (
                os.getenv("VERTICE_VERTEX_INCLUDE_THOUGHTS", "0").strip().lower()
                in {"1", "true", "yes", "on"}
            )

            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Thinking / "inner voice" (2026):
            # google-genai streams thought parts with `part.thought == True`.
            if include_thoughts and hasattr(types, "ThinkingConfig"):
                try:
                    config.thinking_config = types.ThinkingConfig(include_thoughts=True)  # type: ignore[attr-defined]
                except Exception:
                    # Older SDKs may not accept thinking_config; keep streaming functional output only.
                    include_thoughts = False

            # Message formatting for v3
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                )

            def _extract_parts(item: Any) -> list[tuple[bool, str]]:
                """
                Extract (is_thought, text) parts from a streamed chunk.

                When thinking is enabled, Gemini may stream thought parts separately
                (part.thought==True). We keep them distinct so callers can route them.
                """
                out: list[tuple[bool, str]] = []

                direct = getattr(item, "text", None)
                if isinstance(direct, str) and direct:
                    out.append((False, direct))
                    return out

                candidates = getattr(item, "candidates", None)
                if candidates:
                    for cand in candidates:
                        content = getattr(cand, "content", None)
                        parts = getattr(content, "parts", None) if content else None
                        if not parts:
                            continue
                        for part in parts:
                            part_text = getattr(part, "text", None)
                            if not isinstance(part_text, str) or not part_text:
                                continue
                            is_thought = bool(getattr(part, "thought", False))
                            out.append((is_thought, part_text))

                return out

            stream = await self._genai_client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=contents,
                config=config,
            )
            if stream is None:
                raise RuntimeError(
                    "google-genai returned None for aio.generate_content_stream "
                    "(likely auth/config issue)"
                )

            async for chunk in stream:
                for is_thought, text in _extract_parts(chunk):
                    if is_thought and include_thoughts:
                        yield f"<thought>{text}</thought>"
                    elif not is_thought:
                        yield text
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Gemini 3 Stream Error: {e}")
            yield f"[Vertex Error: {e}]"

    def get_model_info(self) -> Dict[str, Any]:
        """Metadata for Router."""
        return {
            "provider": "vertex-ai",
            "model": self.model_id,
            "sdk": "google-genai",
            "context_window": 1000000,
            "supports_streaming": True,
        }

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def stream_open_responses(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream usando protocolo Open Responses.

        Emite eventos SSE seguindo a especificação Open Responses.

        Yields:
            str: Eventos SSE formatados

        Exemplo de uso:
            async for event in provider.stream_open_responses(messages):
                print(event)  # event: response.output_text.delta\ndata: {...}\n\n
        """
        # Cria builder com nome do modelo
        builder = OpenResponsesStreamBuilder(model=self.model_id)

        try:
            # Emite eventos iniciais
            builder.start()
            for event in builder.get_events():
                yield event.to_sse()
            builder.clear_events()

            # Cria MessageItem
            message_item = builder.add_message()
            for event in builder.get_events():
                yield event.to_sse()
            builder.clear_events()

            # Stream do conteúdo
            token_count = 0
            async for chunk in self.stream_chat(
                messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            ):
                token_count += len(chunk.split())  # Estimativa simples
                builder.text_delta(message_item, chunk)
                yield builder.get_last_event_sse()
                builder.clear_events()

            # Finaliza com sucesso
            usage = TokenUsage(
                input_tokens=sum(len(m.get("content", "")) // 4 for m in messages),
                output_tokens=token_count,
                total_tokens=0,  # Será calculado
            )
            usage.total_tokens = usage.input_tokens + usage.output_tokens

            builder.complete(usage)
            for event in builder.get_events():
                yield event.to_sse()

            # Evento terminal
            yield builder.done()

        except Exception as e:
            # Emite erro
            error = OpenResponsesError(
                type=ErrorType.MODEL_ERROR, code="generation_failed", message=str(e)
            )
            builder.fail(error)
            for event in builder.get_events():
                yield event.to_sse()
            yield builder.done()

    async def stream_chat_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: "JsonSchemaResponseFormat",
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream com structured output (JSON Schema).
        """
        from google.genai.types import GenerateContentConfig

        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_format.schema,
        )

        async for chunk in self.stream_chat(
            messages,
            generation_config=config,
            **kwargs,
        ):
            yield chunk
