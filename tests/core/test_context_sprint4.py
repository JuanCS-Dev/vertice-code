"""
Tests for Sprint 4: Context Optimization.

Tests cover:
- ObservationMasker: Zero-cost context compression
- SlidingWindowCompressor: Gemini-style progressive truncation
- ThoughtSignatures: Gemini 3 reasoning continuity
- TokenDashboard: Widget testing (without Textual app)

Phase 10: Sprint 4 - Context Optimization

Soli Deo Gloria
"""

import time
import pytest
from unittest.mock import Mock, patch

# =============================================================================
# OBSERVATION MASKER TESTS
# =============================================================================


class TestMaskingStrategy:
    """Test MaskingStrategy enum."""

    def test_strategies_exist(self):
        from vertice_tui.core.context.masking import MaskingStrategy

        assert MaskingStrategy.PLACEHOLDER == "placeholder"
        assert MaskingStrategy.HASH_ONLY == "hash_only"
        assert MaskingStrategy.SUMMARY_LINE == "summary_line"
        assert MaskingStrategy.TRUNCATE == "truncate"


class TestContentType:
    """Test ContentType enum."""

    def test_content_types_exist(self):
        from vertice_tui.core.context.masking import ContentType

        assert ContentType.TOOL_OUTPUT == "tool_output"
        assert ContentType.CODE_BLOCK == "code_block"
        assert ContentType.STACK_TRACE == "stack_trace"
        assert ContentType.LOG_OUTPUT == "log_output"
        assert ContentType.FILE_CONTENT == "file_content"
        assert ContentType.JSON_RESPONSE == "json_response"
        assert ContentType.GENERIC == "generic"


class TestMaskedContent:
    """Test MaskedContent dataclass."""

    def test_tokens_saved(self):
        from vertice_tui.core.context.masking import MaskedContent, ContentType

        result = MaskedContent(
            original_hash="abc123",
            content_type=ContentType.TOOL_OUTPUT,
            original_tokens=1000,
            masked_tokens=50,
            masked_content="[masked]",
        )

        assert result.tokens_saved == 950
        assert result.compression_ratio == 0.05

    def test_compression_ratio_zero_division(self):
        from vertice_tui.core.context.masking import MaskedContent, ContentType

        result = MaskedContent(
            original_hash="abc123",
            content_type=ContentType.GENERIC,
            original_tokens=0,
            masked_tokens=0,
            masked_content="",
        )

        assert result.compression_ratio == 1.0


