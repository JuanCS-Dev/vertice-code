"""
Think Tool - Extended Reasoning for Complex Tasks.

Implements Anthropic's 2025 "think" tool pattern for agentic workflows.
Key insight: LLMs perform 2x better on complex tasks when given space
to reason before acting.

Phase 9.3 Enhancement: Structured thinking with bilingual support.

Source: NLU_OPTIMIZATION_PLAN.md Phase 9
"""

import re
from dataclasses import dataclass
from typing import List

from .base import Tool, ToolCategory, ToolResult


@dataclass
class StructuredThought:
    """Parsed structured thought."""

    understanding: str = ""
    approaches: List[str] = None
    decision: str = ""
    risks: List[str] = None
    next_steps: List[str] = None

    def __post_init__(self):
        if self.approaches is None:
            self.approaches = []
        if self.risks is None:
            self.risks = []
        if self.next_steps is None:
            self.next_steps = []


class ThinkTool(Tool):
    """
    Extended reasoning tool for complex tasks.

    Usage by LLM:
    - Call BEFORE executing complex tool sequences
    - Analyze the problem step-by-step
    - Consider alternatives and risks
    - Plan execution order

    Benefits:
    - 2x improvement in tool call accuracy (Anthropic research)
    - Better error recovery
    - More coherent multi-step workflows
    """

    # Structured thought markers (bilingual)
    THOUGHT_MARKERS = {
        "understanding": [
            r"(?:1\)|entendimento|understanding|objetivo|goal|problema|problem)[:\s]*(.+?)(?=\n\n|\n\d|\Z)",
        ],
        "approaches": [
            r"(?:2\)|abordagens?|approaches?|opcoes|options)[:\s]*(.+?)(?=\n\n|\n\d|\Z)",
        ],
        "decision": [
            r"(?:3\)|decisao|decision|escolha|choice)[:\s]*(.+?)(?=\n\n|\n\d|\Z)",
        ],
        "risks": [
            r"(?:4\)|riscos?|risks?|perigos?|dangers?)[:\s]*(.+?)(?=\n\n|\n\d|\Z)",
        ],
        "next_steps": [
            r"(?:5\)|proximos?\s*passos?|next\s*steps?|acoes?|actions?)[:\s]*(.+?)(?=\n\n|\Z)",
        ],
    }

    def __init__(self):
        super().__init__()
        self.name = "think"
        self.category = ToolCategory.SYSTEM
        self.description = (
            "Pense antes de agir em tarefas complexas. "
            "Think before acting on complex tasks. "
            "Estruture: 1) Entendimento/Understanding, 2) Abordagens/Approaches, "
            "3) Decisao/Decision, 4) Riscos/Risks, 5) Proximos passos/Next steps."
        )
        self.parameters = {
            "thought": {
                "type": "string",
                "description": (
                    "Raciocinio estruturado / Structured reasoning: "
                    "1) Entendimento/Understanding, "
                    "2) Abordagens/Approaches, "
                    "3) Decisao/Decision, "
                    "4) Riscos/Risks, "
                    "5) Proximos passos/Next steps"
                ),
                "required": True,
            }
        }

    async def _execute_validated(self, thought: str) -> ToolResult:
        """
        Process and structure the thought.

        Args:
            thought: Free-form or structured thinking text

        Returns:
            ToolResult with structured analysis
        """
        # Parse structured thought
        parsed = self._parse_thought(thought)

        # Build summary
        summary_parts = []

        if parsed.understanding:
            summary_parts.append(f"Objetivo/Goal: {parsed.understanding[:100]}...")

        if parsed.approaches:
            approaches_str = ", ".join(parsed.approaches[:3])
            summary_parts.append(f"Opcoes/Options: {approaches_str}")

        if parsed.decision:
            summary_parts.append(f"Decisao/Decision: {parsed.decision[:100]}...")

        if parsed.risks:
            risks_str = ", ".join(parsed.risks[:2])
            summary_parts.append(f"Riscos/Risks: {risks_str}")

        if parsed.next_steps:
            steps_str = " -> ".join(parsed.next_steps[:3])
            summary_parts.append(f"Passos/Steps: {steps_str}")

        summary = (
            "\n".join(summary_parts)
            if summary_parts
            else "Pensamento registrado / Thought recorded."
        )

        return ToolResult(
            success=True,
            data=f"[Thinking complete]\n{summary}\n\nProssiga com a execucao / Proceed with execution.",
            metadata={
                "thought_length": len(thought),
                "has_structure": bool(summary_parts),
                "understanding": parsed.understanding[:200] if parsed.understanding else "",
                "decision": parsed.decision[:200] if parsed.decision else "",
                "num_approaches": len(parsed.approaches),
                "num_risks": len(parsed.risks),
                "num_steps": len(parsed.next_steps),
                "internal": True,
            },
        )

    def _parse_thought(self, thought: str) -> StructuredThought:
        """
        Parse thought text into structured components.

        Args:
            thought: Raw thought text (can be structured or free-form)

        Returns:
            StructuredThought with extracted components
        """
        result = StructuredThought()

        # Try to extract each component
        for field, patterns in self.THOUGHT_MARKERS.items():
            for pattern in patterns:
                match = re.search(pattern, thought, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()

                    # For list fields, split by common separators
                    if field in ["approaches", "risks", "next_steps"]:
                        items = self._split_list(content)
                        setattr(result, field, items)
                    else:
                        setattr(result, field, content)
                    break

        # If no structure found, use the whole thought as understanding
        if not result.understanding and not result.decision:
            result.understanding = thought[:500]

        return result

    def _split_list(self, text: str) -> List[str]:
        """Split text into list items."""
        # Split by common list patterns
        items = re.split(r"[;\n]|\d+\)|\-\s+|\*\s+", text)
        # Clean and filter
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 2]


# Convenience function
def create_think_tool() -> ThinkTool:
    """Create a configured ThinkTool instance."""
    return ThinkTool()
