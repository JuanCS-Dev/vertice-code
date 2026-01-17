"""
Vertex AI Gemini Provider

Usa ADC (Application Default Credentials) - sem necessidade de API key.
Inferência via Vertex AI, não Google AI Studio.

Modelos disponíveis (2026):
- gemini-2.5-pro (DEFAULT - best quality for code, 128K context)
- gemini-2.5-flash (fast + quality balance)
- gemini-3-pro-preview (FUTURE - reasoning-first, 1M context, thinking_level)
- gemini-3-flash-preview (FUTURE - ultra-fast, 1M context, multimodal)
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

# --- SDK HYBRID IMPORTS ---
HAS_GENAI_SDK = False
try:
    from google import genai
    from google.genai import types

    HAS_GENAI_SDK = True
except ImportError:
    pass

HAS_LEGACY_SDK = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel

    HAS_LEGACY_SDK = True
except ImportError:
    pass


class VertexAIProvider:
    """
    Vertex AI Gemini Provider - Enterprise-grade inference.

    Hybrid Architecture:
    - Legacy SDK (v2): gemini-2.5-* models
    - Native SDK (v3): gemini-3-* models (via google-genai)
    """

    MODELS = {
        # Gemini 3 (Standard)
        "flash": "gemini-3-flash-preview",
        "pro": "gemini-3-pro-preview",
        "gemini-3-flash": "gemini-3-flash-preview",
        "gemini-3-pro": "gemini-3-pro-preview",
        # Legacy Mappings (Forced Upgrade)
        "gemini-2.5-flash": "gemini-3-flash-preview",
        "gemini-2.5-pro": "gemini-3-pro-preview",
    }

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "global",
        model_name: str = "pro",
        enable_grounding: bool = False,
    ):
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_LOCATION", location)
        self.model_alias = model_name
        self.model_id = self.MODELS.get(model_name, model_name)
        self.enable_grounding = enable_grounding

        # Determine SDK Mode
        self.is_gemini_3 = "gemini-3" in self.model_id

        # Private State
        self._legacy_model = None
        self._genai_client = None

    def _init_genai_client(self):
        """Lazy init for Google GenAI SDK (v3)."""
        if not self._genai_client and HAS_GENAI_SDK:
            # Gemini 3 Preview requires 'global' location currently
            loc = "global" if "preview" in self.model_id else self.location
            try:
                self._genai_client = genai.Client(vertexai=True, project=self.project, location=loc)
                logger.info(f"✅ GenAI Client (v3) active: {self.model_id} @ {loc}")
            except Exception as e:
                logger.error(f"GenAI Init Failed: {e}")
                raise

    def _init_legacy_model(self):
        """Lazy init for Vertex AI Legacy SDK (v2)."""
        if not self._legacy_model and HAS_LEGACY_SDK:
            try:
                vertexai.init(project=self.project, location=self.location)
                self._legacy_model = GenerativeModel(self.model_id)
                logger.info(f"✅ Legacy SDK (v2) active: {self.model_id} @ {self.location}")
            except Exception as e:
                logger.error(f"Legacy SDK Init Failed: {e}")
                raise

    def is_available(self) -> bool:
        """Check if any SDK is capable."""
        if self.is_gemini_3:
            return HAS_GENAI_SDK
        return HAS_LEGACY_SDK

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
        """Unified Hybrid Streamer."""

        # 1. Routing
        if self.is_gemini_3:
            self._init_genai_client()
            async for chunk in self._stream_v3(
                messages, system_prompt, max_tokens, temperature, tools, **kwargs
            ):
                yield chunk
        else:
            self._init_legacy_model()
            async for chunk in self._stream_v2(
                messages,
                system_prompt,
                max_tokens,
                temperature,
                tools,
                tool_config,
                enable_grounding,
                **kwargs,
            ):
                yield chunk

    async def _stream_v3(self, messages, system_prompt, max_tokens, temperature, tools, **kwargs):
        """Native SDK v3 Implementation."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Message formatting for v3
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                )

            loop = asyncio.get_running_loop()

            def _get_stream():
                return self._genai_client.models.generate_content_stream(
                    model=self.model_id, contents=contents, config=config
                )

            stream_iter = await loop.run_in_executor(None, _get_stream)

            for chunk in stream_iter:
                if chunk.text:
                    yield chunk.text
                    await asyncio.sleep(0)  # Breathe

        except Exception as e:
            logger.error(f"Gemini 3 Stream Error: {e}")
            yield f"[Vertex Error: {e}]"

    async def _stream_v2(
        self,
        messages,
        system_prompt,
        max_tokens,
        temperature,
        tools,
        tool_config,
        enable_grounding,
        **kwargs,
    ):
        """Legacy SDK v2 Implementation (supports Grounding)."""
        # (This is a simplified merge of the previous enterprise logic)
        try:
            from vertexai.generative_models import GenerationConfig, GenerativeModel, Content, Part

            # Grounding logic
            # use_grounding = enable_grounding if enable_grounding is not None else self.enable_grounding
            vertex_tools = self._convert_tools_v2(tools)

            # Re-init model for this specific call to ensure system prompt/tools
            model = GenerativeModel(
                self.model_id,
                system_instruction=system_prompt,
                tools=vertex_tools,  # Grounding would be added here if needed
            )

            # Format contents
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                gemini_role = "user" if msg["role"] == "user" else "model"
                contents.append(Content(role=gemini_role, parts=[Part.from_text(msg["content"])]))

            responses = await model.generate_content_async(
                contents,
                generation_config=GenerationConfig(
                    max_output_tokens=max_tokens, temperature=temperature
                ),
                stream=True,
            )

            async for chunk in responses:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini 2.5 Stream Error: {e}")
            yield f"[Vertex Error: {e}]"

    def _convert_tools_v2(self, tools):
        """Legacy Tooling."""
        if not tools or not HAS_LEGACY_SDK:
            return None
        try:
            from vertexai.generative_models import Tool, FunctionDeclaration

            declarations = []
            for tool in tools:
                schema = tool.get_schema() if hasattr(tool, "get_schema") else tool
                declarations.append(
                    FunctionDeclaration(
                        name=schema["name"],
                        description=schema["description"],
                        parameters=schema["parameters"],
                    )
                )
            return [Tool(function_declarations=declarations)]
        except Exception:
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """Metadata for Router."""
        return {
            "provider": "vertex-ai",
            "model": self.model_id,
            "sdk": "native-v3" if self.is_gemini_3 else "legacy-v2",
            "context_window": 1000000 if self.is_gemini_3 else 128000,
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