class TestObservationMasker:
    """Test ObservationMasker class."""

    def test_initialization(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        assert masker.min_tokens_to_mask == 50
        assert masker.preserve_errors is True
        assert len(masker.rules) > 0

    def test_should_mask_small_content(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        # Small content should not be masked
        assert masker.should_mask("hello") is False

    def test_should_mask_large_content(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        # Large log-like content should be masked
        large_content = "\n".join(
            f"2024-01-01 12:00:00 INFO: Log line {i}"
            for i in range(50)
        )
        assert masker.should_mask(large_content) is True

    def test_mask_content_basic(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        large_content = "x" * 1000  # Large generic content

        result = masker.mask_content(large_content)

        assert result.original_tokens > result.masked_tokens
        assert result.original_hash is not None
        assert len(result.masked_content) < len(large_content)

    def test_mask_stack_trace(self):
        from vertice_tui.core.context.masking import ObservationMasker, ContentType

        masker = ObservationMasker()
        # Large stack trace that exceeds min_chars (200)
        stack_trace = """Traceback (most recent call last):
  File "/home/user/project/main.py", line 150, in main
    result = process_data(input_data)
  File "/home/user/project/processor.py", line 75, in process_data
    validated = validate(data)
  File "/home/user/project/validator.py", line 42, in validate
    check_format(data)
  File "/home/user/project/validator.py", line 28, in check_format
    raise ValueError("Invalid format: expected JSON")
  File "/home/user/project/utils.py", line 15, in helper
    do_something()
ValueError: Invalid format: expected JSON"""

        result = masker.mask_content(stack_trace, ContentType.STACK_TRACE)

        # Should be masked (content is large enough)
        assert result.masked_tokens < result.original_tokens

    def test_mask_messages_keep_recent(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        messages = [
            {"role": "user", "content": f"message {i}" * 100}
            for i in range(10)
        ]

        masked_msgs, result = masker.mask_messages(messages, keep_recent=3)

        assert len(masked_msgs) == 10
        assert result.success is True
        # Last 3 should be unchanged
        for i, msg in enumerate(masked_msgs[-3:]):
            assert msg.get("_masked") is not True

    def test_mask_messages_empty(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        masked_msgs, result = masker.mask_messages([], keep_recent=5)

        assert masked_msgs == []
        assert result.success is True
        assert result.items_masked == 0

    def test_get_stats(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        masker.mask_content("x" * 1000)
        stats = masker.get_stats()

        assert "total_masked" in stats
        assert stats["total_masked"] >= 1

    def test_reset_stats(self):
        from vertice_tui.core.context.masking import ObservationMasker

        masker = ObservationMasker()
        masker.mask_content("x" * 1000)
        masker.reset_stats()
        stats = masker.get_stats()

        assert stats["total_masked"] == 0


class TestMaskingConvenienceFunctions:
    """Test convenience functions."""

    def test_mask_observation(self):
        from vertice_tui.core.context.masking import mask_observation

        result = mask_observation("small")
        assert result == "small"  # Not masked

        # Use content that matches a rule (indented code-like content)
        large_content = "\n".join(
            f"    line {i}: some code here with details"
            for i in range(50)
        )
        result = mask_observation(large_content)
        assert len(result) < len(large_content)  # Masked

    def test_mask_tool_output(self):
        from vertice_tui.core.context.masking import mask_tool_output, ToolMaskingResult

        result = mask_tool_output("small output", "grep")
        assert isinstance(result, ToolMaskingResult)
        assert "[grep]" in result.content
        assert result.compression_ratio == 1.0  # Small content not masked
        assert not result.was_masked


# =============================================================================
# SLIDING WINDOW COMPRESSOR TESTS
# =============================================================================


class TestWindowStrategy:
    """Test WindowStrategy enum."""

    def test_strategies_exist(self):
        from vertice_tui.core.context.sliding_window import WindowStrategy

        assert WindowStrategy.FIFO == "fifo"
        assert WindowStrategy.PRIORITY == "priority"
        assert WindowStrategy.HIERARCHICAL == "hierarchical"
        assert WindowStrategy.ADAPTIVE == "adaptive"


class TestWindowConfig:
    """Test WindowConfig dataclass."""

    def test_default_values(self):
        from vertice_tui.core.context.sliding_window import WindowConfig

        config = WindowConfig()
        assert config.max_tokens == 32_000
        assert config.target_tokens == 24_000
        assert config.trigger_percent == 0.85
        assert config.keep_recent_messages == 10


class TestMessage:
    """Test Message dataclass."""

    def test_message_creation(self):
        from vertice_tui.core.context.sliding_window import Message

        msg = Message(role="user", content="Hello world")

        assert msg.role == "user"
        assert msg.tokens > 0
        assert msg.content_hash is not None

    def test_message_to_dict(self):
        from vertice_tui.core.context.sliding_window import Message

        msg = Message(role="assistant", content="Response", priority=0.8)
        d = msg.to_dict()

        assert d["role"] == "assistant"
        assert d["content"] == "Response"
        assert d["priority"] == 0.8


class TestSlidingWindowCompressor:
    """Test SlidingWindowCompressor class."""

    def test_initialization(self):
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        compressor = SlidingWindowCompressor()
        assert compressor.total_tokens == 0
        assert compressor.message_count == 0

    def test_add_message(self):
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        compressor = SlidingWindowCompressor()
        result = compressor.add_message("user", "Hello")

        assert result is True
        assert compressor.message_count == 1
        assert compressor.total_tokens > 0

    def test_utilization(self):
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
        )

        config = WindowConfig(max_tokens=1000)
        compressor = SlidingWindowCompressor(config=config)
        compressor.add_message("user", "x" * 400)  # ~100 tokens

        assert 0 < compressor.utilization < 1.0

    def test_needs_compression(self):
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
        )

        config = WindowConfig(max_tokens=100, trigger_percent=0.5)
        compressor = SlidingWindowCompressor(config=config)
        compressor.add_message("user", "x" * 200)  # ~50 tokens

        assert compressor.needs_compression() is True

    def test_compress_fifo(self):
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
            WindowStrategy,
        )

        config = WindowConfig(
            max_tokens=500,
            target_tokens=200,
            keep_recent_messages=2,
            keep_first_messages=1,
        )
        compressor = SlidingWindowCompressor(config=config)

        # Add messages
        for i in range(10):
            compressor.add_message("user", f"Message {i} " * 20)

        result = compressor.compress(WindowStrategy.FIFO, force=True)

        assert result.success is True
        assert result.messages_after < result.messages_before

    def test_compress_priority(self):
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
            WindowStrategy,
        )

        config = WindowConfig(
            max_tokens=500,
            target_tokens=200,
            keep_recent_messages=2,
            keep_first_messages=1,
        )
        compressor = SlidingWindowCompressor(config=config)

        # Add messages with varying priority
        for i in range(10):
            priority = 0.1 if i % 2 == 0 else 0.9
            compressor.add_message("user", f"Message {i} " * 20, priority=priority)

        result = compressor.compress(WindowStrategy.PRIORITY, force=True)

        assert result.success is True

    def test_compress_hierarchical(self):
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
            WindowStrategy,
        )

        config = WindowConfig(
            max_tokens=1000,
            target_tokens=400,
            keep_recent_messages=3,
            keep_first_messages=1,
        )
        compressor = SlidingWindowCompressor(config=config)

        for i in range(15):
            compressor.add_message("user", f"Message {i} " * 30)

        result = compressor.compress(WindowStrategy.HIERARCHICAL, force=True)

        assert result.success is True

    def test_get_context_string(self):
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        compressor = SlidingWindowCompressor()
        compressor.add_message("user", "Hello")
        compressor.add_message("assistant", "Hi there!")

        context = compressor.get_context_string()

        assert "Hello" in context
        assert "Hi there!" in context

    def test_clear(self):
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        compressor = SlidingWindowCompressor()
        compressor.add_message("user", "Hello")
        compressor.clear()

        assert compressor.message_count == 0
        assert compressor.total_tokens == 0

    def test_get_stats(self):
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        compressor = SlidingWindowCompressor()
        compressor.add_message("user", "Hello")
        stats = compressor.get_stats()

        assert "total_tokens" in stats
        assert "message_count" in stats
        assert "utilization" in stats

    def test_singleton(self):
        from vertice_tui.core.context.sliding_window import get_sliding_window

        w1 = get_sliding_window()
        w2 = get_sliding_window()

        assert w1 is w2


# =============================================================================
# THOUGHT SIGNATURES TESTS
# =============================================================================


class TestThinkingLevel:
    """Test ThinkingLevel enum."""

    def test_levels_exist(self):
        from vertice_tui.core.context.thought_signatures import ThinkingLevel

        assert ThinkingLevel.MINIMAL == "minimal"
        assert ThinkingLevel.LOW == "low"
        assert ThinkingLevel.MEDIUM == "medium"
        assert ThinkingLevel.HIGH == "high"


class TestSignatureStatus:
    """Test SignatureStatus enum."""

    def test_statuses_exist(self):
        from vertice_tui.core.context.thought_signatures import SignatureStatus

        assert SignatureStatus.VALID == "valid"
        assert SignatureStatus.EXPIRED == "expired"
        assert SignatureStatus.BROKEN_CHAIN == "broken_chain"
        assert SignatureStatus.INVALID == "invalid"


class TestThoughtSignature:
    """Test ThoughtSignature dataclass."""

    def test_creation(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignature,
            ThinkingLevel,
        )

        sig = ThoughtSignature(
            signature_id="test123",
            version="v1",
            timestamp=time.time(),
            thinking_level=ThinkingLevel.HIGH,
            thought_hash="abc123",
            key_insights=["insight1", "insight2"],
            next_action="implement",
            chain_hash="prev123",
        )

        assert sig.signature_id == "test123"
        assert sig.thinking_level == ThinkingLevel.HIGH

    def test_to_dict(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignature,
            ThinkingLevel,
        )

        sig = ThoughtSignature(
            signature_id="test123",
            version="v1",
            timestamp=time.time(),
            thinking_level=ThinkingLevel.MEDIUM,
            thought_hash="abc123",
            key_insights=["insight1"],
            next_action="test",
            chain_hash="prev123",
        )

        d = sig.to_dict()
        assert d["id"] == "test123"
        assert d["level"] == "medium"

    def test_encode_decode(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignature,
            ThinkingLevel,
        )

        original = ThoughtSignature(
            signature_id="test123",
            version="v1",
            timestamp=time.time(),
            thinking_level=ThinkingLevel.HIGH,
            thought_hash="abc123",
            key_insights=["insight1", "insight2"],
            next_action="implement",
            chain_hash="prev123",
        )

        encoded = original.encode()
        decoded = ThoughtSignature.decode(encoded)

        assert decoded.signature_id == original.signature_id
        assert decoded.thinking_level == original.thinking_level

    def test_is_expired(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignature,
            ThinkingLevel,
        )

        # Recent signature - not expired
        recent = ThoughtSignature(
            signature_id="test123",
            version="v1",
            timestamp=time.time(),
            thinking_level=ThinkingLevel.MEDIUM,
            thought_hash="abc123",
            key_insights=[],
            next_action="test",
            chain_hash="prev123",
        )
        assert recent.is_expired(ttl=3600) is False

        # Old signature - expired
        old = ThoughtSignature(
            signature_id="test456",
            version="v1",
            timestamp=time.time() - 7200,  # 2 hours ago
            thinking_level=ThinkingLevel.MEDIUM,
            thought_hash="abc123",
            key_insights=[],
            next_action="test",
            chain_hash="prev123",
        )
        assert old.is_expired(ttl=3600) is True


class TestThoughtSignatureManager:
    """Test ThoughtSignatureManager class."""

    def test_initialization(self):
        from vertice_tui.core.context.thought_signatures import ThoughtSignatureManager

        manager = ThoughtSignatureManager()
        assert manager.get_thinking_level().value == "medium"

    def test_create_signature(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignatureManager,
            ThinkingLevel,
        )

        manager = ThoughtSignatureManager()
        sig = manager.create_signature(
            reasoning="Analyzing the problem...",
            insights=["Key insight 1", "Key insight 2"],
            next_action="Implement solution",
            level=ThinkingLevel.HIGH,
        )

        assert sig.signature_id is not None
        assert sig.thinking_level == ThinkingLevel.HIGH
        assert len(sig.key_insights) == 2

    def test_chain_building(self):
        from vertice_tui.core.context.thought_signatures import ThoughtSignatureManager

        manager = ThoughtSignatureManager()

        sig1 = manager.create_signature(
            reasoning="Step 1",
            insights=["Insight 1"],
            next_action="Continue",
        )

        sig2 = manager.create_signature(
            reasoning="Step 2",
            insights=["Insight 2"],
            next_action="Finish",
        )

        # Chain should have 2 signatures
        context = manager.get_reasoning_context()
        assert context.chain_length == 2

    def test_validate_signature(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignatureManager,
            SignatureStatus,
        )

        manager = ThoughtSignatureManager()
        sig = manager.create_signature(
            reasoning="Test",
            insights=["Test insight"],
            next_action="Test action",
        )

        validation = manager.validate(sig)
        assert validation.status == SignatureStatus.VALID
        assert validation.chain_position == 0

    def test_validate_expired_signature(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignatureManager,
            ThoughtSignature,
            ThinkingLevel,
            SignatureStatus,
        )

        manager = ThoughtSignatureManager(signature_ttl=1)

        # Create an old signature
        old_sig = ThoughtSignature(
            signature_id="old123",
            version="v1",
            timestamp=time.time() - 100,  # 100 seconds ago
            thinking_level=ThinkingLevel.MEDIUM,
            thought_hash="abc",
            key_insights=[],
            next_action="test",
            chain_hash="xxx",
        )

        validation = manager.validate(old_sig)
        assert validation.status == SignatureStatus.EXPIRED

    def test_get_reasoning_context(self):
        from vertice_tui.core.context.thought_signatures import ThoughtSignatureManager

        manager = ThoughtSignatureManager()

        manager.create_signature(
            reasoning="Analysis",
            insights=["Important finding"],
            next_action="Next step",
        )

        context = manager.get_reasoning_context()

        assert len(context.key_insights) >= 1
        assert context.chain_length == 1

    def test_clear_chain(self):
        from vertice_tui.core.context.thought_signatures import ThoughtSignatureManager

        manager = ThoughtSignatureManager()
        manager.create_signature(
            reasoning="Test",
            insights=["Test"],
            next_action="Test",
        )

        count = manager.clear_chain()
        assert count == 1
        assert manager.get_reasoning_context().chain_length == 0

    def test_set_thinking_level(self):
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignatureManager,
            ThinkingLevel,
        )

        manager = ThoughtSignatureManager()
        manager.set_thinking_level(ThinkingLevel.HIGH)

        assert manager.get_thinking_level() == ThinkingLevel.HIGH

    def test_get_stats(self):
        from vertice_tui.core.context.thought_signatures import ThoughtSignatureManager

        manager = ThoughtSignatureManager()
        manager.create_signature(
            reasoning="Test",
            insights=["Test"],
            next_action="Test",
        )

        stats = manager.get_stats()

        assert "chain_length" in stats
        assert stats["chain_length"] == 1

    def test_singleton(self):
        from vertice_tui.core.context.thought_signatures import get_thought_manager

        m1 = get_thought_manager()
        m2 = get_thought_manager()

        assert m1 is m2


class TestConvenienceFunction:
    """Test create_thought_signature convenience function."""

    def test_create_thought_signature(self):
        from vertice_tui.core.context.thought_signatures import (
            create_thought_signature,
            ThinkingLevel,
            ThoughtSignature,
        )

        encoded = create_thought_signature(
            reasoning="Quick test",
            insights=["Insight"],
            next_action="Done",
            level=ThinkingLevel.LOW,
        )

        # Should be a base64 string
        assert isinstance(encoded, str)

        # Should be decodable
        sig = ThoughtSignature.decode(encoded)
        assert sig.thinking_level == ThinkingLevel.LOW


# =============================================================================
# TOKEN DASHBOARD TESTS (Unit tests without Textual app)
# =============================================================================


class TestTokenBreakdown:
    """Test TokenBreakdown dataclass."""

    def test_creation(self):
        from vertice_tui.widgets.token_meter import TokenBreakdown

        breakdown = TokenBreakdown(
            messages=4000,
            files=2000,
            summary=1000,
            system=500,
            tools=500,
        )

        assert breakdown.total == 8000

    def test_to_dict(self):
        from vertice_tui.widgets.token_meter import TokenBreakdown

        breakdown = TokenBreakdown(messages=1000, files=500)
        d = breakdown.to_dict()

        assert d["messages"] == 1000
        assert d["files"] == 500
        assert d["total"] == 1500


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestContextIntegration:
    """Integration tests for context optimization components."""

    def test_masker_with_sliding_window(self):
        """Test ObservationMasker with SlidingWindowCompressor."""
        from vertice_tui.core.context.masking import ObservationMasker
        from vertice_tui.core.context.sliding_window import SlidingWindowCompressor

        masker = ObservationMasker()
        compressor = SlidingWindowCompressor()

        # Add messages, some with large tool outputs
        for i in range(10):
            content = f"Message {i} " * 10
            if i % 3 == 0:
                content += "\n" + "x" * 500  # Large output

            # Mask first, then add
            if masker.should_mask(content):
                result = masker.mask_content(content)
                content = result.masked_content

            compressor.add_message("user", content)

        assert compressor.message_count == 10
        # Masked content should be smaller
        assert compressor.total_tokens < 5000

    def test_thought_signatures_with_compression(self):
        """Test thought signatures preserved through compression."""
        from vertice_tui.core.context.thought_signatures import (
            ThoughtSignatureManager,
            ThinkingLevel,
        )
        from vertice_tui.core.context.sliding_window import (
            SlidingWindowCompressor,
            WindowConfig,
        )

        manager = ThoughtSignatureManager()
        config = WindowConfig(max_tokens=500, target_tokens=200)
        compressor = SlidingWindowCompressor(config=config)

        # Create signatures while adding messages
        for i in range(5):
            sig = manager.create_signature(
                reasoning=f"Step {i}",
                insights=[f"Insight {i}"],
                next_action=f"Action {i}",
                level=ThinkingLevel.MEDIUM,
            )
            compressor.add_message("assistant", f"Response {i}: {sig.encode()[:50]}")

        # Compress
        result = compressor.compress(force=True)
        assert result.success

        # Signatures should still be valid
        context = manager.get_reasoning_context()
        assert context.chain_length == 5

    def test_full_context_pipeline(self):
        """Test complete context optimization pipeline."""
        from vertice_tui.core.context import (
            ObservationMasker,
            SlidingWindowCompressor,
            ThoughtSignatureManager,
            WindowConfig,
            ThinkingLevel,
        )

        # Initialize components
        masker = ObservationMasker()
        config = WindowConfig(max_tokens=2000, target_tokens=1000)
        compressor = SlidingWindowCompressor(config=config)
        thought_manager = ThoughtSignatureManager()

        # Simulate a conversation
        messages = [
            ("user", "Analyze this code"),
            ("assistant", "I'll analyze the code...\n" + "x" * 500),
            ("user", "What about the tests?"),
            ("assistant", "Looking at tests...\n" + "x" * 500),
            ("user", "Fix the bug"),
            ("assistant", "Implementing fix...\n" + "x" * 500),
        ]

        for role, content in messages:
            # 1. Mask if needed
            if masker.should_mask(content):
                masked = masker.mask_content(content)
                content = masked.masked_content

            # 2. Add to compressor
            compressor.add_message(role, content)

            # 3. Create thought signature for assistant
            if role == "assistant":
                thought_manager.create_signature(
                    reasoning=content[:100],
                    insights=["Processing"],
                    next_action="Continue",
                    level=ThinkingLevel.MEDIUM,
                )

        # Verify pipeline
        assert compressor.message_count == 6
        assert thought_manager.get_reasoning_context().chain_length == 3

        # Compress if needed
        if compressor.needs_compression():
            result = compressor.compress()
            assert result.success


class TestModuleExports:
    """Test that all exports are available."""

    def test_masking_exports(self):
        from vertice_tui.core.context import (
            MaskingStrategy,
            ContentType,
            MaskingRule,
            MaskedContent,
            MaskingResult,
            ObservationMasker,
            mask_observation,
            mask_tool_output,
            DEFAULT_RULES,
        )

        assert MaskingStrategy is not None
        assert ObservationMasker is not None

    def test_sliding_window_exports(self):
        from vertice_tui.core.context import (
            WindowStrategy,
            RetentionPolicy,
            WindowConfig,
            WindowSlice,
            CompressionResult,
            Message,
            SlidingWindowCompressor,
            get_sliding_window,
        )

        assert WindowStrategy is not None
        assert SlidingWindowCompressor is not None

    def test_thought_signatures_exports(self):
        from vertice_tui.core.context import (
            SignatureStatus,
            ThinkingLevel,
            ThoughtSignature,
            SignatureValidation,
            ReasoningContext,
            ThoughtSignatureManager,
            get_thought_manager,
            create_thought_signature,
        )

        assert ThinkingLevel is not None
        assert ThoughtSignatureManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
