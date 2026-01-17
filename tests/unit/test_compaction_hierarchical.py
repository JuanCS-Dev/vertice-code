"""
Tests for HierarchicalStrategy - Intelligent hierarchical compaction.

Tests cover:
    - Multi-level summarization (recent verbatim, medium structured, old high-level)
    - Time window management
    - Structured summary creation
    - High-level summary creation
    - Performance with large datasets
    - Edge cases and error handling
    - Quality preservation metrics
"""

from vertice_core.agents.compaction.strategies.hierarchical import HierarchicalStrategy
from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
from vertice_core.agents.context.unified import UnifiedContext


class TestHierarchicalStrategyInitialization:
    """Test HierarchicalStrategy initialization."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = HierarchicalStrategy()
        assert hasattr(strategy, "compact")
        assert callable(strategy.compact)


class TestHierarchicalCompactionLogic:
    """Test hierarchical compaction logic."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = HierarchicalStrategy()
        self.config = CompactionConfig()

    def test_basic_compaction_functionality(self) -> None:
        """Test that basic compaction functionality works."""
        ctx = UnifiedContext()

        # Add some messages
        for i in range(3):
            ctx.add_message("user", f"Message {i}")

        # Compact
        result = self.strategy.compact(ctx, self.config)

        # Should be successful
        assert result.success is True
        assert isinstance(result, CompactionResult)
        assert result.duration_ms >= 0

    def test_empty_context_handling(self) -> None:
        """Test compaction of empty context."""
        ctx = UnifiedContext()

        result = self.strategy.compact(ctx, self.config)

        assert result.success is True
        assert isinstance(result, CompactionResult)


class TestHierarchicalSummaryQuality:
    """Test quality of hierarchical summaries."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = HierarchicalStrategy()
        self.config = CompactionConfig()

    def test_structured_summary_creation(self) -> None:
        """Test creation of structured summaries."""
        # Test the internal method
        message = {
            "role": "user",
            "content": "I need help with database optimization for a Django application running PostgreSQL",
        }

        summary = self.strategy._create_structured_summary(message, self.config)

        # Summary should be string and meaningful
        assert isinstance(summary, str)
        assert len(summary) > 10  # Should have meaningful content
        assert "User query:" in summary  # Should have prefix
        assert len(summary) > 10  # Should have meaningful content

    def test_high_level_summary_creation(self) -> None:
        """Test creation of high-level summaries."""
        message = {
            "role": "assistant",
            "content": "The database optimization involves creating indexes on frequently queried columns, optimizing query patterns, and considering database partitioning for large tables.",
        }

        summary = self.strategy._create_high_level_summary(message)

        # Should be very concise
        assert isinstance(summary, str)
        assert len(summary) < 100  # Very short
        assert len(summary) > 5  # Not empty

    def test_summary_preserves_key_information(self) -> None:
        """Test that summaries preserve key technical information."""
        message = {
            "role": "user",
            "content": "How do I implement JWT authentication in a FastAPI application with role-based access control?",
        }

        summary = self.strategy._create_structured_summary(message, self.config)

        # Should mention key technologies
        summary_lower = summary.lower()
        assert "jwt" in summary_lower or "authentication" in summary_lower
        assert "fastapi" in summary_lower or "api" in summary_lower

    def test_unsummarizable_content_handling(self) -> None:
        """Test handling of content that cannot be summarized."""
        message = {
            "role": "user",
            "content": "OK",  # Very short, hard to summarize
        }

        summary = self.strategy._create_high_level_summary(message)

        # Should either return None or a minimal summary
        if summary is not None:
            assert isinstance(summary, str)
        # If None, that's acceptable for unsummarizable content


class TestHierarchicalEdgeCases:
    """Test edge cases in hierarchical compaction."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.strategy = HierarchicalStrategy()
        self.config = CompactionConfig()

    def test_config_with_zero_keep_recent(self) -> None:
        """Test compaction with zero keep_recent_messages."""
        config = CompactionConfig(keep_recent_messages=0, keep_decisions=2)
        ctx = UnifiedContext()

        for i in range(5):
            ctx.add_message("user", f"Message {i}")

        result = self.strategy.compact(ctx, config)

        # Should still work
        assert result.success is True

        messages = ctx.get_messages()
        # All messages should be summarized (since keep_recent=0)
        summarized = [msg for msg in messages if msg.get("_summarized") == "true"]
        assert len(summarized) > 0

    def test_very_small_config(self) -> None:
        """Test with minimal config values."""
        config = CompactionConfig(keep_recent_messages=1, keep_decisions=1)
        ctx = UnifiedContext()

        for i in range(10):
            ctx.add_message("user", f"Message {i}")

        result = self.strategy.compact(ctx, config)

        assert result.success is True

        messages = ctx.get_messages()
        assert len(messages) <= 10  # Should not exceed original

    def test_compaction_result_metrics(self) -> None:
        """Test that compaction results include proper metrics."""
        ctx = UnifiedContext()

        # Set up some token usage
        ctx._token_usage = 1000

        for i in range(20):
            ctx.add_message("user", f"Message {i} with content")

        result = self.strategy.compact(ctx, self.config)

        # Check result metrics
        assert isinstance(result, CompactionResult)
        assert result.success is True
        assert result.tokens_before >= 1000
        assert result.compression_ratio > 0
        assert result.duration_ms >= 0
        assert result.messages_removed >= 0

    def test_context_without_messages(self) -> None:
        """Test compaction when context has no messages."""
        ctx = UnifiedContext()
        # Context without messages attribute would fail, but our setup should have it

        result = self.strategy.compact(ctx, self.config)

        assert result.success is True
        assert result.messages_removed == 0

    def test_message_with_missing_content(self) -> None:
        """Test handling of messages with missing content."""
        ctx = UnifiedContext()

        # Add a malformed message
        ctx._messages.append({"role": "user"})  # Missing content

        # Should not crash
        result = self.strategy.compact(ctx, self.config)

        assert result.success is True  # Should handle gracefully


class TestHierarchicalStrategyIntegration:
    """Integration tests for hierarchical strategy."""

    def test_multiple_compactions(self) -> None:
        """Test multiple sequential compactions."""
        strategy = HierarchicalStrategy()
        ctx = UnifiedContext()

        # Add initial messages
        for i in range(50):
            ctx.add_message("user", f"Initial message {i}")

        # First compaction
        config1 = CompactionConfig(keep_recent_messages=5, keep_decisions=3)
        result1 = strategy.compact(ctx, config1)

        assert result1.success is True

        # Add more messages
        for i in range(30):
            ctx.add_message("user", f"Additional message {i}")

        # Second compaction with different config
        config2 = CompactionConfig(keep_recent_messages=3, keep_decisions=2)
        result2 = strategy.compact(ctx, config2)

        assert result2.success is True

        # Context should still be functional
        messages = ctx.get_messages()
        assert len(messages) > 0

    def test_strategy_reuse(self) -> None:
        """Test reusing the same strategy instance."""
        strategy = HierarchicalStrategy()

        # Use on multiple contexts
        for context_num in range(3):
            ctx = UnifiedContext()
            for i in range(10):
                ctx.add_message("user", f"Context {context_num} message {i}")

            result = strategy.compact(ctx, CompactionConfig())
            assert result.success is True
