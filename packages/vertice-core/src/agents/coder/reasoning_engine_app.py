"""Vertex AI Reasoning Engines adapter for the Coder agent (2026 Google-native).

Implements the minimal `Queryable` protocol expected by:
`vertexai.preview.reasoning_engines.ReasoningEngine.create(...)`.

No local code execution is performed. Inference is delegated to Vertex AI
via the Google Gen AI SDK (Gemini 3 only).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from vertice_core.providers.vertex_ai import VertexAIProvider


class CoderReasoningEngineApp:
    """Minimal Reasoning Engines Queryable app for code generation."""

    SYSTEM_PROMPT = (
        "You are an expert code generation agent. "
        "Your code MUST be production-ready, well-documented, and follow best practices. "
        "Include type hints. Handle edge cases. Return clean, runnable code."
    )

    def __init__(
        self,
        *,
        project: Optional[str] = None,
        location: str = "global",
        model: str = "pro",
    ) -> None:
        self._provider = VertexAIProvider(project=project, location=location, model_name=model)

    def query(self, **kwargs) -> Dict[str, Any]:
        """Reasoning Engines entrypoint (sync)."""
        description = kwargs.get("description") or kwargs.get("prompt") or ""
        language = kwargs.get("language") or "python"
        style = kwargs.get("style") or ""

        if not isinstance(description, str) or not description.strip():
            raise ValueError("query requires non-empty 'description' (or 'prompt').")

        async def _run() -> Dict[str, Any]:
            prompt = (
                f"TASK: {description}\n"
                f"LANGUAGE: {language}\n"
                f"STYLE: {style}\n\n"
                "MISSION:\n"
                "Provide the corrected, production-ready code.\n"
                "Use a clean code block for the chosen language.\n"
                "Include all necessary imports and type hints.\n"
            )
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            text = await self._provider.generate(messages, max_tokens=8192, temperature=0.7)
            return {"output": text}

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        raise RuntimeError("CoderReasoningEngineApp.query must be called from a non-async context.")
