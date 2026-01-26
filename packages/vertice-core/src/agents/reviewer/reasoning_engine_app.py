"""Vertex AI Reasoning Engines adapter for the Reviewer agent (2026 Google-native)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional

from vertice_core.providers.vertex_ai import VertexAIProvider
from vertice_core.memory.cortex.cortex import MemoryCortex


class ReviewerReasoningEngineApp:
    """Reasoning Engines app for code review and security auditing."""

    SYSTEM_PROMPT = (
        "You are an expert code reviewer and security auditor. "
        "Your mission is to find vulnerabilities, logic errors, and best practice violations. "
        "Be thorough, fair, and provide clear explanations and fixes for your findings."
    )

    def __init__(
        self,
        *,
        project: Optional[str] = None,
        location: str = "global",
        model: str = "pro",
    ) -> None:
        self._provider = VertexAIProvider(project=project, location=location, model_name=model)
        self._cortex = MemoryCortex()

    async def query(self, *, input: str | Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Reasoning Engines entrypoint (async)."""
        description = ""

        if isinstance(input, str):
            description = input
        elif isinstance(input, Mapping):
            description = str(
                input.get("code")
                or input.get("content")
                or input.get("description")
                or input.get("prompt")
                or input.get("message")
                or input.get("user_input")
                or input.get("input")
                or ""
            )

        if not description:
            raise ValueError("query requires non-empty 'input' containing code or description.")

        # 1. Retrieve relevant facts/patterns from Semantic Memory (AlloyDB)
        context = await self._cortex.to_context_prompt(description)

        async def _run() -> str:
            prompt = (
                f"CONTEXT:\n{context}\n\n"
                f"REVIEW TASK:\n{description}\n\n"
                "MISSION:\n"
                "1. Audit for security vulnerabilities (OWASP Top 10).\n"
                "2. Evaluate code quality and logic.\n"
                "3. Check for performance bottlenecks.\n"
                "4. Suggest improvements or fixes.\n"
            )
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            return await self._provider.generate(messages, max_tokens=8192, temperature=0.7)

        output = await _run()
        return {"output": output}
