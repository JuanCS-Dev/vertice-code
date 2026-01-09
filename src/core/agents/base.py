"""
Unified Agent Base - Simple by Design.
======================================

Follows 2025 patterns from Anthropic, Google, OpenAI:
- Simple Agent class (name, instructions, tools, handoffs)
- Strict tool schemas
- Observable by design

References:
- Anthropic: https://docs.anthropic.com/en/docs/agents-and-tools
- OpenAI SDK: https://openai.github.io/openai-agents-python/
- Google Gemini: https://ai.google.dev/gemini-api/docs/function-calling

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# =============================================================================
# HANDOFF - Agent Delegation
# =============================================================================


@dataclass
class Handoff:
    """Handoff to another agent.

    Enables agent delegation following OpenAI SDK pattern.

    Attributes:
        target: Target agent name or Agent instance
        description: When to use this handoff
        input_filter: Optional function to filter context passed to target
    """

    target: Union[str, "Agent"]
    description: str = ""
    input_filter: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None

    @property
    def target_name(self) -> str:
        """Get target agent name."""
        if isinstance(self.target, str):
            return self.target
        return self.target.name


# =============================================================================
# AGENT CONFIG
# =============================================================================


@dataclass
class AgentConfig:
    """Agent configuration.

    Attributes:
        max_turns: Maximum conversation turns (0 = unlimited)
        tool_timeout: Timeout for tool execution (seconds)
        enable_tracing: Enable observability tracing
    """

    max_turns: int = 10
    tool_timeout: float = 30.0
    enable_tracing: bool = True


# =============================================================================
# UNIFIED AGENT
# =============================================================================


@dataclass
class Agent:
    """Unified Agent - Simple, Observable, Extensible.

    Follows Anthropic-first design: simple interface with strict tools.

    Attributes:
        name: Agent identifier (e.g., "coder", "reviewer")
        instructions: System prompt / agent personality
        tools: List of Tool instances or callables
        handoffs: List of Handoff definitions for delegation
        config: Optional configuration overrides

    Example:
        >>> agent = Agent(
        ...     name="coder",
        ...     instructions="You write clean Python code.",
        ...     tools=[read_file_tool, write_file_tool],
        ...     handoffs=[Handoff(target="reviewer", description="For code review")],
        ... )
        >>> # Run with LLM client
        >>> response = await run_agent(agent, "Fix the bug", llm_client)
    """

    name: str
    instructions: str = ""
    tools: List[Any] = field(default_factory=list)
    handoffs: List[Handoff] = field(default_factory=list)
    config: AgentConfig = field(default_factory=AgentConfig)

    def __post_init__(self) -> None:
        """Validate agent configuration."""
        if not self.name:
            raise ValueError("Agent name is required")

    def get_tool_schemas(self, provider: str = "anthropic") -> List[Dict[str, Any]]:
        """Get tool schemas for LLM.

        Args:
            provider: Target provider (anthropic, openai, gemini)

        Returns:
            List of tool schemas in provider format
        """
        schemas = []
        for tool in self.tools:
            if hasattr(tool, "get_schema"):
                # Tool class with schema method - get base schema and transform
                base_schema = tool.get_schema()
                schemas.append(self._transform_schema(base_schema, provider))
            elif callable(tool):
                # Function tool - generate schema from signature
                schemas.append(self._schema_from_function(tool, provider))
        return schemas

    def _transform_schema(
        self, base_schema: Dict[str, Any], provider: str
    ) -> Dict[str, Any]:
        """Transform base schema to provider-specific format.

        Args:
            base_schema: Base schema from Tool.get_schema()
            provider: Target provider (anthropic, openai, gemini)

        Returns:
            Provider-specific schema
        """
        name = base_schema.get("name", "")
        description = base_schema.get("description", "")
        # Handle both 'parameters' and 'input_schema' keys
        params = base_schema.get("input_schema") or base_schema.get("parameters", {})

        # Ensure proper object schema format
        if not isinstance(params, dict):
            params = {"type": "object", "properties": {}, "required": []}
        elif "type" not in params:
            # Wrap properties in object schema
            params = {
                "type": "object",
                "properties": params,
                "required": [k for k, v in params.items() if v.get("required", False)],
            }

        if provider == "openai":
            return {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": params,
                },
            }
        elif provider == "gemini":
            return {
                "name": name,
                "description": description,
                "parameters": params,
            }
        else:  # anthropic (default)
            return {
                "name": name,
                "description": description,
                "input_schema": params,
                "strict": True,
            }

    def _schema_from_function(
        self, func: Callable[..., Any], provider: str
    ) -> Dict[str, Any]:
        """Generate schema from function signature.

        Args:
            func: Function to generate schema for
            provider: Target provider

        Returns:
            Tool schema dict
        """
        import inspect

        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            prop: Dict[str, Any] = {"type": "string"}  # Default type

            # Try to get type from annotation
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                prop["type"] = type_map.get(param.annotation, "string")

            properties[param_name] = prop

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

        schema = {
            "name": func.__name__,
            "description": doc.split("\n")[0] if doc else "",
            "input_schema": input_schema,
            "strict": True,
        }

        if provider == "openai":
            return {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": input_schema,
                },
            }
        elif provider == "gemini":
            return {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": input_schema,
            }

        return schema  # Anthropic format

    def get_handoff_schemas(self) -> List[Dict[str, Any]]:
        """Get handoff definitions as tool schemas.

        Handoffs appear as special tools that transfer to other agents.

        Returns:
            List of handoff tool schemas
        """
        schemas = []
        for handoff in self.handoffs:
            schemas.append({
                "name": f"transfer_to_{handoff.target_name}",
                "description": handoff.description or f"Transfer to {handoff.target_name}",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "string",
                            "description": "Context to pass to target agent",
                        }
                    },
                    "required": [],
                    "additionalProperties": False,
                },
                "strict": True,
            })
        return schemas

    def get_all_schemas(self, provider: str = "anthropic") -> List[Dict[str, Any]]:
        """Get all tool and handoff schemas.

        Args:
            provider: Target provider

        Returns:
            Combined list of tool and handoff schemas
        """
        return self.get_tool_schemas(provider) + self.get_handoff_schemas()

    def find_tool(self, name: str) -> Optional[Any]:
        """Find tool by name.

        Args:
            name: Tool name to find

        Returns:
            Tool instance or None
        """
        for tool in self.tools:
            if hasattr(tool, "name") and tool.name == name:
                return tool
            elif callable(tool) and tool.__name__ == name:
                return tool
        return None

    def find_handoff(self, name: str) -> Optional[Handoff]:
        """Find handoff by target name.

        Args:
            name: Target agent name (or transfer_to_name)

        Returns:
            Handoff instance or None
        """
        # Support both "target" and "transfer_to_target" formats
        clean_name = name.replace("transfer_to_", "")
        for handoff in self.handoffs:
            if handoff.target_name == clean_name:
                return handoff
        return None

    def clone(self, **overrides: Any) -> "Agent":
        """Create a copy of this agent with overrides.

        Args:
            **overrides: Fields to override

        Returns:
            New Agent instance
        """
        return Agent(
            name=overrides.get("name", self.name),
            instructions=overrides.get("instructions", self.instructions),
            tools=overrides.get("tools", self.tools.copy()),
            handoffs=overrides.get("handoffs", self.handoffs.copy()),
            config=overrides.get("config", self.config),
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Agent",
    "AgentConfig",
    "Handoff",
]
