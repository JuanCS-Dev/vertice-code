"""
Anthropic Claude via Google Vertex AI Provider

Permite usar modelos Claude 4.5 (Sonnet/Opus) via Google Cloud Vertex AI.

Requer: `pip install "anthropic[vertex]"`
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
import logging

logger = logging.getLogger(__name__)


class AnthropicVertexProvider:
    """
    Anthropic Vertex AI Provider.

    Uses the Anthropic SDK with Vertex AI backend.
    Inherits authentication from Google Cloud (ADC).
    """

    MODELS = {
        "sonnet-4.5": "claude-sonnet-4-5@20250929",
        "opus-4.5": "claude-opus-4-5@20251101",
        # Aliases
        "sonnet": "claude-sonnet-4-5@20250929",
        "opus": "claude-opus-4-5@20251101",
    }
    _ALLOWED_MODEL_IDS = set(MODELS.values())

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "global",  # Global endpoint for lower cost and availability
        model_name: str = "sonnet-4.5",  # Default to user-confirmed 4.5
        enable_caching: bool = True,
    ):
        """Initialize Anthropic Vertex provider.

        Args:
            project: GCP project ID
            location: Vertex AI location
            model_name: Model alias or full name
            enable_caching: Enable Prompt Caching (90% discount on cached tokens)
        """
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = self.MODELS.get(model_name, model_name)
        if self.model_name not in self._ALLOWED_MODEL_IDS:
            raise ValueError(
                "Unsupported Claude model for 2026 Google-native mode. "
                f"Got: {self.model_name!r}. Allowed: {sorted(self._ALLOWED_MODEL_IDS)}"
            )
        self.enable_caching = enable_caching
        self._client = None

    def _ensure_client(self):
        """Lazy initialize Anthropic Vertex client."""
        if self._client is None:
            try:
                from anthropic import AnthropicVertex

                # Usar regional endpoint por padrão, mas permitir override via env
                # Em 2026, 'global' pode ser uma opção para custo reduzido em algumas regiões
                self._client = AnthropicVertex(
                    project_id=self.project,
                    region=os.getenv("ANTHROPIC_VERTEX_LOCATION", self.location),
                )
                logger.info(f"✅ Anthropic Vertex initialized: {self.model_name} @ {self.location}")
            except ImportError:
                raise RuntimeError(
                    'anthropic[vertex] not installed. Run: pip install "anthropic[vertex]"'
                )
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic Vertex: {e}")
                raise RuntimeError(f"Anthropic Vertex initialization failed: {e}")

    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            self._ensure_client()
            return self._client is not None
        except (ImportError, RuntimeError):
            return False

            # Test if model is accessible by making a minimal request
            # This will fail with 404 if model not enabled in project
            import asyncio

            loop = asyncio.new_event_loop()
            try:
                # Quick test with minimal tokens and simple message
                test_params = {
                    "model": self.model_name,
                    "max_tokens": 1,  # Minimal tokens
                    "temperature": 0.0,
                    "messages": [{"role": "user", "content": "test"}],
                }
                loop.run_until_complete(
                    loop.run_in_executor(None, lambda: self._client.messages.create(**test_params))
                )
                return True
            except Exception as e:
                if "404" in str(e) or "Not Found" in str(e) or "not found" in str(e).lower():
                    logger.warning(
                        f"Claude model {self.model_name} not enabled in Vertex AI project"
                    )
                    return False
                # For other errors (rate limits, etc.), consider available
                logger.debug(f"Claude model test failed with non-404 error: {e}")
                return True
            finally:
                loop.close()
        except (ImportError, RuntimeError):
            return False

    def _apply_caching(
        self, system_prompt: str, messages: List[Dict[str, Any]]
    ) -> tuple[Any, List[Dict[str, Any]]]:
        """Apply Prompt Caching markers to system prompt and messages."""
        if not self.enable_caching:
            return system_prompt, messages

        # System prompt is the best candidate for caching
        cached_system = None
        if system_prompt:
            cached_system = [
                {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
            ]

        # Cache the last large user message if applicable (Anthropic supports up to 4 cache breakpoints)
        processed_messages = []
        for i, msg in enumerate(messages):
            content = msg["content"]
            # If it's the last message and it's from the user and it's significant
            if i == len(messages) - 1 and msg["role"] == "user" and len(content) > 2048:
                processed_messages.append(
                    {
                        "role": msg["role"],
                        "content": [
                            {
                                "type": "text",
                                "text": content,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                    }
                )
            else:
                processed_messages.append(msg)

        return cached_system, processed_messages

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        effort: Optional[str] = None,  # Claude 4.5 parameter
        **kwargs,
    ) -> str:
        """Generate completion from messages."""
        self._ensure_client()

        # Extract system prompt
        system_prompt = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append({"role": msg["role"], "content": msg["content"]})

        # Apply Caching
        cached_system, cached_messages = self._apply_caching(system_prompt, user_messages)

        loop = asyncio.get_event_loop()

        def _generate():
            # Prepare base parameters
            params = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": (
                    cached_system if cached_system else (system_prompt if system_prompt else None)
                ),
                "messages": cached_messages,
                **kwargs,
            }

            # Add effort if provided (and model supports it)
            if effort and "4.5" in self.model_name:
                params["effort"] = effort

            response = self._client.messages.create(**params)
            return response.content[0].text

        return await loop.run_in_executor(None, _generate)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None,
        effort: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat with Claude."""
        self._ensure_client()

        # Filter and prepare messages
        user_messages = []
        actual_system = system_prompt
        for msg in messages:
            if msg["role"] == "system":
                if not actual_system:
                    actual_system = msg["content"]
            else:
                user_messages.append({"role": msg["role"], "content": msg["content"]})

        # Apply Caching
        cached_system, cached_messages = self._apply_caching(actual_system or "", user_messages)

        # Tool conversion
        anthropic_tools = self._convert_tools(tools)

        loop = asyncio.get_event_loop()

        def _create_stream():
            params = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": (
                    cached_system if cached_system else (actual_system if actual_system else None)
                ),
                "messages": cached_messages,
                "stream": True,
                **kwargs,
            }

            # Only add tools if provided
            if anthropic_tools:
                params["tools"] = anthropic_tools
                # Tell Claude to prefer using tools when appropriate
                params["tool_choice"] = {"type": "auto"}

            if effort and "4.5" in self.model_name:
                params["effort"] = effort

            return self._client.messages.create(**params)

        stream = await loop.run_in_executor(None, _create_stream)

        import json

        # Track tool use blocks
        current_tool_input = {}  # id -> partial JSON

        for event in stream:
            if event.type == "content_block_start":
                # Start of a tool_use block
                if hasattr(event, "content_block") and event.content_block.type == "tool_use":
                    tool_block = event.content_block
                    current_tool_input[tool_block.id] = {"name": tool_block.name, "input": ""}
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    yield event.delta.text
                elif event.delta.type == "input_json_delta":
                    # Accumulate tool input JSON
                    if hasattr(event, "index"):
                        # Find the tool by index or just use first
                        for tool_id in current_tool_input:
                            current_tool_input[tool_id]["input"] += event.delta.partial_json
            elif event.type == "content_block_stop":
                # End of a tool_use block - emit complete tool call
                for tool_id, tool_data in list(current_tool_input.items()):
                    try:
                        # Parse the accumulated JSON input
                        tool_args = json.loads(tool_data["input"]) if tool_data["input"] else {}
                        # Emit in the same format as VertexAIProvider
                        tool_call_json = json.dumps(
                            {"tool_call": {"name": tool_data["name"], "arguments": tool_args}}
                        )
                        yield tool_call_json
                        logger.info(f"Claude tool call: {tool_data['name']}")
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool input JSON: {tool_data['input']}")
                    del current_tool_input[tool_id]
            elif event.type == "message_start":
                # Could log usage here
                pass
            elif event.type == "message_delta":
                # Could log stop reason here
                pass
            await asyncio.sleep(0)

    def _convert_tools(self, tools: Optional[List[Any]]) -> Optional[List[Dict]]:
        """Convert internal tools to Anthropic tool schema."""
        if not tools:
            return None

        anthropic_tools = []
        for tool in tools:
            schema = tool.get_schema() if hasattr(tool, "get_schema") else tool
            anthropic_tools.append(
                {
                    "name": schema["name"],
                    "description": schema["description"],
                    "input_schema": schema["parameters"],
                }
            )
        return anthropic_tools

    def get_model_info(self) -> Dict[str, Any]:
        """Get model info optimized for Vertice Router."""
        return {
            "provider": "anthropic-vertex",
            "model": self.model_name,
            "available": self.is_available(),
            "context_window": 300000 if "4.5" in self.model_name else 200000,
            "supports_streaming": True,
            "supports_prompt_caching": True,  # 90% discount!
            "speed_tier": "fast" if "haiku" in self.model_name else "normal",
            "cost_tier": "optimized" if self.enable_caching else "premium",
        }
