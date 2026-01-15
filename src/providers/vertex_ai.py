"""
Vertex AI Gemini Provider

Usa ADC (Application Default Credentials) - sem necessidade de API key.
Inferência via Vertex AI, não Google AI Studio.

Modelos disponíveis:
- gemini-2.5-flash (recomendado)
- gemini-3-flash-preview (future fast)
- gemini-2.5-pro (code optimized)
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
        "flash": "gemini-2.5-flash",          # Current Stable Fast
        "pro": "gemini-2.5-pro",              # Current Stable High-Intel
        "flash-3": "gemini-3-flash-preview",  # Next-Gen Fast (Preview)
        "pro-3": "gemini-3-pro-preview",      # Next-Gen Reasoning (Preview)
        # Aliases
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-3-flash": "gemini-3-flash-preview",
        "gemini-3-pro": "gemini-3-pro-preview",
    }

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "pro",  # Default to 2.5-pro for best quality
    ):
        """Initialize Vertex AI provider.

        Args:
            project: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
            location: Vertex AI location (defaults to us-central1, but 'global' is an option in 2026)
            model_name: Model alias or full name
        """
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_LOCATION", location)
        self.model_name = self.MODELS.get(model_name, model_name)
        self._client = None
        self._model = None

    def _ensure_client(self):
        """Lazy initialize Vertex AI client."""
        if self._client is None:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                # In 2026, we prefer 'global' if supported for cost optimization,
                # but 'us-central1' is still the most stable for features.
                vertexai.init(project=self.project, location=self.location)
                self._model = GenerativeModel(self.model_name)
                self._client = True  # Flag to indicate initialization
                logger.info(f"✅ Vertex AI initialized: {self.model_name} @ {self.location}")

            except ImportError:
                raise RuntimeError(
                    "google-cloud-aiplatform not installed. "
                    "Run: pip install google-cloud-aiplatform"
                )
            except (ImportError, RuntimeError, AttributeError) as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise RuntimeError(f"Vertex AI initialization failed: {e}") from e

    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            self._ensure_client()
            return self._model is not None
        except (ImportError, RuntimeError, AttributeError):
            return False

    def count_tokens(self, text: str) -> int:
        """Count tokens using the official Vertex AI SDK."""
        self._ensure_client()
        try:
            response = self._model.count_tokens(text)
            return response.total_tokens
        except Exception as e:
            logger.warning(f"Failed to count tokens via SDK: {e}. Falling back to heuristic.")
            return len(text) // 4

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

    def _convert_tools(self, tools: Optional[List[Any]]) -> Optional[List]:
        """Convert internal tools to Vertex AI tools."""
        if not tools:
            return None
            
        try:
            from vertexai.generative_models import Tool, FunctionDeclaration
            
            declarations = []
            for tool in tools:
                # Handle both internal Tool objects and raw dictionaries
                schema = tool.get_schema() if hasattr(tool, 'get_schema') else tool
                
                declarations.append(
                    FunctionDeclaration(
                        name=schema['name'],
                        description=schema['description'],
                        parameters=schema['parameters']
                    )
                )
                
            return [Tool(function_declarations=declarations)]
        except ImportError:
            logger.warning("Vertex AI SDK not found, skipping tool conversion")
            return None

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt and tools."""
        self._ensure_client()
        
        # 1. Extract system prompt if present in messages but not provided
        if not system_prompt:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content")
                    break
        
        # 2. Prepare tools
        vertex_tools = self._convert_tools(tools)
        
        # 3. Format messages as structured Content objects (SDK best practice)
        from vertexai.generative_models import Content, Part
        
        contents = []
        for msg in messages:
            role = msg.get("role")
            if role == "system":
                continue
            
            # Map roles to Gemini roles
            gemini_role = "user" if role == "user" else "model"
            
            # Handle tool calls in history
            if "tool_call" in msg:
                # This is a bit complex for a simple refactor, but we should handle it 
                # if we want real multi-turn tool use. 
                # For now, we'll keep it simple as text if it's in the history.
                pass
                
            contents.append(Content(role=gemini_role, parts=[Part.from_text(msg.get("content", ""))]))
        
        loop = asyncio.get_event_loop()

        def _create_stream():
            from vertexai.generative_models import GenerationConfig, GenerativeModel, ToolConfig

            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Force function calling if tools are present
            tool_config = None
            if vertex_tools:
                tool_config = ToolConfig(
                    function_calling_config=ToolConfig.FunctionCallingConfig(
                        mode=ToolConfig.FunctionCallingConfig.Mode.AUTO,
                    )
                )

            # Always create a fresh model instance to ensure tools and system instruction are applied
            model = GenerativeModel(
                self.model_name,
                system_instruction=system_prompt,
                tools=vertex_tools,
                tool_config=tool_config
            )

            return model.generate_content(contents, generation_config=config, stream=True)

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
            
            # Handle Function Calls
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for candidate in chunk.candidates:
                    for part in candidate.content.parts:
                        if part.function_call:
                            import json
                            call_data = {
                                "tool_call": {
                                    "name": part.function_call.name,
                                    "arguments": dict(part.function_call.args)
                                }
                            }
                            yield json.dumps(call_data)
                            continue # Skip text check for this part

            # Handle Text (Safely)
            try:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
            except ValueError:
                # Vertex AI raises ValueError if no text is present (e.g. only function call)
                pass
            
            await asyncio.sleep(0)

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
        return {
            'provider': 'vertex-ai',
            'model': self.model_name,
            'project': self.project,
            'location': self.location,
            'available': self.is_available(),
            'context_window': 2000000 if 'pro' in self.model_name else 1000000, # 2026 Context Windows
            'supports_streaming': True,
            'supports_context_caching': True,
            'cost_tier': 'optimized',
            'speed_tier': 'ultra_fast',
        }
