"""
Vertex AI Gemini Provider

Usa ADC (Application Default Credentials) - sem necessidade de API key.
Inferência via Vertex AI, não Google AI Studio.

Modelos disponíveis:
- gemini-2.5-flash (Legacy SDK)
- gemini-3-flash-preview (Native SDK)
- gemini-3-pro-preview (Native SDK)
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any, Union
import logging
import json

# Configure Logging
logger = logging.getLogger(__name__)

# --- SDK IMPORTS ---
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
    from vertexai.generative_models import (
        GenerativeModel, Part, Content, 
        GenerationConfig, ToolConfig
    )
    HAS_LEGACY_SDK = True
except ImportError:
    pass

class VertexAIProvider:
    """
    Vertex AI Gemini Provider - Hybrid Architecture.
    
    Supports:
    - Gemini 2.5 (via Legacy SDK `vertexai`)
    - Gemini 3.0 (via New SDK `google-genai` with `global` location)
    """

    MODELS = {
        # Legacy (v2)
        "flash": "gemini-2.5-flash",          
        "pro": "gemini-2.5-pro",              
        
        # Native (v3)
        "flash-3": "gemini-3-flash-preview",  
        "pro-3": "gemini-3-pro-preview",      
        "gemini-3-pro": "gemini-3-pro-preview",
        "gemini-3-flash": "gemini-3-flash-preview",
        
        # Aliases
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-pro": "gemini-2.5-pro",
    }

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "pro", 
    ):
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_LOCATION", location)
        self.model_alias = model_name
        self.model_id = self.MODELS.get(model_name, model_name)
        
        # State
        self._legacy_model = None
        self._genai_client = None
        
        # Determine Mode
        self.is_gemini_3 = "gemini-3" in self.model_id
        
        # Validation
        if self.is_gemini_3 and not HAS_GENAI_SDK:
            logger.warning(
                "Gemini 3 requested but `google-genai` SDK missing. "
                "Install with `pip install google-genai`. "
                "Falling back to legacy SDK (may fail)."
            )
            self.is_gemini_3 = False # Fallback attempt

    def _init_genai_client(self):
        """Initialize Google GenAI Client (v3)."""
        if not self._genai_client and HAS_GENAI_SDK:
            # Gemini 3 Preview often requires 'global' location
            loc = "global" if "preview" in self.model_id else self.location
            
            try:
                self._genai_client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=loc
                )
                logger.info(f"✅ GenAI Client (v3) initialized: {self.model_id} @ {loc}")
            except Exception as e:
                logger.error(f"GenAI Init Failed: {e}")
                raise

    def _init_legacy_model(self):
        """Initialize Legacy Vertex AI Model (v2)."""
        if not self._legacy_model and HAS_LEGACY_SDK:
            try:
                vertexai.init(project=self.project, location=self.location)
                self._legacy_model = GenerativeModel(self.model_id)
                logger.info(f"✅ Legacy Vertex Model initialized: {self.model_id} @ {self.location}")
            except Exception as e:
                logger.error(f"Legacy Init Failed: {e}")
                raise

    def count_tokens(self, text: str) -> int:
        """Estimate tokens (SDK count is async/complex to bridge)."""
        return len(text) // 4

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Unified Single-Turn Generation."""
        # Wrap simple prompt into message format and delegate
        messages = [{"role": "user", "content": prompt}]
        if system_instruction:
            # Prepend system instruction as internal context if needed
            # But stream_chat handles it better.
            pass 
            
        async for chunk in self.stream_chat(
            messages=messages,
            system_prompt=system_instruction,
            **kwargs
        ):
            yield chunk

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Unified Chat Stream."""
        
        # 1. Extract system prompt from messages if not explicit
        if not system_prompt:
            start_idx = 0
            if messages and messages[0]["role"] == "system":
                system_prompt = messages[0]["content"]
                start_idx = 1
            messages = messages[start_idx:]

        # 2. Route to correct handler
        if self.is_gemini_3:
            self._init_genai_client()
            async for chunk in self._stream_chat_v3(
                messages, system_prompt, max_tokens, temperature, tools
            ):
                yield chunk
        else:
            self._init_legacy_model()
            async for chunk in self._stream_chat_v2(
                messages, system_prompt, max_tokens, temperature, tools
            ):
                yield chunk

    async def _stream_chat_v3(
        self, messages, system_prompt, max_tokens, temperature, tools
    ):
        """Gemini 3 Handler (New SDK)."""
        try:
            # Config
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                # Tools would go here (v3 supports tool_config)
            )
            
            # Convert Messages
            # v3 expects structured content or simple dicts
            contents = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                ))

            loop = asyncio.get_running_loop()
            
            # Execute (Sync SDK -> Async Wrapper)
            # stream=True returns an iterator
            def _run_stream():
                return self._genai_client.models.generate_content_stream(
                    model=self.model_id,
                    contents=contents,
                    config=config
                )

            stream_iter = await loop.run_in_executor(None, _run_stream)
            
            # Iterate
            # Note: The iterator yields chunks. We need to run iteration in executor too 
            # OR assume it's fast enough. 
            # The v3 SDK iterator is synchronous.
            
            for chunk in stream_iter:
                if chunk.text:
                    yield chunk.text
                    # Small yield to let event loop breathe
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Gemini 3 Error: {e}")
            yield f"[Error: {str(e)}]"

    async def _stream_chat_v2(
        self, messages, system_prompt, max_tokens, temperature, tools
    ):
        """Gemini 2.5 Handler (Legacy SDK)."""
        try:
            # Convert Tools (Legacy)
            vertex_tools = self._convert_tools_v2(tools)
            
            # Prepare Model
            # Re-init for system instruction change
            model = GenerativeModel(
                self.model_id,
                system_instruction=system_prompt,
                tools=vertex_tools
            )
            
            # Convert History
            history = []
            last_msg = messages[-1]["content"] if messages else ""
            
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))

            chat = model.start_chat(history=history)
            
            # Config
            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            responses = await chat.send_message_async(
                last_msg, 
                generation_config=config, 
                stream=True
            )
            
            async for chunk in responses:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
             logger.error(f"Gemini 2.5 Error: {e}")
             yield f"[Error: {str(e)}]"

    def _convert_tools_v2(self, tools):
        """Legacy Tool Conversion."""
        if not tools or not HAS_LEGACY_SDK: return None
        try:
            from vertexai.generative_models import Tool, FunctionDeclaration
            declarations = []
            for tool in tools:
                schema = tool.get_schema() if hasattr(tool, 'get_schema') else tool
                declarations.append(FunctionDeclaration(
                    name=schema['name'],
                    description=schema['description'],
                    parameters=schema['parameters']
                ))
            return [Tool(function_declarations=declarations)]
        except:
            return None

    def get_model_info(self):
        return {
            "provider": "vertex-ai",
            "model": self.model_id,
            "sdk": "v3-native" if self.is_gemini_3 else "v2-legacy",
            "project": self.project,
            "location": self.location
        }
