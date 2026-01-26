"""Vertice ADK - Tool Decorators and Schema Generation."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar("T", bound=Callable[..., Any])


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, func: T) -> T:
        """Register a function as a tool."""
        self.tools[func.__name__] = func
        return func

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Generate Vertex AI / OpenAI compatible schemas for all registered tools."""
        schemas = []
        for name, func in self.tools.items():
            doc = inspect.getdoc(func) or ""
            sig = inspect.signature(func)

            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Basic type mapping
                ptype = "string"
                if param.annotation == int:
                    ptype = "integer"
                elif param.annotation == bool:
                    ptype = "boolean"
                elif param.annotation == float:
                    ptype = "number"

                properties[param_name] = {
                    "type": ptype,
                    "description": f"Parameter {param_name}",  # In 2026, we could parse docstrings more deeply
                }

                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            schemas.append(
                {
                    "name": name,
                    "description": doc.split("\n")[0],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            )
        return schemas


def vertice_tool(func: T) -> T:
    """
    Decorator to mark a method as a tool.
    In 2026, this enables automated function calling schema generation.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Mark for schema extraction
    wrapper._is_vertice_tool = True
    return wrapper  # type: ignore
