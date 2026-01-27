"""
Cost Tracking for LLM Operations.

Tracks token usage and estimates costs in real-time for:
- Gemini 3 Pro/Flash models
- Other supported models

Pricing based on Google Cloud Vertex AI pricing (2026).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (USD) - Vertex AI 2026
PRICING_PER_MILLION_TOKENS = {
    # Gemini 3 models
    "gemini-3-pro-preview": {"input": 1.25, "output": 5.00},
    "gemini-3-pro": {"input": 1.25, "output": 5.00},
    "gemini-3-flash": {"input": 0.075, "output": 0.30},
    "gemini-3-flash-preview": {"input": 0.075, "output": 0.30},
    # Embedding models
    "gemini-embedding-001": {"input": 0.00, "output": 0.00},  # Free tier
    "text-embedding-005": {"input": 0.025, "output": 0.00},
}


@dataclass
class TokenUsage:
    """Token usage for a single operation."""

    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "gemini-3-pro-preview"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    operation: str = "unknown"
    run_id: Optional[str] = None
    latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost in USD based on model pricing."""
        return estimate_cost_usd(
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "run_id": self.run_id,
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


def estimate_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Estimate cost in USD for token usage.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    # Normalize model name
    model_key = model.lower()

    # Find matching pricing
    pricing = None
    for key, price in PRICING_PER_MILLION_TOKENS.items():
        if key in model_key or model_key in key:
            pricing = price
            break

    if pricing is None:
        # Default to Pro pricing for unknown models
        pricing = PRICING_PER_MILLION_TOKENS["gemini-3-pro-preview"]
        logger.warning(f"Unknown model {model}, using default pricing")

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return round(input_cost + output_cost, 6)


class CostTracker:
    """
    Tracks token usage and costs across operations.

    Provides real-time cost estimation and usage analytics.
    """

    def __init__(self, max_history: int = 10000):
        """Initialize cost tracker."""
        self.max_history = max_history
        self._usage_history: List[TokenUsage] = []
        self._totals: Dict[str, Dict[str, int]] = {}  # model -> {input, output}

    def track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-3-pro-preview",
        operation: str = "generation",
        run_id: Optional[str] = None,
        latency_ms: float = 0.0,
    ) -> TokenUsage:
        """
        Track token usage for an operation.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used
            operation: Type of operation (generation, embedding, etc.)
            run_id: Associated run ID
            latency_ms: Operation latency in milliseconds

        Returns:
            TokenUsage record
        """
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            operation=operation,
            run_id=run_id,
            latency_ms=latency_ms,
        )

        # Add to history
        self._usage_history.append(usage)
        if len(self._usage_history) > self.max_history:
            self._usage_history = self._usage_history[-self.max_history :]

        # Update totals
        if model not in self._totals:
            self._totals[model] = {"input": 0, "output": 0}
        self._totals[model]["input"] += input_tokens
        self._totals[model]["output"] += output_tokens

        logger.debug(
            f"Tracked usage: {input_tokens}+{output_tokens} tokens, "
            f"${usage.estimated_cost_usd:.6f}"
        )

        return usage

    def get_run_usage(self, run_id: str) -> List[TokenUsage]:
        """Get all usage for a specific run."""
        return [u for u in self._usage_history if u.run_id == run_id]

    def get_run_cost(self, run_id: str) -> Dict[str, Any]:
        """Get total cost for a run."""
        usage_list = self.get_run_usage(run_id)

        total_input = sum(u.input_tokens for u in usage_list)
        total_output = sum(u.output_tokens for u in usage_list)
        total_cost = sum(u.estimated_cost_usd for u in usage_list)
        total_latency = sum(u.latency_ms for u in usage_list)

        return {
            "run_id": run_id,
            "operations": len(usage_list),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "estimated_cost_usd": round(total_cost, 6),
            "total_latency_ms": round(total_latency, 2),
            "avg_latency_ms": round(total_latency / len(usage_list), 2) if usage_list else 0,
        }

    def get_total_cost(self) -> Dict[str, Any]:
        """Get total cost across all tracked operations."""
        total_cost = 0.0
        by_model: Dict[str, Dict[str, Any]] = {}

        for model, tokens in self._totals.items():
            cost = estimate_cost_usd(model, tokens["input"], tokens["output"])
            total_cost += cost
            by_model[model] = {
                "input_tokens": tokens["input"],
                "output_tokens": tokens["output"],
                "total_tokens": tokens["input"] + tokens["output"],
                "estimated_cost_usd": round(cost, 6),
            }

        return {
            "total_estimated_cost_usd": round(total_cost, 6),
            "total_operations": len(self._usage_history),
            "by_model": by_model,
        }

    def get_recent_usage(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent usage records."""
        return [u.to_dict() for u in self._usage_history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        totals = self.get_total_cost()

        return {
            "history_size": len(self._usage_history),
            "max_history": self.max_history,
            "models_tracked": list(self._totals.keys()),
            **totals,
        }


# Global instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
