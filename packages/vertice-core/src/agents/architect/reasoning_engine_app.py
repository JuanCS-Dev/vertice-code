"""Vertex AI Reasoning Engines adapter for the Architect agent (2026 Google-native)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional

from vertice_core.providers.vertex_ai import VertexAIProvider


class ArchitectReasoningEngineApp:
    """Reasoning Engines app for system architecture design."""

    SYSTEM_PROMPT = (
        "You are a senior system architect. Your goal is to design robust, scalable, "
        "and secure systems based on user requirements. Use Mermaid for diagrams. "
        "Provide clear trade-off analysis for your design decisions."
    )

    def __init__(
        self,
        *,
        project: Optional[str] = None,
        location: str = "global",
        model: str = "pro",
    ) -> None:
        self._provider = VertexAIProvider(project=project, location=location, model_name=model)

    async def query(self, *, input: str | Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Reasoning Engines entrypoint (async)."""
        description = ""

        if isinstance(input, str):
            description = input
        elif isinstance(input, Mapping):
            description = str(
                input.get("description")
                or input.get("prompt")
                or input.get("message")
                or input.get("user_input")
                or input.get("input")
                or ""
            )

        if not description:
            raise ValueError("query requires non-empty 'input' (string or dict).")

        async def _run() -> str:
            prompt = (
                f"DESIGN TASK: {description}\n\n"
                "MISSION:\n"
                "1. Propose a high-level architecture.\n"
                "2. Define key components and their interactions.\n"
                "3. Provide a Mermaid diagram.\n"
                "4. List trade-offs and security considerations.\n"
            )
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            return await self._provider.generate(messages, max_tokens=8192, temperature=0.7)

        output = await _run()
        return {"output": output}
