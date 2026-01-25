"""
Code Generation Engine - Core logic for code generation

Extracted from CoderAgent for better modularity and maintainability.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from vertice_core.types import LLMResponse
from vertice_core.providers.vertice_router import TaskComplexity

logger = logging.getLogger(__name__)


@dataclass
class CodeGenerationContext:
    """Context for code generation operations."""

    task: str
    language: str = "python"
    complexity: TaskComplexity = TaskComplexity.MODERATE
    requirements: Optional[List[str]] = None
    constraints: Optional[Dict[str, str]] = None


class CodeGenerationEngine:
    """
    Core engine for code generation operations.

    Handles the actual LLM interactions and code generation logic,
    separated from agent orchestration for better maintainability.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def generate_code(self, context: CodeGenerationContext) -> str:
        """
        Generate code based on the given context.

        Args:
            context: Code generation parameters and constraints

        Returns:
            Generated code as string
        """
        prompt = self._build_generation_prompt(context)

        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}], max_tokens=2048, temperature=0.7
        )

        return self._extract_code_from_response(response)

    def _build_generation_prompt(self, context: CodeGenerationContext) -> str:
        """Build the LLM prompt for code generation."""
        prompt_parts = [
            f"Generate {context.language} code for the following task:",
            f"Task: {context.task}",
            f"Complexity: {context.complexity.value}",
        ]

        if context.requirements:
            prompt_parts.append(f"Requirements: {', '.join(context.requirements)}")

        if context.constraints:
            constraints_str = "\n".join(f"- {k}: {v}" for k, v in context.constraints.items())
            prompt_parts.append(f"Constraints:\n{constraints_str}")

        prompt_parts.extend(
            [
                "",
                "Provide only the code without explanation.",
                "```python" if context.language == "python" else f"```{context.language}",
            ]
        )

        return "\n".join(prompt_parts)

    def _extract_code_from_response(self, response: LLMResponse) -> str:
        """Extract code from LLM response."""
        content = response.get("content", "")

        # Remove markdown code blocks if present
        if "```" in content:
            # Extract code between first and last ```
            parts = content.split("```")
            if len(parts) >= 3:
                return parts[1].strip()

        return content.strip()
