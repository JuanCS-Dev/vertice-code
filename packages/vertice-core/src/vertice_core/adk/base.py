"""Vertice ADK - Base Agent Protocol (2026 Google-Native)."""

from __future__ import annotations

import abc
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from vertice_core.providers.vertex_ai import VertexAIProvider
from vertice_core.memory.cortex.cortex import MemoryCortex


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
        location: str = "us-central1",
    ) -> None:
        self.project = project
        self.location = location
        self.model_alias = model

        # Injected providers
        self._provider = VertexAIProvider(project=project, location=location, model_name=model)
        self._cortex = MemoryCortex()

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
