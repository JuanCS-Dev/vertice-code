"""
Vertice Base Agent

Base class providing common functionality for all agents.

Features:
- ObservabilityMixin: OpenTelemetry-compatible tracing and metrics

References:
- OpenTelemetry GenAI Semantic Conventions 2025
- https://opentelemetry.io/blog/2025/ai-agent-observability/
"""

from __future__ import annotations

import logging
from typing import Optional

from core.observability import ObservabilityMixin

logger = logging.getLogger(__name__)


class BaseAgent(ObservabilityMixin):
    """
    Base class for all Vertice agents.

    Provides:
    - Distributed tracing (trace_operation, trace_llm_call, trace_tool)
    - Metrics collection (record_tokens, record_latency, record_error)
    - Export capabilities (export_traces, export_metrics, get_prometheus_metrics)

    Usage:
        class MyAgent(SpecializedMixin, BaseAgent):
            name = "my_agent"

            async def do_work(self):
                with self.trace_operation("do_work"):
                    # ... agent logic ...
                    with self.trace_llm_call("gpt-4", operation="chat"):
                        response = await llm.chat(...)
                        self.record_tokens("gpt-4", input_tokens, output_tokens)
    """

    # Subclasses should override
    name: str = "base"
    agent_id: Optional[str] = None

    def __init__(self) -> None:
        """Initialize base agent with observability."""
        # Set agent_id from name if not set
        if self.agent_id is None:
            self.agent_id = getattr(self, "name", "unknown")

        # Lazy init - observability initialized on first use
        # via _init_observability() in ObservabilityMixin

    def _ensure_observability(self) -> None:
        """Ensure observability is initialized (call before tracing)."""
        if not hasattr(self, "_observability_initialized"):
            self._init_observability()
