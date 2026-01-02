"""
Vertex AI Gemini Provider

Usa ADC (Application Default Credentials) - sem necessidade de API key.
Inferência via Vertex AI, não Google AI Studio.

Modelos disponíveis (2026):
- gemini-3-pro-preview (RECOMMENDED - reasoning-first, 1M context)
- gemini-2.0-flash (multimodal, agentic)
- gemini-3-deep-think (coming soon)
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, List, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class VertexAIProvider:
    """
    Vertex AI Gemini Provider - Enterprise-grade inference.

    Usa ADC (Application Default Credentials):
    - No Cloud: credenciais automáticas
    - Local: `gcloud auth application-default login`

    Não precisa de API key!
    """

    MODELS = {
        # Gemini 3 (2026) - RECOMMENDED
        "pro": "gemini-3-pro-preview",            # Reasoning-first, 1M context, agentic
        "flash": "gemini-2.0-flash",        # Multimodal, complex understanding
        "3-pro": "gemini-3-pro-preview",
        "3-flash": "gemini-2.0-flash",
        # Legacy (still available)
        "2.0-flash": "gemini-2.0-flash-exp",
        "2.5-flash": "gemini-2.5-flash-preview",
    }

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "flash",  # Default to Gemini 3 Flash (Pro only for reasoning)
    ):
        """Initialize Vertex AI provider.

        Args:
            project: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
            location: Vertex AI location (gemini-2.5-flash only in us-central1)
            model_name: Model alias or full name
        """
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = self.MODELS.get(model_name, model_name)
        self._client = None
        self._model = None

    def _ensure_client(self):
        """Lazy initialize Vertex AI client."""
        if self._client is None:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                vertexai.init(project=self.project, location=self.location)
                self._model = GenerativeModel(self.model_name)
                self._client = True  # Flag to indicate initialization
                logger.info(f"✅ Vertex AI initialized: {self.model_name} @ {self.location}")

            except ImportError:
                raise RuntimeError(
                    "google-cloud-aiplatform not installed. "
                    "Run: pip install google-cloud-aiplatform"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise

    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            self._ensure_client()
            return self._model is not None
        except Exception:
            return False

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate completion from messages."""
        self._ensure_client()

        # Format messages for Gemini
        prompt = self._format_messages(messages)

        # Extract system prompt if present
        system_prompt = None
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
                break

        # Run in thread pool (Vertex SDK is sync)
        loop = asyncio.get_event_loop()

        def _generate():
            from vertexai.generative_models import GenerationConfig

            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            # Create model with system instruction if provided
            if system_prompt:
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(
                    self.model_name,
                    system_instruction=system_prompt
                )
            else:
                model = self._model

            response = model.generate_content(prompt, generation_config=config)
            return response.text

        result = await loop.run_in_executor(None, _generate)
        return result

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        self._ensure_client()

        prompt = self._format_messages(messages)
        system_prompt = None
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
                break

        loop = asyncio.get_event_loop()

        def _create_stream():
            from vertexai.generative_models import GenerationConfig, GenerativeModel

            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            if system_prompt:
                model = GenerativeModel(
                    self.model_name,
                    system_instruction=system_prompt
                )
            else:
                model = self._model

            return model.generate_content(prompt, generation_config=config, stream=True)

        response_stream = await loop.run_in_executor(None, _create_stream)

        def _get_next(iterator):
            try:
                return next(iterator)
            except StopIteration:
                return None

        iterator = iter(response_stream)
        while True:
            chunk = await loop.run_in_executor(None, _get_next, iterator)
            if chunk is None:
                break
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
            await asyncio.sleep(0)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async for chunk in self.stream_generate(
            full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            yield chunk

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Gemini (non-chat mode)."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                continue  # Handled separately
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")

        return "\n\n".join(formatted)

    def get_model_info(self) -> Dict[str, str | bool | int]:
        """Get model information."""
        # Gemini 3 has 1M context for all models
        context_window = 1_000_000 if "3" in self.model_name else 128_000
        return {
            'provider': 'vertex-ai',
            'model': self.model_name,
            'project': self.project,
            'location': self.location,
            'available': self.is_available(),
            'context_window': context_window,
            'supports_streaming': True,
            'supports_thinking': "3-pro" in self.model_name,  # Gemini 3 Pro has thinking
            'cost_tier': 'enterprise',  # R$8000 credits!
            'speed_tier': 'ultra_fast',
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        # Gemini tokenizer is roughly 4 chars per token
        return len(text) // 4
