"""
Context Module - File Context Window & Smart Summarization.

Phase 10: Sprint 1 + Sprint 4 - Context Optimization

Components:
- FileContextWindow: Manage files in context (like Claude Code /add)
- ObservationMasker: Zero-cost context compression (research-backed)
- SlidingWindowCompressor: Gemini-style progressive truncation
- ThoughtSignatures: Gemini 3 reasoning continuity

Key Insights (Dec 2025 Research):
- Observation masking performs EQUAL or BETTER than LLM summarization
- Sliding window with progressive truncation prevents abrupt cutoffs
- Thought signatures maintain reasoning context across API calls

Soli Deo Gloria
"""

from __future__ import annotations

from .file_window import (
    FileContextEntry,
    FileContextWindow,
    get_file_context_window,
)

from .masking import (
    MaskingStrategy,
    ContentType,
    MaskingRule,
    MaskedContent,
    MaskingResult,
    ToolMaskingResult,
    ObservationMasker,
    mask_observation,
    mask_tool_output,
    DEFAULT_RULES,
)

from .sliding_window import (
    WindowStrategy,
    RetentionPolicy,
    WindowConfig,
    WindowSlice,
    CompressionResult,
    Message,
    SlidingWindowCompressor,
    get_sliding_window,
)

from .thought_signatures import (
    SignatureStatus,
    ThinkingLevel,
    ThoughtSignature,
    SignatureValidation,
    ReasoningContext,
    ThoughtSignatureManager,
    get_thought_manager,
    create_thought_signature,
)

__all__ = [
    # File Window (Sprint 1)
    "FileContextEntry",
    "FileContextWindow",
    "get_file_context_window",
    # Observation Masking (Sprint 4)
    "MaskingStrategy",
    "ContentType",
    "MaskingRule",
    "MaskedContent",
    "MaskingResult",
    "ToolMaskingResult",
    "ObservationMasker",
    "mask_observation",
    "mask_tool_output",
    "DEFAULT_RULES",
    # Sliding Window (Sprint 4)
    "WindowStrategy",
    "RetentionPolicy",
    "WindowConfig",
    "WindowSlice",
    "CompressionResult",
    "Message",
    "SlidingWindowCompressor",
    "get_sliding_window",
    # Thought Signatures (Sprint 4)
    "SignatureStatus",
    "ThinkingLevel",
    "ThoughtSignature",
    "SignatureValidation",
    "ReasoningContext",
    "ThoughtSignatureManager",
    "get_thought_manager",
    "create_thought_signature",
]
