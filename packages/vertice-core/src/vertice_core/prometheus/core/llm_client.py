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
from typing import AsyncIterator, Optional, List, Deque, Any
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
        "pro": "gemini-3-flash",
        "thinking": "gemini-3-flash",
        "fallback": "gemini-3-flash-preview",
    }

    def __init__(
        self,
        model: str = "gemini-3-flash",
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
        tools: Optional[List[Any]] = None,
    ) -> str:
        """Standardized Generate with Automatic Tool Use."""
        full_response = ""
        async for chunk in self.generate_stream(
            prompt=prompt, system_prompt=system_prompt, include_history=include_history, tools=tools
        ):
            if not chunk.startswith("\n[Executing") and not chunk.startswith("[Result:"):
                full_response += chunk
        return full_response

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        include_history: bool = False,
        tools: Optional[List[Any]] = None,
    ) -> AsyncIterator[str]:
        """Standardized Streaming with Automatic Tool Use (2026 Pattern)."""

        # Prepare contents
        contents = []
        if include_history:
            for msg in self.conversation_history:
                if msg.role != "system":
                    contents.append(
                        types.Content(role=msg.role, parts=[types.Part.from_text(text=msg.content)])
                    )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        # 1. Configure Config and Tools
        sys_instr = None
        if system_prompt:
            sys_instr = [types.Part.from_text(text=system_prompt)]

        # Register Tool Callables for Auto-Execution
        vertex_tools = []
        tool_instances = {}
        if tools:
            functions = []
            for t in tools:
                if hasattr(t, "get_schema"):
                    schema = t.get_schema()
                    name = getattr(t, "name", None) or schema.get("name", "unknown_tool")
                    name = name.replace("-", "_")
                    tool_instances[name] = t
                    functions.append(
                        types.FunctionDeclaration(
                            name=name,
                            description=schema.get("description", ""),
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    k: types.Schema(
                                        type=v.get("type", "string").upper(),
                                        description=v.get("description", ""),
                                    )
                                    for k, v in schema.get("parameters", {})
                                    .get("properties", {})
                                    .items()
                                },
                                required=schema.get("parameters", {}).get("required", []),
                            ),
                        )
                    )
            if functions:
                vertex_tools = [types.Tool(function_declarations=functions)]

        config = self.config.to_vertex_config()
        config.system_instruction = sys_instr
        if vertex_tools:
            config.tools = vertex_tools
            config.tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )

        # 2. Multi-turn Auto-Execution Loop
        try:
            max_turns = 5
            current_turn = 0
            full_text_acc = ""

            while current_turn < max_turns:
                current_turn += 1
                response = await self._client.aio.models.generate_content(
                    model=self.model_name, contents=contents, config=config
                )

                if response.candidates:
                    contents.append(response.candidates[0].content)
                    has_tool_call = False

                    for part in response.candidates[0].content.parts:
                        # Handle Text
                        if hasattr(part, "text") and part.text:
                            full_text_acc += part.text
                            yield part.text

                        # Handle Tool Call
                        f_call = getattr(part, "function_call", None)
                        if f_call:
                            has_tool_call = True
                            tool_name = f_call.name

                            args = {}
                            if f_call.args:
                                for k, v in f_call.args.items():
                                    args[k] = v

                            yield f"\n[Executing Tool: {tool_name}]...\n"

                            if tool_name in tool_instances:
                                try:
                                    t_res = await tool_instances[tool_name]._execute_validated(
                                        **args
                                    )
                                    output = (
                                        t_res.data if t_res.success else f"Error: {t_res.error}"
                                    )
                                    contents.append(
                                        types.Content(
                                            role="user",
                                            parts=[
                                                types.Part.from_function_response(
                                                    name=tool_name, response={"result": output}
                                                )
                                            ],
                                        )
                                    )
                                    yield f"[Result: {str(output)[:100]}...]\n"
                                except Exception as e:
                                    contents.append(
                                        types.Content(
                                            role="user",
                                            parts=[
                                                types.Part.from_function_response(
                                                    name=tool_name, response={"error": str(e)}
                                                )
                                            ],
                                        )
                                    )
                                    yield f"[Error: {e}]\n"
                            else:
                                yield f"[Error: Tool {tool_name} not found]\n"

                    if not has_tool_call:
                        break
                else:
                    break

            # Update history only with final result
            self.conversation_history.append(Message(role="user", content=prompt))
            self.conversation_history.append(Message(role="model", content=full_text_acc))

        except Exception as e:
            logger.error(f"Vertex AI Standard Stream Failed: {e}")
            yield f"[Vertex Error: {e}]"

    async def close(self):
        """Cleanup."""
        pass  # New SDK manages its own connections


# Quick test capability
async def quick_generate(prompt: str) -> str:
    client = GeminiClient()
    return await client.generate(prompt)
