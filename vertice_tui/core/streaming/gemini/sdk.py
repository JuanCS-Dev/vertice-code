"""
Gemini SDK Streamer - google-generativeai implementation.

Optimized for Gemini 2.5+ (Nov 2025).

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from .config import GeminiStreamConfig
from .base import BaseStreamer

logger = logging.getLogger(__name__)


class GeminiSDKStreamer(BaseStreamer):
    """
    Streamer using google-generativeai SDK.

    OPTIMIZED for Gemini 2.5+ (Nov 2025):
    - Uses native system_instruction parameter
    - Temperature locked at 1.0 to prevent looping
    - Anti-repetition instructions embedded
    """

    def __init__(self, config: GeminiStreamConfig) -> None:
        """Initialize SDK streamer."""
        super().__init__(config)
        self._genai: Any = None  # google.generativeai module
        self._generation_config: Any = None
        self._cached_system_prompt: Optional[str] = None
        self._model: Any = None

    async def initialize(self) -> bool:
        """Initialize the Gemini SDK."""
        if self._initialized:
            return True

        try:
            import google.generativeai as genai
            self._genai = genai
            genai.configure(api_key=self.config.api_key)

            # CRITICAL: Temperature MUST be 1.0 for Gemini 2.5+
            safe_temperature = 1.0
            if self.config.temperature != 1.0:
                logger.warning(
                    f"Temperature {self.config.temperature} overridden to 1.0 "
                    "to prevent Gemini 2.5+ looping behavior"
                )

            self._generation_config = genai.GenerationConfig(
                temperature=safe_temperature,
                max_output_tokens=self.config.max_output_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )

            self._initialized = True
            logger.info(
                f"GeminiSDKStreamer initialized: model={self.config.model_name}, "
                f"temperature=1.0 (forced), max_tokens={self.config.max_output_tokens}"
            )
            return True

        except ImportError as e:
            logger.warning(f"google-generativeai not available: {e}")
            return False
        except Exception as e:
            logger.error(f"SDK initialization failed: {e}")
            return False

    def _get_model_with_system_instruction(self, system_prompt: str) -> Any:
        """
        Get or create model with native system_instruction.

        Uses caching to avoid recreating model for same system prompt.
        """
        full_system_prompt = system_prompt

        # Check if we need to create new model (system prompt changed)
        if self._model is None or self._cached_system_prompt != full_system_prompt:
            self._cached_system_prompt = full_system_prompt

            # Create model with native system_instruction
            self._model = self._genai.GenerativeModel(
                self.config.model_name,
                generation_config=self._generation_config,
                system_instruction=full_system_prompt if full_system_prompt else None,
            )
            logger.debug(f"Created model with system_instruction ({len(full_system_prompt)} chars)")

        return self._model

    def _convert_protobuf_args(self, args: Any) -> Dict[str, Any]:
        """
        Convert protobuf MapComposite/RepeatedComposite to regular Python dict.

        Handles nested structures and various protobuf types.
        """
        if args is None:
            return {}

        result: Dict[str, Any] = {}
        try:
            # Try to iterate as a map
            items = None
            if hasattr(args, 'items'):
                items = args.items()
            elif hasattr(args, '__iter__') and not isinstance(args, (str, bytes)):
                try:
                    items_list = list(args)
                    if items_list and isinstance(items_list[0], tuple) and len(items_list[0]) == 2:
                        items = items_list
                    else:
                        items = None
                except Exception as e:
                    logger.debug(f"Protobuf items extraction failed: {e}")
                    items = None

            if items:
                for key, value in items:
                    # Recursively convert nested structures
                    if hasattr(value, 'items') or (
                        hasattr(value, '__iter__') and not isinstance(value, (str, bytes, int, float, bool))
                    ):
                        try:
                            result[key] = self._convert_protobuf_args(value)
                        except Exception as e:
                            logger.debug(f"Nested protobuf conversion for {key} failed: {e}")
                            result[key] = str(value)
                    else:
                        # Convert to native Python type
                        if hasattr(value, 'string_value'):
                            result[key] = value.string_value
                        elif hasattr(value, 'number_value'):
                            result[key] = value.number_value
                        elif hasattr(value, 'bool_value'):
                            result[key] = value.bool_value
                        else:
                            result[key] = value
            else:
                # Fallback: try direct dict conversion
                result = dict(args) if args else {}
        except Exception as e:
            logger.debug(f"Protobuf conversion fallback: {e}")
            try:
                result = {"_raw": str(args)}
            except Exception as e2:
                logger.debug(f"Final protobuf fallback failed: {e2}")
                result = {}

        return result

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream using google-generativeai SDK with native system_instruction."""
        if not self._initialized:
            yield "❌ SDK not initialized"
            return

        # Get model with proper system instruction
        model = self._get_model_with_system_instruction(system_prompt)

        # Build contents for conversation (WITHOUT system prompt - it's native now)
        contents = self._build_contents(prompt, context)

        # Run in executor since SDK is sync
        loop = asyncio.get_event_loop()

        def _generate() -> Any:
            kwargs: Dict[str, Any] = {"stream": True}
            if tools:
                kwargs["tools"] = tools
                try:
                    from google.generativeai.types import content_types
                    kwargs["tool_config"] = content_types.to_tool_config({
                        "function_calling_config": {"mode": "AUTO"}
                    })
                    logger.debug(f"Tool config set to AUTO mode with {len(tools)} tools")
                except Exception as e:
                    logger.warning(f"Could not set tool_config: {e}")
            return model.generate_content(
                contents if len(contents) > 1 else prompt,
                **kwargs
            )

        try:
            response = await loop.run_in_executor(None, _generate)
            response_iterator = iter(response)

            def _next_chunk() -> Any:
                try:
                    return next(response_iterator)
                except StopIteration:
                    return None
                except Exception as e:
                    return e

            while True:
                chunk = await loop.run_in_executor(None, _next_chunk)

                if chunk is None:
                    break
                if isinstance(chunk, Exception):
                    raise chunk

                async for text in self._process_chunk(chunk):
                    if text:
                        yield text

                # Small sleep to force Gradio websocket flush
                await asyncio.sleep(0.002)

        except Exception as e:
            logger.error(f"SDK streaming error: {e}")
            yield f"\n❌ Streaming error: {str(e)}"

    def _build_contents(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, Any]]:
        """
        Build contents array for multi-turn conversation.

        NOTE: System prompt is now passed via native system_instruction,
        NOT as a fake user message.
        """
        contents: List[Dict[str, Any]] = []

        # Add conversation context if provided
        if context:
            for msg in context:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })

        # Add current prompt
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        return contents

    async def _process_chunk(self, chunk: Any) -> AsyncIterator[str]:
        """Process a single response chunk. Deduplicated."""
        yielded = False

        if hasattr(chunk, 'candidates') and chunk.candidates:
            for candidate in chunk.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            args = self._convert_protobuf_args(fc.args)
                            try:
                                args_json = json.dumps(args)
                            except (TypeError, ValueError):
                                args_json = "{}"
                            yield f"[TOOL_CALL:{fc.name}:{args_json}]"
                            yielded = True
                        elif hasattr(part, 'text') and part.text:
                            yield part.text
                            yielded = True

        # Fallback ONLY if nothing yielded from candidates
        if not yielded and hasattr(chunk, 'text') and chunk.text:
            yield chunk.text
