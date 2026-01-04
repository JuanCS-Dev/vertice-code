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

import base64
import os
import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
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
        "pro": "gemini-3-pro-preview",  # Reasoning-first, 1M context, agentic
        "flash": "gemini-2.0-flash",  # Multimodal, complex understanding
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
        enable_grounding: bool = False,  # Google Search grounding
    ):
        """Initialize Vertex AI provider.

        Args:
            project: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
            location: Vertex AI location (gemini-2.5-flash only in us-central1)
            model_name: Model alias or full name
            enable_grounding: Enable Google Search grounding by default
        """
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = self.MODELS.get(model_name, model_name)
        self.enable_grounding = enable_grounding
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

    def set_grounding(self, enabled: bool = True) -> None:
        """Toggle Google Search grounding at runtime.

        Args:
            enabled: Whether to enable grounding
        """
        self.enable_grounding = enabled
        logger.info(f"Google Search grounding {'enabled' if enabled else 'disabled'}")

    def _get_grounding_tool(self) -> Optional[Any]:
        """Get Google Search grounding tool.

        Returns:
            Tool instance for Google Search grounding, or None if unavailable.
        """
        try:
            from vertexai.generative_models import Tool, grounding

            # Use from_google_search_retrieval for Vertex AI SDK
            # Note: For Gemini 2.0+ models, API may require different field
            return Tool.from_google_search_retrieval(
                google_search_retrieval=grounding.GoogleSearchRetrieval()
            )
        except ImportError:
            logger.warning("Vertex AI grounding SDK not available")
            return None
        except Exception as e:
            logger.warning(f"Failed to create grounding tool: {e}")
            return None

    def _format_content_parts(self, content: Any) -> List[Any]:
        """Convert content to Vertex AI Parts for multimodal support.

        Args:
            content: Can be:
                - str: Plain text
                - dict: Content block (text or image)
                - list: Mixed content blocks
                - None: Returns empty list

        Returns:
            List of Part objects for Vertex AI
        """
        if content is None:
            return []

        try:
            from vertexai.generative_models import Part

            # String content -> text part
            if isinstance(content, str):
                return [Part.from_text(content)]

            # Single content block (dict)
            if isinstance(content, dict):
                block_type = content.get("type")

                if block_type == "text":
                    return [Part.from_text(content.get("text", ""))]

                if block_type == "image":
                    source = content.get("source", {})
                    if source.get("type") == "base64":
                        image_data = base64.b64decode(source.get("data", ""))
                        mime_type = source.get("media_type", "image/png")
                        return [Part.from_data(data=image_data, mime_type=mime_type)]

                # Unknown block type, convert to text
                return [Part.from_text(str(content))]

            # List of content blocks
            if isinstance(content, list):
                parts = []
                for item in content:
                    parts.extend(self._format_content_parts(item))
                return parts

            # Fallback: convert to string
            return [Part.from_text(str(content))]

        except ImportError:
            logger.warning("Vertex AI SDK not available for content formatting")
            return []

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
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

                model = GenerativeModel(self.model_name, system_instruction=system_prompt)
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
        **kwargs,
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
                model = GenerativeModel(self.model_name, system_instruction=system_prompt)
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
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text
            await asyncio.sleep(0)

    def _convert_tools(self, tools: Optional[List[Any]]) -> Optional[List]:
        """Convert internal tools to Vertex AI format.

        Args:
            tools: List of tool schemas (dict) or Tool objects with get_schema()

        Returns:
            List with single Tool containing all FunctionDeclarations, or None
        """
        if not tools:
            return None

        try:
            from vertexai.generative_models import Tool, FunctionDeclaration

            declarations = []
            for tool in tools:
                # Handle both internal Tool objects and raw dictionaries
                schema = tool.get_schema() if hasattr(tool, "get_schema") else tool

                declarations.append(
                    FunctionDeclaration(
                        name=schema["name"],
                        description=schema["description"],
                        parameters=schema["parameters"],
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
        tool_config: Optional[str] = "AUTO",
        enable_grounding: Optional[bool] = None,
        cached_content: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt and native function calling.

        Args:
            messages: Conversation messages
            system_prompt: Optional system instruction
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            tools: List of tool schemas for native function calling
            tool_config: Function calling mode (AUTO, ANY, NONE)
            enable_grounding: Override instance grounding setting (None = use instance default)
            cached_content: Cache resource name for explicit caching (90% cost reduction)
            **kwargs: Additional arguments

        Yields:
            Text chunks or JSON function call objects
        """
        self._ensure_client()

        # Extract system prompt if present in messages but not provided
        if not system_prompt:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content")
                    break

        # Determine grounding: parameter overrides instance default
        use_grounding = enable_grounding if enable_grounding is not None else self.enable_grounding

        # Build combined tools list
        all_tools: List[Any] = []

        # Add function calling tools if provided
        vertex_tools = self._convert_tools(tools)
        if vertex_tools:
            all_tools.extend(vertex_tools)

        # Add grounding tool if enabled
        if use_grounding:
            grounding_tool = self._get_grounding_tool()
            if grounding_tool:
                all_tools.append(grounding_tool)
                logger.debug("Google Search grounding tool added")

        # Use combined tools or None if empty
        final_tools = all_tools if all_tools else None

        # Format messages as structured Content objects (SDK best practice)
        from vertexai.generative_models import Content, Part

        contents = []
        for msg in messages:
            role = msg.get("role")
            if role == "system":
                continue

            # Map roles to Gemini roles
            gemini_role = "user" if role == "user" else "model"

            # Use _format_content_parts for multimodal support (images, etc.)
            msg_content = msg.get("content", "")
            parts = self._format_content_parts(msg_content)
            if parts:
                contents.append(Content(role=gemini_role, parts=parts))

        loop = asyncio.get_event_loop()

        def _create_stream():
            from vertexai.generative_models import GenerationConfig, GenerativeModel, ToolConfig

            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            # Configure function calling mode (only if function calling tools present)
            vertex_tool_config = None
            if vertex_tools:  # Only set tool_config for function calling tools
                mode_map = {
                    "AUTO": ToolConfig.FunctionCallingConfig.Mode.AUTO,
                    "ANY": ToolConfig.FunctionCallingConfig.Mode.ANY,
                    "NONE": ToolConfig.FunctionCallingConfig.Mode.NONE,
                }
                mode = mode_map.get(tool_config, ToolConfig.FunctionCallingConfig.Mode.AUTO)
                vertex_tool_config = ToolConfig(
                    function_calling_config=ToolConfig.FunctionCallingConfig(mode=mode)
                )

            # Create model - use from_cached_content if cache provided (90% cost reduction)
            if cached_content:
                logger.debug(f"Using cached content: {cached_content}")
                model = GenerativeModel.from_cached_content(cached_content)
            else:
                model = GenerativeModel(
                    self.model_name,
                    system_instruction=system_prompt,
                    tools=final_tools,  # Combined: function tools + grounding tool
                    tool_config=vertex_tool_config,
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

            # Handle Function Calls (native response)
            if hasattr(chunk, "candidates") and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call") and part.function_call:
                                call_data = {
                                    "tool_call": {
                                        "name": part.function_call.name,
                                        "arguments": dict(part.function_call.args),
                                    }
                                }
                                yield json.dumps(call_data)
                                continue  # Skip text check for this part

            # Handle Text (Safely)
            try:
                if hasattr(chunk, "text") and chunk.text:
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
        # Gemini 3 has 1M context for all models
        context_window = 1_000_000 if "3" in self.model_name else 128_000
        return {
            "provider": "vertex-ai",
            "model": self.model_name,
            "project": self.project,
            "location": self.location,
            "available": self.is_available(),
            "context_window": context_window,
            "supports_streaming": True,
            "supports_thinking": "3-pro" in self.model_name,  # Gemini 3 Pro has thinking
            "cost_tier": "enterprise",  # R$8000 credits!
            "speed_tier": "ultra_fast",
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        # Gemini tokenizer is roughly 4 chars per token
        return len(text) // 4
