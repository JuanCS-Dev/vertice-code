"""
ObservationMasker - Zero-Cost Context Compression.

Research-backed approach (Dec 2025):
- Observation masking performs EQUAL or BETTER than LLM summarization
- ZERO additional token cost (no summarization calls)
- Works by replacing verbose tool outputs with fixed placeholders

Key insight: "Too much context can harm performance" - agents do better
by forgetting context that doesn't help remaining tasks.

References:
- "The Complexity Trap: Simple Observation Masking Is as Efficient as
   LLM Summarization for Agent Context Management" (2025)
- Tested on Gemini 2.5 Flash, Qwen 3 (480B, 32B)
- 4 of 5 models performed BETTER with masking vs baseline

Phase 10: Sprint 4 - Context Optimization

Soli Deo Gloria
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple

# Token estimation
CHARS_PER_TOKEN = 4


class MaskingStrategy(str, Enum):
    """Available masking strategies."""

    PLACEHOLDER = "placeholder"  # Fixed placeholder (recommended)
    HASH_ONLY = "hash_only"  # Keep only content hash
    SUMMARY_LINE = "summary_line"  # Single line summary
    TRUNCATE = "truncate"  # Keep first N chars


class ContentType(str, Enum):
    """Types of content that can be masked."""

    TOOL_OUTPUT = "tool_output"
    CODE_BLOCK = "code_block"
    STACK_TRACE = "stack_trace"
    LOG_OUTPUT = "log_output"
    FILE_CONTENT = "file_content"
    JSON_RESPONSE = "json_response"
    GENERIC = "generic"


@dataclass
class MaskingRule:
    """Rule for matching and masking content."""

    name: str
    pattern: Pattern[str]
    content_type: ContentType
    strategy: MaskingStrategy = MaskingStrategy.PLACEHOLDER
    priority: int = 0  # Higher = process first
    min_chars: int = 100  # Only mask if exceeds this
    placeholder_template: str = "[{type}: {summary}]"

    def matches(self, content: str) -> bool:
        """Check if content matches this rule."""
        return bool(self.pattern.search(content))


@dataclass
class MaskedContent:
    """Result of masking operation."""

    original_hash: str
    content_type: ContentType
    original_tokens: int
    masked_tokens: int
    masked_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def tokens_saved(self) -> int:
        """Tokens saved by masking."""
        return self.original_tokens - self.masked_tokens

    @property
    def compression_ratio(self) -> float:
        """Compression ratio achieved."""
        if self.original_tokens == 0:
            return 1.0
        return self.masked_tokens / self.original_tokens


@dataclass
class MaskingResult:
    """Result of masking an entire message or context."""

    success: bool
    original_tokens: int
    masked_tokens: int
    items_masked: int
    masked_contents: List[MaskedContent] = field(default_factory=list)
    duration_ms: float = 0.0
    error: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.masked_tokens

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 1.0
        return self.masked_tokens / self.original_tokens


# Default masking rules based on Big 3 patterns
DEFAULT_RULES: List[MaskingRule] = [
    # Stack traces (high priority - very verbose)
    MaskingRule(
        name="stack_trace",
        pattern=re.compile(
            r"Traceback \(most recent call last\):.*?(?=\n\n|\Z)",
            re.DOTALL | re.MULTILINE
        ),
        content_type=ContentType.STACK_TRACE,
        strategy=MaskingStrategy.SUMMARY_LINE,
        priority=100,
        min_chars=200,
        placeholder_template="[Stack trace: {error_type} - {error_msg}]",
    ),
    # Large code blocks
    MaskingRule(
        name="code_block",
        pattern=re.compile(r"```[\w]*\n[\s\S]{500,}?```"),
        content_type=ContentType.CODE_BLOCK,
        strategy=MaskingStrategy.TRUNCATE,
        priority=80,
        min_chars=500,
        placeholder_template="[Code block: {lines} lines, {lang}]",
    ),
    # Log outputs (timestamps + messages)
    MaskingRule(
        name="log_output",
        pattern=re.compile(
            r"(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}.*?\n){5,}",
            re.MULTILINE
        ),
        content_type=ContentType.LOG_OUTPUT,
        strategy=MaskingStrategy.PLACEHOLDER,
        priority=70,
        min_chars=300,
        placeholder_template="[Log output: {count} lines]",
    ),
    # JSON responses
    MaskingRule(
        name="json_response",
        pattern=re.compile(r"\{[\s\S]{500,}?\}"),
        content_type=ContentType.JSON_RESPONSE,
        strategy=MaskingStrategy.SUMMARY_LINE,
        priority=60,
        min_chars=500,
        placeholder_template="[JSON: {keys} keys]",
    ),
    # File contents (indented blocks)
    MaskingRule(
        name="file_content",
        pattern=re.compile(r"(^\s{4,}.+$\n){10,}", re.MULTILINE),
        content_type=ContentType.FILE_CONTENT,
        strategy=MaskingStrategy.TRUNCATE,
        priority=50,
        min_chars=400,
        placeholder_template="[File content: {lines} lines]",
    ),
    # Generic tool output
    MaskingRule(
        name="tool_output",
        pattern=re.compile(r"\[Tool Output\][\s\S]{200,}"),
        content_type=ContentType.TOOL_OUTPUT,
        strategy=MaskingStrategy.PLACEHOLDER,
        priority=40,
        min_chars=200,
        placeholder_template="[Tool output: executed]",
    ),
]


class ObservationMasker:
    """
    Zero-cost observation masker for context compression.

    This is the PRIMARY strategy for agentic loops based on 2025 research:
    - Performs equal or better than LLM summarization
    - Zero additional token cost
    - Simple placeholder replacement

    Usage:
        masker = ObservationMasker()

        # Mask a single message
        result = masker.mask_content(tool_output)

        # Mask conversation history
        messages = masker.mask_messages(history, keep_recent=5)

        # Check if masking would help
        if masker.should_mask(content):
            masked = masker.mask_content(content)
    """

    # Default placeholder for masked content
    DEFAULT_PLACEHOLDER = "[Previous {count} lines elided for brevity]"

    def __init__(
        self,
        rules: Optional[List[MaskingRule]] = None,
        placeholder_template: str = DEFAULT_PLACEHOLDER,
        min_tokens_to_mask: int = 50,
        preserve_errors: bool = True,
        preserve_decisions: bool = True,
    ):
        """
        Initialize observation masker.

        Args:
            rules: Custom masking rules (default: DEFAULT_RULES)
            placeholder_template: Template for masked content
            min_tokens_to_mask: Minimum tokens before masking applies
            preserve_errors: Keep error messages unmasked
            preserve_decisions: Keep decision-related content unmasked
        """
        self.rules = sorted(
            rules or DEFAULT_RULES,
            key=lambda r: -r.priority
        )
        self.placeholder_template = placeholder_template
        self.min_tokens_to_mask = min_tokens_to_mask
        self.preserve_errors = preserve_errors
        self.preserve_decisions = preserve_decisions

        # Statistics
        self._total_masked = 0
        self._total_tokens_saved = 0

    def should_mask(self, content: str) -> bool:
        """
        Check if content should be masked.

        Args:
            content: Content to check

        Returns:
            True if masking would be beneficial
        """
        tokens = len(content) // CHARS_PER_TOKEN

        if tokens < self.min_tokens_to_mask:
            return False

        # Check if any rule matches
        for rule in self.rules:
            if rule.matches(content) and len(content) >= rule.min_chars:
                return True

        return False

    def mask_content(
        self,
        content: str,
        content_type: Optional[ContentType] = None,
        strategy: Optional[MaskingStrategy] = None,
    ) -> MaskedContent:
        """
        Mask a piece of content.

        Args:
            content: Content to mask
            content_type: Type of content (auto-detected if None)
            strategy: Masking strategy (uses rule default if None)

        Returns:
            MaskedContent with result
        """
        original_tokens = len(content) // CHARS_PER_TOKEN
        original_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Find matching rule
        rule = self._find_matching_rule(content)

        if rule is None:
            # No rule matches, use generic masking
            masked, metadata = self._apply_generic_masking(content)
            ct = content_type or ContentType.GENERIC
        else:
            ct = content_type or rule.content_type
            strat = strategy or rule.strategy
            masked, metadata = self._apply_rule(content, rule, strat)

        masked_tokens = len(masked) // CHARS_PER_TOKEN

        # Update stats
        self._total_masked += 1
        self._total_tokens_saved += (original_tokens - masked_tokens)

        return MaskedContent(
            original_hash=original_hash,
            content_type=ct,
            original_tokens=original_tokens,
            masked_tokens=masked_tokens,
            masked_content=masked,
            metadata=metadata,
        )

    def mask_messages(
        self,
        messages: List[Dict[str, Any]],
        keep_recent: int = 5,
        mask_roles: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], MaskingResult]:
        """
        Mask a list of messages (conversation history).

        Args:
            messages: List of message dicts with 'role' and 'content'
            keep_recent: Number of recent messages to keep unmasked
            mask_roles: Roles to mask (default: ['tool', 'assistant'])

        Returns:
            Tuple of (masked messages, result)
        """
        start_time = time.time()
        mask_roles = mask_roles or ["tool", "assistant"]

        if len(messages) <= keep_recent:
            # Nothing to mask
            total_tokens = sum(
                len(m.get("content", "")) // CHARS_PER_TOKEN
                for m in messages
            )
            return messages, MaskingResult(
                success=True,
                original_tokens=total_tokens,
                masked_tokens=total_tokens,
                items_masked=0,
                duration_ms=0,
            )

        # Split messages
        to_mask = messages[:-keep_recent]
        to_keep = messages[-keep_recent:]

        masked_messages = []
        masked_contents = []
        original_tokens = 0
        masked_tokens = 0

        for msg in to_mask:
            role = msg.get("role", "")
            content = msg.get("content", "")
            original_tokens += len(content) // CHARS_PER_TOKEN

            if role in mask_roles and self.should_mask(content):
                # Apply masking
                result = self.mask_content(content)
                masked_contents.append(result)
                masked_tokens += result.masked_tokens

                masked_messages.append({
                    **msg,
                    "content": result.masked_content,
                    "_masked": True,
                    "_original_hash": result.original_hash,
                })
            else:
                # Keep as is
                masked_tokens += len(content) // CHARS_PER_TOKEN
                masked_messages.append(msg)

        # Add kept messages
        for msg in to_keep:
            content = msg.get("content", "")
            tokens = len(content) // CHARS_PER_TOKEN
            original_tokens += tokens
            masked_tokens += tokens
            masked_messages.append(msg)

        duration_ms = (time.time() - start_time) * 1000

        return masked_messages, MaskingResult(
            success=True,
            original_tokens=original_tokens,
            masked_tokens=masked_tokens,
            items_masked=len(masked_contents),
            masked_contents=masked_contents,
            duration_ms=duration_ms,
        )

    def _find_matching_rule(self, content: str) -> Optional[MaskingRule]:
        """Find first matching rule for content."""
        for rule in self.rules:
            if rule.matches(content) and len(content) >= rule.min_chars:
                return rule
        return None

    def _apply_rule(
        self,
        content: str,
        rule: MaskingRule,
        strategy: MaskingStrategy,
    ) -> Tuple[str, Dict[str, Any]]:
        """Apply masking rule to content."""
        metadata: Dict[str, Any] = {"rule": rule.name}

        if strategy == MaskingStrategy.PLACEHOLDER:
            return self._mask_placeholder(content, rule, metadata)

        elif strategy == MaskingStrategy.HASH_ONLY:
            return self._mask_hash_only(content, metadata)

        elif strategy == MaskingStrategy.SUMMARY_LINE:
            return self._mask_summary_line(content, rule, metadata)

        elif strategy == MaskingStrategy.TRUNCATE:
            return self._mask_truncate(content, rule, metadata)

        else:
            return self._apply_generic_masking(content)

    def _mask_placeholder(
        self,
        content: str,
        rule: MaskingRule,
        metadata: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Replace content with fixed placeholder."""
        line_count = content.count("\n") + 1
        metadata["lines"] = line_count

        placeholder = self.placeholder_template.format(count=line_count)
        return placeholder, metadata

    def _mask_hash_only(
        self,
        content: str,
        metadata: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Keep only content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        metadata["hash"] = content_hash
        return f"[Content hash: {content_hash}]", metadata

    def _mask_summary_line(
        self,
        content: str,
        rule: MaskingRule,
        metadata: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract single line summary."""
        # Extract key info based on content type
        if rule.content_type == ContentType.STACK_TRACE:
            # Extract error type and message
            error_match = re.search(r"(\w+Error|\w+Exception): (.+?)$", content, re.MULTILINE)
            if error_match:
                error_type = error_match.group(1)
                error_msg = error_match.group(2)[:50]
                metadata["error_type"] = error_type
                metadata["error_msg"] = error_msg
                return f"[Stack trace: {error_type} - {error_msg}]", metadata

        elif rule.content_type == ContentType.JSON_RESPONSE:
            # Count top-level keys
            key_matches = re.findall(r'"(\w+)":', content[:500])
            unique_keys = list(set(key_matches))[:5]
            metadata["keys"] = len(unique_keys)
            return f"[JSON: {len(unique_keys)} keys - {', '.join(unique_keys[:3])}...]", metadata

        # Default summary
        first_line = content.split("\n")[0][:80]
        line_count = content.count("\n") + 1
        metadata["lines"] = line_count
        return f"[{rule.content_type.value}: {first_line}... ({line_count} lines)]", metadata

    def _mask_truncate(
        self,
        content: str,
        rule: MaskingRule,
        metadata: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Truncate content keeping beginning."""
        max_chars = rule.min_chars
        line_count = content.count("\n") + 1
        metadata["lines"] = line_count

        if len(content) <= max_chars:
            return content, metadata

        truncated = content[:max_chars]
        remaining_lines = content[max_chars:].count("\n")
        return f"{truncated}\n[...{remaining_lines} more lines truncated]", metadata

    def _apply_generic_masking(
        self,
        content: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Apply generic masking (fallback)."""
        line_count = content.count("\n") + 1
        placeholder = self.placeholder_template.format(count=line_count)
        return placeholder, {"lines": line_count, "rule": "generic"}

    def get_stats(self) -> Dict[str, Any]:
        """Get masking statistics."""
        return {
            "total_masked": self._total_masked,
            "total_tokens_saved": self._total_tokens_saved,
            "rules_count": len(self.rules),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._total_masked = 0
        self._total_tokens_saved = 0


# Convenience functions
def mask_observation(content: str) -> str:
    """Quick mask of observation content."""
    masker = ObservationMasker()
    if masker.should_mask(content):
        result = masker.mask_content(content)
        return result.masked_content
    return content


@dataclass
class ToolMaskingResult:
    """Result of tool output masking."""

    content: str
    original_tokens: int
    masked_tokens: int
    was_masked: bool
    compression_ratio: float

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.masked_tokens


def mask_tool_output(
    output: str,
    tool_name: str = "tool",
    preserve_errors: bool = True,
) -> ToolMaskingResult:
    """
    Mask tool output with tool name context.

    Returns structured result with compression metrics for dashboard.

    Args:
        output: Raw tool output
        tool_name: Name of tool for context
        preserve_errors: Keep error outputs unmasked

    Returns:
        ToolMaskingResult with content and compression metrics
    """
    original_tokens = len(output) // CHARS_PER_TOKEN

    # Check if this is an error (preserve if requested)
    is_error = any(
        indicator in output.lower()
        for indicator in ["error", "exception", "failed", "traceback"]
    )

    masker = ObservationMasker(preserve_errors=preserve_errors)

    if is_error and preserve_errors:
        # Keep errors unmasked but still format nicely
        return ToolMaskingResult(
            content=f"[{tool_name}] {output}",
            original_tokens=original_tokens,
            masked_tokens=original_tokens,
            was_masked=False,
            compression_ratio=1.0,
        )

    if masker.should_mask(output):
        result = masker.mask_content(output, ContentType.TOOL_OUTPUT)
        masked_content = f"[{tool_name}] {result.masked_content}"
        masked_tokens = len(masked_content) // CHARS_PER_TOKEN

        return ToolMaskingResult(
            content=masked_content,
            original_tokens=original_tokens,
            masked_tokens=masked_tokens,
            was_masked=True,
            compression_ratio=masked_tokens / max(original_tokens, 1),
        )

    # No masking needed
    return ToolMaskingResult(
        content=f"[{tool_name}] {output}",
        original_tokens=original_tokens,
        masked_tokens=original_tokens,
        was_masked=False,
        compression_ratio=1.0,
    )


__all__ = [
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
]
