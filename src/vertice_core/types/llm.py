# LLM and generation types - Domain level

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .tools import ToolCall  # type: ignore


class ModelInfo(TypedDict):
    """Information about an LLM model."""

    model: str
    provider: str
    cost_tier: NotRequired[str]
    speed_tier: NotRequired[str]
    supports_streaming: NotRequired[bool]
    requests_per_day: NotRequired[int]


class GenerationConfig(TypedDict, total=False):
    """Configuration for LLM generation."""

    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    stop_sequences: List[str]
    presence_penalty: float
    frequency_penalty: float


class TokenUsage(TypedDict):
    """Token usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: Optional[float]


class LLMResponse(TypedDict):
    """Complete LLM response with metadata."""

    content: str
    usage: TokenUsage
    model: str
    finish_reason: Literal["stop", "length", "tool_calls", "error"]
    tool_calls: Optional[List[ToolCall]]
