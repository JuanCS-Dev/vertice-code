"""
Gemini HTTPX Streamer - Direct API implementation.

Fallback streaming using httpx SSE.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from .config import GeminiStreamConfig, GEMINI_OUTPUT_RULES
from .base import BaseStreamer

logger = logging.getLogger(__name__)


class GeminiHTTPXStreamer(BaseStreamer):
    """
    Streamer using httpx direct API call with SSE.

    OPTIMIZED for Gemini 3+ (Nov 2025):
    - Uses systemInstruction in API payload (native)
    - Temperature locked at 1.0 to prevent looping
    - Anti-repetition instructions embedded
    """

    def __init__(self, config: GeminiStreamConfig) -> None:
        """Initialize HTTPX streamer."""
        super().__init__(config)
        self._client: Any = None

    async def initialize(self) -> bool:
        """Initialize httpx client."""
        if self._initialized:
            return True

        try:
            import httpx

            self._client = httpx.AsyncClient(timeout=self.config.stream_timeout)
            self._initialized = True
            logger.info("GeminiHTTPXStreamer initialized")
            return True

        except ImportError as e:
            logger.warning(f"httpx not available: {e}")
            return False
        except Exception as e:
            logger.error(f"HTTPX initialization failed: {e}")
            return False

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream using httpx direct API call with native systemInstruction."""
        if not self._initialized:
            yield "❌ HTTPX not initialized"
            return

        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.config.model_name}:streamGenerateContent?key={self.config.api_key}"
        )

        # Build contents (WITHOUT system prompt - it goes in systemInstruction)
        contents = self._build_contents(prompt, context)

        # Build full system instruction with anti-repetition rules
        full_system_instruction = ""
        if system_prompt:
            full_system_instruction = system_prompt + GEMINI_OUTPUT_RULES

        # CRITICAL: Temperature MUST be 1.0 for Gemini 3+
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 1.0,  # FORCED to prevent looping
                "maxOutputTokens": self.config.max_output_tokens,
                "topP": self.config.top_p,
                "topK": self.config.top_k,
            },
        }

        # Add native systemInstruction if provided
        if full_system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": full_system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=self.config.stream_timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"❌ API error {response.status_code}: {error_text.decode()[:200]}"
                        return

                    buffer = ""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode("utf-8", errors="ignore")

                        # Parse SSE events
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            # Handle JSON array format from Gemini
                            if line.startswith("[") or line.startswith("{"):
                                text = self._parse_sse_line(line)
                                if text:
                                    yield text

        except httpx.TimeoutException:
            yield f"\n⚠️ Request timed out after {self.config.stream_timeout}s"
        except Exception as e:
            logger.error(f"HTTPX streaming error: {e}")
            yield f"\n❌ Streaming error: {str(e)}"

    def _build_contents(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, Any]]:
        """
        Build contents array for API request.

        NOTE: System prompt is now passed via systemInstruction in payload,
        NOT as a fake user message.
        """
        contents: List[Dict[str, Any]] = []

        if context:
            for msg in context:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        return contents

    def _parse_sse_line(self, line: str) -> Optional[str]:
        """Parse an SSE line and extract text."""
        try:
            data = json.loads(line.rstrip(","))
            if isinstance(data, list):
                data = data[0] if data else {}

            if "candidates" in data:
                text = (
                    data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                )
                return text if text else None

        except json.JSONDecodeError:
            pass

        return None
