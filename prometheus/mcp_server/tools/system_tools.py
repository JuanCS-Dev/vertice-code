"""
System Tools for MCP Server
System-level utilities and reasoning aids

This module provides system-level tools for enhanced agent capabilities.
"""

import re
from typing import List
from .validated import create_validated_tool


# Tool 1: Think Tool
async def think_tool(thought: str) -> dict:
    """Process structured thinking for complex tasks."""
    # Parse the thought
    parsed = _parse_thought(thought)

    # Build summary
    summary_parts = []

    if parsed.get("understanding"):
        summary_parts.append(f"Goal: {parsed['understanding'][:100]}...")

    if parsed.get("approaches"):
        approaches_str = ", ".join(parsed["approaches"][:3])
        summary_parts.append(f"Options: {approaches_str}")

    if parsed.get("decision"):
        summary_parts.append(f"Decision: {parsed['decision'][:100]}...")

    if parsed.get("risks"):
        risks_str = ", ".join(parsed["risks"][:2])
        summary_parts.append(f"Risks: {risks_str}")

    if parsed.get("next_steps"):
        steps_str = " -> ".join(parsed["next_steps"][:3])
        summary_parts.append(f"Steps: {steps_str}")

    summary = "\n".join(summary_parts) if summary_parts else "Thought recorded."

    return {
        "success": True,
        "summary": f"[Thinking complete]\n{summary}\n\nProceed with execution.",
        "parsed": parsed,
        "thought_length": len(thought),
        "has_structure": bool(summary_parts),
    }


def _parse_thought(thought: str) -> dict:
    """Parse thought text into structured components."""
    result = {"understanding": "", "approaches": [], "decision": "", "risks": [], "next_steps": []}

    # Thought markers (bilingual)
    markers = {
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

    # Extract each component
    for field, patterns in markers.items():
        for pattern in patterns:
            match = re.search(pattern, thought, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()

                if field in ["approaches", "risks", "next_steps"]:
                    items = _split_list(content)
                    result[field] = items
                else:
                    result[field] = content
                break

    # If no structure found, use whole thought as understanding
    if not result["understanding"] and not result["decision"]:
        result["understanding"] = thought[:500]

    return result


def _split_list(text: str) -> List[str]:
    """Split text into list items."""
    items = re.split(r"[;\n]|\d+\)|\-\s+|\*\s+", text)
    return [item.strip() for item in items if item.strip() and len(item.strip()) > 2]


# Create and register system tools
system_tools = [
    create_validated_tool(
        name="think",
        description="Think before acting on complex tasks. Structure: 1) Understanding, 2) Approaches, 3) Decision, 4) Risks, 5) Next steps",
        category="system",
        parameters={
            "thought": {
                "type": "string",
                "description": "Structured reasoning: 1) Understanding, 2) Approaches, 3) Decision, 4) Risks, 5) Next steps",
                "required": True,
            }
        },
        required_params=["thought"],
        execute_func=think_tool,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in system_tools:
    register_tool(tool)
