"Gemini API provider implementation."

import os
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

# Try to import Google exceptions for precise catching
try:
    from google.api_core import exceptions as google_exceptions

    GOOGLE_EXCEPTIONS = (google_exceptions.GoogleAPIError,)
except ImportError:
    GOOGLE_EXCEPTIONS = ()  # type: ignore

logger = logging.getLogger(__name__)

# REMOVED top-level import: import google.generativeai as genai

# Anti-repetition and table formatting suffix added to all system prompts
# Based on: https://ai.google.dev/gemini-api/docs/troubleshooting
GEMINI_OUTPUT_RULES = """

CRITICAL OUTPUT RULES:
- Be concise and direct
- Never repeat yourself
- Never duplicate content horizontally or vertically
- Provide each answer only once
- If you find yourself repeating, STOP and move on

MARKDOWN TABLES - CRITICAL:
- Use EXACTLY 3 hyphens per column: |---|---|---|
- NO extra spaces or padding for visual alignment
- NO tabs - only single spaces
- FOR TABLE HEADINGS, IMMEDIATELY ADD ' |' AFTER THE HEADING
- Keep cell content short (under 30 chars)
"""


class GeminiProvider:
    """Google Gemini API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = None,
        enable_code_execution: bool = False,
        enable_search: bool = False,
        enable_caching: bool = True,
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model name override
            enable_code_execution: Enable native Python sandbox
            enable_search: Enable Google Search grounding
            enable_caching: Enable Context Caching for large contexts
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # Respect GEMINI_MODEL from .env unconditionally (Constitutional compliance)
        default_model = "gemini-2.5-pro"  # Best reasoning model
        self.model_name = model_name or os.getenv("GEMINI_MODEL", default_model)

        # Native Capabilities
        self.enable_code_execution = enable_code_execution
        self.enable_search = enable_search
        self.enable_caching = enable_caching

        self._client = None
        self._genai = None
        self.generation_config = None
        self._cached_content = None

    def _ensure_genai(self):
        """Lazy load genai SDK."""
        if self._genai is None:
            try:
                # Suppress gRPC warnings during import
                import sys
                import io

                _original_stderr = sys.stderr
                sys.stderr = io.StringIO()

                import google.generativeai as genai

                # Restore stderr
                sys.stderr = _original_stderr

                self._genai = genai
                self._genai.configure(api_key=self.api_key)
                self.generation_config = self._genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                )
                logger.info("Lazy loaded google.generativeai")
            except ImportError:
                logger.error("google-generativeai not installed")
                raise RuntimeError("google-generativeai not installed")

    @property
    def client(self):
        """Lazy client initialization."""
        if self._client is None:
            if self.api_key:
                self._ensure_genai()
                try:
                    # Configure Tools
                    tools = []
                    if self.enable_code_execution:
                        tools.append("code_execution")
                    if self.enable_search:
                        tools.append("google_search_retrieval")

                    # Initialize Model with Tools
                    self._client = self._genai.GenerativeModel(
                        self.model_name, tools=tools if tools else None
                    )

                    # FORCE visible confirmation
                    print(f"✅ Gemini Native: {self.model_name}")
                    if self.enable_code_execution:
                        print("   └── 🐍 Native Code Execution: ENABLED")
                    if self.enable_search:
                        print("   └── 🌍 Google Search: ENABLED")

                    logger.info(f"Gemini provider initialized with model: {self.model_name}")
                except (RuntimeError, ValueError, *GOOGLE_EXCEPTIONS) as e:
                    logger.error(f"Failed to initialize Gemini: {e}")
                    self._client = None
        return self._client

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.client is not None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Generate completion from messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("Gemini provider not available")

        try:
            # Convert messages to Gemini format
            prompt = self._format_messages(messages)

            # Generate in thread pool (Gemini SDK is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": temperature,
                    },
                ),
            )

            return response.text

        except (RuntimeError, ValueError, asyncio.TimeoutError, *GOOGLE_EXCEPTIONS) as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages.

        Args:
            messages: List of message dicts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Generated text chunks
        """
        if not self.is_available():
            raise RuntimeError("Gemini provider not available")

        try:
            prompt = self._format_messages(messages)

            # Create generator function for streaming (suppress stderr for gRPC)
            def _stream():
                import sys
                import io

                _original_stderr = sys.stderr
                sys.stderr = io.StringIO()
                try:
                    result = self.client.generate_content(
                        prompt,
                        generation_config={
                            "max_output_tokens": max_tokens,
                            "temperature": temperature,
                        },
                        stream=True,
                    )
                    return result
                finally:
                    sys.stderr = _original_stderr

            # Run streaming in thread pool and yield chunks
            loop = asyncio.get_event_loop()
            response_iterator = await loop.run_in_executor(None, _stream)

            # Yield chunks (run iteration in thread pool to avoid blocking)
            for chunk in response_iterator:
                if chunk.text:
                    yield chunk.text
                    # Small delay to allow other tasks
                    await asyncio.sleep(0)

        except (RuntimeError, ValueError, asyncio.TimeoutError, *GOOGLE_EXCEPTIONS) as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Native Streaming with System Instruction and Tools.
        """
        if not self.is_available():
            raise RuntimeError("Gemini provider not available")

        try:
            # 1. Prepare Builtin Tools
            builtin_tools = []
            if self.enable_code_execution:
                builtin_tools.append("code_execution")
            if self.enable_search:
                builtin_tools.append("google_search_retrieval")

            # 2. Add custom tools if provided
            final_tools = builtin_tools
            
            if tools:
                try:
                    from google.generativeai.types import FunctionDeclaration, Tool
                    
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
                    
                    if declarations:
                        # Create a Tool object for the functions
                        function_tool = Tool(function_declarations=declarations)
                        # google-generativeai expects a list of Tool objects or strings
                        if not final_tools:
                            final_tools = [function_tool]
                        else:
                            # Mix of strings and Tool objects is supported in newer SDKs, 
                            # but explicit separate list is safer. 
                            # However, GenerativeModel.tools accepts iterables.
                            final_tools.append(function_tool)
                            
                except ImportError:
                    logger.warning("google-generativeai not found, skipping custom tool conversion")
                except Exception as e:
                    logger.error(f"Failed to convert custom tools: {e}")

            # 3. Initialize Model (with System Instruction)
            # We create a specific instance for this chat to support dynamic system prompt
            # This is lightweight and ensures we use the native system_instruction

            # Add anti-repetition instructions
            full_system_prompt = (system_prompt or "") + GEMINI_OUTPUT_RULES

            # CRITICAL: Temperature MUST be 1.0 for Gemini 2.5+ to prevent looping
            safe_temperature = 1.0
            if temperature != 1.0:
                # We silently enforce 1.0 for stability as per DeepMind docs
                safe_temperature = 1.0

            model = self._genai.GenerativeModel(
                self.model_name,
                tools=final_tools if final_tools else None,
                system_instruction=full_system_prompt,
            )

            # 3. Prepare History
            history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                content = msg.get("content", "")
                history.append({"role": role, "parts": [content]})

            last_user_msg = messages[-1]["content"] if messages else ""

            # 4. Start Chat
            chat = model.start_chat(history=history)

            # Build tool map for execution
            tool_map = {t.name: t for t in tools} if tools else {}

            # 5. Send Message (Async Wrapper)
            def _send(content, is_function_response=False):
                # If function response, content is the FunctionResponse part
                return chat.send_message(
                    content,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": safe_temperature,
                    },
                    stream=True,
                )

            loop = asyncio.get_event_loop()
            
            # Initial message
            current_message = last_user_msg
            is_func_resp = False
            
            while True:
                # Send current message/response
                # We need to capture the variable locally to use in lambda/func
                msg_to_send = current_message
                is_resp = is_func_resp
                
                response = await loop.run_in_executor(None, lambda: _send(msg_to_send, is_resp))
                response_iterator = iter(response)

                # Process chunks
                def _next_chunk():
                    try:
                        return next(response_iterator)
                    except StopIteration:
                        return None
                    except Exception as e:
                        return e

                function_calls_to_make = []
                
                while True:
                    chunk = await loop.run_in_executor(None, _next_chunk)

                    if chunk is None:
                        break
                    if isinstance(chunk, Exception):
                        raise chunk

                    try:
                        if hasattr(chunk, "parts"):
                            for part in chunk.parts:
                                if hasattr(part, "function_call") and part.function_call:
                                    # Emit tool_call JSON for TUI to parse and execute
                                    fc = part.function_call
                                    logger.info(f"Gemini requested tool: {fc.name}")
                                    
                                    # Convert args to dict
                                    import json
                                    try:
                                        args_dict = dict(fc.args)
                                    except:
                                        args_dict = {}
                                    
                                    # Yield JSON in the format TUI expects
                                    tool_call_json = json.dumps({
                                        "tool_call": {
                                            "name": fc.name,
                                            "arguments": args_dict
                                        }
                                    })
                                    yield tool_call_json
                                    # Mark that we yielded a tool call
                                    function_calls_to_make.append(fc)
                                    
                                elif hasattr(part, "executable_code"):
                                    pass # Native code execution is handled by Gemini backend mostly
                                elif hasattr(part, "code_execution_result"):
                                    pass
                                elif hasattr(part, "text") and part.text:
                                    yield part.text
                        elif hasattr(chunk, "text") and chunk.text:
                            yield chunk.text
                    except (AttributeError, ValueError, KeyError):
                        continue

                    await asyncio.sleep(0)

                # If we emitted function calls, we're done - TUI will handle execution
                # No need for internal tool loop since TUI's ChatController handles it
                if function_calls_to_make:
                    break
                
                # If no function calls, we are done
                break
                
                # Execute Tools and Loop
                from google.ai.generativelanguage_v1beta.types import content as content_types
                
                parts = []
                for fc in function_calls_to_make:
                    tool_name = fc.name
                    tool_args = dict(fc.args)
                    
                    if tool_name in tool_map:
                        try:
                            logger.info(f"Executing tool {tool_name} with args {tool_args}")
                            # Execute tool
                            # Handle both tool signatures (execute vs _execute_validated)
                            tool_instance = tool_map[tool_name]
                            if hasattr(tool_instance, "execute"):
                                result = tool_instance.execute(**tool_args)
                            elif hasattr(tool_instance, "_execute_validated"):
                                result = tool_instance._execute_validated(**tool_args)
                            else:
                                result = f"Error: Tool {tool_name} has no execute method."
                            
                            # Convert result to JSON string/Structure
                            import json
                            result_str = str(result)
                            try:
                                result_json = {"result": result} # Wrap simple result
                            except:
                                result_json = {"result": str(result)}

                            # Create Part for response
                            # Correct way to construct Part with FunctionResponse using protobuf
                            # Usually helpful to use the Part object from SDK
                            from google.generativeai.types import content_types
                            from google.protobuf import struct_pb2
                            
                            result_struct = struct_pb2.Struct()
                            result_struct.update({"output": result_str})

                            part = content_types.Part(
                                function_response=content_types.FunctionResponse(
                                    name=tool_name,
                                    response=result_struct
                                )
                            )
                            parts.append(part)
                            
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")
                            # fallback error response
                            # ...
                            pass
                    else:
                        logger.error(f"Tool {tool_name} not found in map")

                if parts:
                    # Continue the loop with the function responses
                    current_message = parts
                    is_func_resp = True
                    logger.info("Feeding tool results back to Gemini...")
                    continue
                else:
                    break


        except (RuntimeError, ValueError, asyncio.TimeoutError, *GOOGLE_EXCEPTIONS) as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"\n[System Error: {str(e)}]"

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Gemini.

        Gemini uses a simpler prompt format than chat APIs.
        We concatenate messages with role prefixes.
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")

        return "\n\n".join(formatted)

    def get_model_info(self) -> Dict[str, str | bool | int]:
        """Get model information."""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "available": self.is_available(),
            "context_window": 32768,  # Gemini Pro context
            "supports_streaming": True,
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens using native API.

        Args:
            text: Text to count tokens for

        Returns:
            Exact token count from Gemini API
        """
        if not self.is_available():
            return len(text) // 4

        try:
            # Use native count_tokens
            return self.client.count_tokens(text).total_tokens
        except (AttributeError, ValueError, RuntimeError, *GOOGLE_EXCEPTIONS) as e:
            logger.warning(f"Native token count failed, falling back to estimation: {e}")
            return len(text) // 4
