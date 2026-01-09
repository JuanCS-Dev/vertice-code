"""Prompt building utilities for VERTICE agents."""

from .types import OutputFormat, AgenticMode, Example, ToolSpec
from .builder import XMLPromptBuilder
from .templates import (
    create_reviewer_prompt,
    create_architect_prompt,
    create_coder_prompt,
    build_agent_prompt,
)

# Backwards-compatible alias
PromptBuilder = XMLPromptBuilder

# Pre-built prompts
REVIEWER_PROMPT = create_reviewer_prompt()
ARCHITECT_PROMPT = create_architect_prompt()
CODER_PROMPT = create_coder_prompt()

__all__ = [
    "OutputFormat",
    "AgenticMode",
    "Example",
    "ToolSpec",
    "XMLPromptBuilder",
    "PromptBuilder",
    "create_reviewer_prompt",
    "create_architect_prompt",
    "create_coder_prompt",
    "build_agent_prompt",
    "REVIEWER_PROMPT",
    "ARCHITECT_PROMPT",
    "CODER_PROMPT",
]
