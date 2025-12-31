"""
Gemini Streaming - Backward Compatibility Shim.

DEPRECATED: Use tui.core.streaming.gemini module directly.

This module re-exports from the new gemini/ package for
backward compatibility. All functionality has been moved to:

- tui.core.streaming.gemini.config  → GeminiStreamConfig, GEMINI_OUTPUT_RULES
- tui.core.streaming.gemini.base    → BaseStreamer
- tui.core.streaming.gemini.sdk     → GeminiSDKStreamer
- tui.core.streaming.gemini.httpx_streamer → GeminiHTTPXStreamer
- tui.core.streaming.gemini.unified → GeminiStreamer

Migration:
    # Old:
    from tui.core.streaming.gemini_stream import GeminiStreamer

    # New:
    from tui.core.streaming.gemini import GeminiStreamer
"""

from __future__ import annotations

import warnings

# Re-export everything from the new module
from .gemini import (
    GEMINI_OUTPUT_RULES,
    GeminiStreamConfig,
    BaseStreamer,
    GeminiSDKStreamer,
    GeminiHTTPXStreamer,
    GeminiStreamer,
)

# Emit deprecation warning on import
warnings.warn(
    "tui.core.streaming.gemini_stream is deprecated. Use tui.core.streaming.gemini instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "GEMINI_OUTPUT_RULES",
    "GeminiStreamConfig",
    "BaseStreamer",
    "GeminiSDKStreamer",
    "GeminiHTTPXStreamer",
    "GeminiStreamer",
]
