"""
Gemini LLM Client for PROMETHEUS (Vertex AI Edition).
=====================================================
Uses the modern Google GenAI SDK (v1.2+) with Vertex AI backend.

Configuration:
- Project: vertice-ai
- Location: us-central1 (default) or global
- SDK: google.genai

Reference: User provided screenshots of google.genai usage.
"""

import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional, List, Deque
from datetime import datetime
from collections import deque

# Import the new SDK
try:
    from google import genai
    from google.genai import types

    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    stop_sequences: List[str] = field(default_factory=list)

    def to_vertex_config(self) -> types.GenerateContentConfig:
        """Convert to Vertex AI config object."""
        return types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens,
            stop_sequences=self.stop_sequences,
        )


@dataclass
class Message:
    """A conversation message."""

    role: str  # "user" or "model" or "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class GeminiClient:
    """
    Vertex AI Client for Prometheus using google.genai SDK.
    """

    MODELS = {
        "flash": "gemini-3-flash-preview",
        "pro": "gemini-3-pro-preview",
        "thinking": "gemini-2.0-flash-thinking-exp",
        "fallback": "gemini-2.0-flash-exp",  # The Savior
    }

    def __init__(
        self,
        model: str = "gemini-3-pro-preview",
        api_key: Optional[str] = None,
        project_id: str = "vertice-ai",
        location: str = "global",
        config: Optional[GenerationConfig] = None,
    ):
        if not _HAS_SDK:
            raise ImportError("google-genai SDK not found. Install with: pip install google-genai")

        self.model_alias = model
        self.model_name = self.MODELS.get(model, model)

        self.project_id = project_id
        self.location = location
        self.config = config or GenerationConfig()

        # Initialize client
        logger.info(
            f"Initializing Vertex AI Client: project={project_id}, loc={location}, model={self.model_name}"
        )
        self._client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

        self.conversation_history: Deque[Message] = deque(maxlen=100)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        include_history: bool = False,
    ) -> str:
        """Video-game style 'generate' - just gets the text."""

        # Prepare contents
        contents = []
        if include_history:
            for msg in self.conversation_history:
                if msg.role != "system":
                    contents.append(
                        types.Content(role=msg.role, parts=[types.Part.from_text(text=msg.content)])
                    )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        config = self.config.to_vertex_config()
        if system_prompt:
            config.system_instruction = [types.Part.from_text(text=system_prompt)]

        try:
            # Execute (using async wrapper if SDK supports async, otherwise sync in thread)
            # google.genai operations are sync by default in v0.x/v1.x unless .aio used
            # We will use .aio.models.generate_content if available, checking sdk

            # Note: 1.2.0 client has .aio accessor
            response = await self._client.aio.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if response.text:
                # Update history
                self.conversation_history.append(Message(role="user", content=prompt))
                self.conversation_history.append(Message(role="model", content=response.text))
                return response.text
            else:
                return ""

        except Exception as e:
            logger.error(f"Vertex AI Generation Failed: {e}")
            raise RuntimeError(f"Vertex AI Error: {e}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        include_history: bool = False,
    ) -> AsyncIterator[str]:
        """Stream generation tokens."""

        # Similar setup...
        contents = []
        if include_history:
            for msg in self.conversation_history:
                if msg.role != "system":
                    contents.append(
                        types.Content(role=msg.role, parts=[types.Part.from_text(text=msg.content)])
                    )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        config = self.config.to_vertex_config()
        if system_prompt:
            config.system_instruction = [types.Part.from_text(text=system_prompt)]

        try:
            full_text = ""
            async for chunk in await self._client.aio.models.generate_content_stream(
                model=self.model_name, contents=contents, config=config
            ):
                if chunk.text:
                    full_text += chunk.text
                    yield chunk.text

            # History update
            self.conversation_history.append(Message(role="user", content=prompt))
            self.conversation_history.append(Message(role="model", content=full_text))

        except Exception as e:
            logger.error(f"Vertex AI Streaming Failed: {e}")
            raise RuntimeError(f"Vertex AI Stream Error: {e}")

    async def close(self):
        """Cleanup."""
        pass  # New SDK manages its own connections


# Quick test capability
async def quick_generate(prompt: str) -> str:
    client = GeminiClient()
    return await client.generate(prompt)
