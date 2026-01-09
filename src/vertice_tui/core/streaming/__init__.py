"""
Streaming Module - Unified streaming for LLM responses.
========================================================

Provides:
- GeminiStreamer: SDK/HTTPX streaming with timeout protection
- ProductionGeminiStreamer: Production-grade with heartbeat, backpressure, reconnect

Example:
    >>> from vertice_tui.core.streaming import ProductionGeminiStreamer, GeminiStreamConfig
    >>> config = GeminiStreamConfig(api_key="...", model_name="gemini-2.0-flash")
    >>> streamer = ProductionGeminiStreamer(config)
    >>> await streamer.initialize()
    >>> async for chunk in streamer.stream_with_resilience("Hello!"):
    ...     print(chunk, end="")
"""

from __future__ import annotations

from .gemini import (
    GEMINI_OUTPUT_RULES,
    GeminiStreamConfig,
    BaseStreamer,
    GeminiSDKStreamer,
    GeminiHTTPXStreamer,
    GeminiStreamer,
)

from .production_stream import (
    StreamCheckpoint,
    ProductionGeminiStreamer,
)

__all__ = [
    # Base streaming
    "GEMINI_OUTPUT_RULES",
    "GeminiStreamConfig",
    "BaseStreamer",
    "GeminiSDKStreamer",
    "GeminiHTTPXStreamer",
    "GeminiStreamer",
    # Production-grade (Phase 2)
    "StreamCheckpoint",
    "ProductionGeminiStreamer",
]
