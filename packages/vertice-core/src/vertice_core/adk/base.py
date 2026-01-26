"""Vertice ADK - Base Agent Protocol (2026 Google-Native)."""

from __future__ import annotations

import abc
import inspect
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from vertice_core.providers.vertex_ai import VertexAIProvider
from vertice_core.memory.cortex.cortex import MemoryCortex
from vertice_core.messaging.events import SystemEvent, get_event_bus


class VerticeAgent(abc.ABC):
    """
    Base class for all Vertice agents.
    Ensures compatibility with Vertex AI Reasoning Engines and AG-UI protocol.
    """

    def __init__(
        self,
        *,
        model: str = "pro",
        project: Optional[str] = None,
        location: str = "global",
    ) -> None:
        self.project = project
        self.location = location
        self.model_alias = model

        # Injected providers
        self._provider = VertexAIProvider(project=project, location=location, model_name=model)
        self._cortex = MemoryCortex()

    def emit_event(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """
        Emit an internal telemetry event (fire-and-forget).

        This is intentionally decoupled from AG-UI: the gateway is responsible for stream framing.
        """

        base: dict[str, Any] = {
            "event_type": str(event_type),
            "agent": self.__class__.__name__,
            "model": self._provider.get_model_info().get("model"),
        }
        base.update(dict(payload))
        get_event_bus().emit_sync(SystemEvent(source=self.__class__.__name__, data=base))

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        query = getattr(cls, "query", None)
        if query is None or getattr(query, "__isabstractmethod__", False):
            return
        if getattr(query, "_vertice_telemetry_wrapped", False):
            return

        if not inspect.iscoroutinefunction(query):
            return

        async def _wrapped_query(self: "VerticeAgent", *args: Any, **kw: Any) -> Dict[str, Any]:
            input_val = kw.get("input")
            if input_val is None and args:
                input_val = args[0]

            prompt = ""
            if isinstance(input_val, str):
                prompt = input_val
            elif isinstance(input_val, Mapping):
                for k in ("description", "prompt", "message"):
                    v = input_val.get(k)
                    if isinstance(v, str) and v.strip():
                        prompt = v
                        break

            self.emit_event(
                "intent",
                {
                    "prompt": prompt,
                    "input_type": type(input_val).__name__ if input_val is not None else "none",
                },
            )
            return await query(self, *args, **kw)

        _wrapped_query._vertice_telemetry_wrapped = True  # type: ignore[attr-defined]
        cls.query = _wrapped_query  # type: ignore[assignment]

    @property
    @abc.abstractmethod
    def system_prompt(self) -> str:
        """The core identity and instructions of the agent."""

    @abc.abstractmethod
    async def query(self, *, input: str | Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        The main entrypoint for the agent.
        Must be compatible with Vertex AI Reasoning Engine query protocol.
        """

    def get_requirements(self) -> List[str]:
        """
        Return the list of pip requirements needed for this agent's runtime.
        Override this in subclasses to add specialized dependencies.
        """
        return [
            "vertice-core",
            "google-cloud-aiplatform==1.115.0",
            "google-genai==1.2.0",
            "pydantic>=2.5.0",
        ]

    async def _generate_response(self, prompt: str, **kwargs) -> str:
        """Helper to generate text via the configured provider."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return await self._provider.generate(messages, **kwargs)
