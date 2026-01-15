"""Google Gemini API Provider (AI Studio / Free Tier)\nStandalone implementation to avoid circular dependencies with src/providers.\n"""

import os
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class GeminiProvider:
    """Google Gemini API provider via AI Studio (google.generativeai)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro-latest",
        **kwargs
    ):
        """Initialize Gemini provider."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None
        self._genai = None

    def _ensure_client(self):
        """Lazy load genai SDK."""
        if self._genai is None:
            try:
                import google.generativeai as genai
                self._genai = genai
                
                if self.api_key:
                    genai.configure(api_key=self.api_key)
                
                self._client = genai.GenerativeModel(self.model_name)
                # logger.info(f"✅ Gemini (AI Studio) initialized: {self.model_name}")
            except ImportError:
                # logger.error("google-generativeai not installed.")
                raise RuntimeError("google-generativeai not installed")
            except Exception as e:
                # logger.error(f"Gemini init failed: {e}")
                pass

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self._ensure_client()
        if not self._client:
            raise RuntimeError("Gemini client not initialized")
            
        prompt = self._format_messages(messages)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self._client.generate_content(prompt)
        )
        return response.text

    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        self._ensure_client()
        if not self._client:
            yield "Error: Gemini client not initialized"
            return

        prompt = self._format_messages(messages)
        
        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(
            None,
            lambda: self._client.generate_content(prompt, stream=True)
        )
        
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                await asyncio.sleep(0)

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        # Simple implementation reusing stream_generate for now
        async for chunk in self.stream_generate(messages, **kwargs):
            yield chunk

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        return "\n\n".join(formatted)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model_name,
            "available": self.is_available()
        }
