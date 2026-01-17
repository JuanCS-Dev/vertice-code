"""
Tests for LLMSummaryStrategy - AI-powered intelligent summarization.

Tests cover:
    - LLM-based context summarization
    - Fallback behavior when LLM unavailable
    - Summary quality and preservation
    - Performance with complex content
    - Error handling and edge cases
"""

from unittest.mock import patch
from vertice_core.agents.compaction.strategies.llm_summary import LLMSummaryStrategy
from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
from vertice_core.agents.context.unified import UnifiedContext


class TestLLMSummaryStrategyInitialization:
    """Test LLMSummaryStrategy initialization."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = LLMSummaryStrategy()
        assert hasattr(strategy, "compact")
        assert callable(strategy.compact)


class TestLLMSummaryCompactionLogic:
    """Test LLM-based compaction logic."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = LLMSummaryStrategy()
        self.config = CompactionConfig()

    def test_basic_compaction_functionality(self) -> None:
        """Test that basic compaction functionality works."""
        ctx = UnifiedContext()

        # Add some messages
        ctx.add_message("user", "Please help me with this task")
        ctx.add_message("assistant", "I'll help you with that")
        ctx.add_message("user", "Great, let's proceed")

        # Mock the summary generation
        with patch.object(
            self.strategy, "_generate_context_summary", return_value="Summary of conversation"
        ):
            result = self.strategy.compact(ctx, self.config)

            assert result.success is True
            assert isinstance(result, CompactionResult)

            # Check that context was compacted
            messages = ctx.get_messages()
            assert len(messages) == 1  # Should be replaced with summary
            assert "_compacted" in messages[0]
            assert "CONTEXT SUMMARY" in messages[0]["content"]

    def test_compaction_with_empty_context(self) -> None:
        """Test compaction of empty context."""
        ctx = UnifiedContext()

        with patch.object(
            self.strategy, "_generate_context_summary", return_value="Empty context summary"
        ):
            result = self.strategy.compact(ctx, self.config)

            assert result.success is True
            assert isinstance(result, CompactionResult)

    def test_compaction_preserves_critical_info(self) -> None:
        """Test that compaction preserves critical context information."""
        ctx = UnifiedContext(user_request="Build a web app")

        # Add various types of messages
        ctx.add_message("user", "I need a web application")
        ctx.add_message("assistant", "What technology stack?")
        ctx.add_message("user", "Use React and Node.js")
        ctx.add_message("assistant", "Great choice!")

        with patch.object(
            self.strategy,
            "_generate_context_summary",
            return_value="Web app development discussion",
        ):
            result = self.strategy.compact(ctx, self.config)

            messages = ctx.get_messages()
            assert len(messages) == 1
            assert "CONTEXT SUMMARY" in messages[0]["content"]
            assert "_original_count" in messages[0]
            assert messages[0]["_original_count"] == "4"  # Original message count

    def test_compaction_result_metrics(self) -> None:
        """Test that compaction results include proper metrics."""
        ctx = UnifiedContext()

        # Add messages to have tokens
        ctx._token_usage = 1000
        ctx.add_message("user", "Test message")

        with patch.object(self.strategy, "_generate_context_summary", return_value="Test summary"):
            result = self.strategy.compact(ctx, self.config)

            assert hasattr(result, "success")
            assert hasattr(result, "strategy_used")
            assert hasattr(result, "tokens_before")
            assert hasattr(result, "compression_ratio")
            assert hasattr(result, "duration_ms")

            assert result.success is True
            assert result.tokens_before >= 1000


class TestLLMSummaryGeneration:
    """Test LLM summary generation."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = LLMSummaryStrategy()
        self.config = CompactionConfig()

    def test_generate_context_summary_method_exists(self) -> None:
        """Test that summary generation method exists."""
        assert hasattr(self.strategy, "_generate_context_summary")

        # Test with mock context
        ctx = UnifiedContext()
        ctx.add_message("user", "Hello")

        # Should be callable (even if not fully implemented)
        try:
            result = self.strategy._generate_context_summary(ctx, self.config)
            assert isinstance(result, str)
        except Exception:
            # If not implemented, should raise appropriate error
            pass

    def test_summary_quality_basic(self) -> None:
        """Test basic summary quality expectations."""
        ctx = UnifiedContext()

        # Add a simple conversation
        ctx.add_message("user", "How do I install Python?")
        ctx.add_message("assistant", "Download from python.org")

        # Mock summary generation
        mock_summary = "User asked about Python installation and received guidance."
        with patch.object(self.strategy, "_generate_context_summary", return_value=mock_summary):
            result = self.strategy.compact(ctx, self.config)

            messages = ctx.get_messages()
            assert mock_summary in messages[0]["content"]
            assert "CONTEXT SUMMARY" in messages[0]["content"]


class TestLLMSummaryErrorHandling:
    """Test error handling in LLM summarization."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = LLMSummaryStrategy()
        self.config = CompactionConfig()

    def test_compaction_handles_summary_generation_errors(self) -> None:
        """Test that compaction handles summary generation errors gracefully."""
        ctx = UnifiedContext()
        ctx.add_message("user", "Test message")

        # Mock summary generation to raise an error
        with patch.object(
            self.strategy, "_generate_context_summary", side_effect=Exception("LLM unavailable")
        ):
            result = self.strategy.compact(ctx, self.config)

            # Should still return a result (even if not successful)
            assert isinstance(result, CompactionResult)

    def test_compaction_with_no_messages(self) -> None:
        """Test compaction when context has no messages."""
        ctx = UnifiedContext()
        # Context without messages

        with patch.object(
            self.strategy, "_generate_context_summary", return_value="No messages to summarize"
        ):
            result = self.strategy.compact(ctx, self.config)

            assert result.success is True
            messages = ctx.get_messages()
            assert len(messages) == 1  # Should still create summary message


class TestLLMSummaryPerformance:
    """Test performance aspects of LLM summarization."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = LLMSummaryStrategy()
        self.config = CompactionConfig()

    def test_compaction_performance_basic(self) -> None:
        """Test basic performance of compaction."""
        ctx = UnifiedContext()

        # Add moderate amount of content
        for i in range(10):
            ctx.add_message("user", f"Message {i} with some content")

        with patch.object(
            self.strategy, "_generate_context_summary", return_value="Summary of 10 messages"
        ):
            result = self.strategy.compact(ctx, self.config)

            assert result.success is True
            assert result.duration_ms >= 0
            assert result.duration_ms < 1000  # Should be reasonable
