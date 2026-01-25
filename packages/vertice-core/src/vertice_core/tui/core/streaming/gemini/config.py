"""
Gemini Streaming Configuration.

Configuration and constants for Gemini streaming.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# SHARED CONSTANTS
# =============================================================================

# Anti-repetition and table formatting suffix added to all system prompts
# Based on: https://ai.google.dev/gemini-api/docs/troubleshooting
GEMINI_OUTPUT_RULES = """

CRITICAL OUTPUT RULES:
- Be concise and direct
- Never repeat yourself
- Never duplicate content horizontally or vertically
- Provide each answer only once
- If you find yourself repeating, STOP and move on

MARKDOWN TABLES - CRITICAL:
- Use EXACTLY 3 hyphens per column: |---|---|---|
- NO extra spaces or padding for visual alignment
- NO tabs - only single spaces
- FOR TABLE HEADINGS, IMMEDIATELY ADD ' |' AFTER THE HEADING
- Keep cell content short (under 30 chars)
"""


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class GeminiStreamConfig:
    """Configuration for Gemini streaming.

    Production-grade features (2025-12-30):
    - heartbeat_interval: SSE heartbeat to prevent connection reset
    - backpressure_queue_size: Bounded queue for flow control
    - checkpoint_interval: Chunks between checkpoints for reconnect
    - max_reconnect_attempts: Maximum reconnection attempts
    - reconnect_base_delay: Base delay for exponential backoff
    """

    model_name: str = "gemini-3-pro"
    api_key: str = ""
    temperature: float = 1.0
    max_output_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40
    init_timeout: float = 10.0
    stream_timeout: float = 60.0
    chunk_timeout: float = 30.0
    # Production-grade streaming config
    heartbeat_interval: float = 30.0  # SSE heartbeat every 30s (RFC 6797)
    backpressure_queue_size: int = 100  # Max chunks in queue before backpressure
    checkpoint_interval: int = 10  # Save checkpoint every N chunks
    max_reconnect_attempts: int = 3  # Max reconnect attempts on network failure
    reconnect_base_delay: float = 1.0  # Base delay for exponential backoff

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be >= 1")
        if self.init_timeout <= 0:
            raise ValueError("init_timeout must be > 0")
        if self.heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be > 0")
        if self.backpressure_queue_size < 1:
            raise ValueError("backpressure_queue_size must be >= 1")
