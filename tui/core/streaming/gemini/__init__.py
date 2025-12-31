"""
Gemini Streaming Module - Unified Streaming Strategies.

Semantic extraction from gemini_stream.py for CODE_CONSTITUTION compliance.

Components:
- config.py: GeminiStreamConfig, GEMINI_OUTPUT_RULES
- base.py: BaseStreamer protocol
- sdk.py: GeminiSDKStreamer (google-generativeai)
- httpx_streamer.py: GeminiHTTPXStreamer (httpx SSE)
- unified.py: GeminiStreamer (automatic fallback)

Following CODE_CONSTITUTION: <500 lines per file, 100% type hints
"""

from __future__ import annotations

from .config import GEMINI_OUTPUT_RULES, GeminiStreamConfig
from .base import BaseStreamer
from .sdk import GeminiSDKStreamer
from .httpx_streamer import GeminiHTTPXStreamer
from .unified import GeminiStreamer

__all__ = [
    "GEMINI_OUTPUT_RULES",
    "GeminiStreamConfig",
    "BaseStreamer",
    "GeminiSDKStreamer",
    "GeminiHTTPXStreamer",
    "GeminiStreamer",
]
