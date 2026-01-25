"""Types and enums for prompt building."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """Standard output format types for agents."""

    JSON = "json"
    JSON_STRICT = "json_strict"
    MARKDOWN = "markdown"
    XML = "xml"
    PLAIN = "plain"


class AgenticMode(Enum):
    """Agentic behavior modes."""

    AUTONOMOUS = "autonomous"  # Keep going until resolved
    CONSERVATIVE = "conservative"  # Ask before major actions
    COLLABORATIVE = "collaborative"  # Regular check-ins


@dataclass(frozen=True)
class Example:
    """An example case for agent prompts."""

    input: str
    output: str
    reasoning: str = ""


@dataclass(frozen=True)
class ToolSpec:
    """Tool specification for agentic prompts."""

    name: str
    when_to_use: str
    when_not_to_use: str = ""
