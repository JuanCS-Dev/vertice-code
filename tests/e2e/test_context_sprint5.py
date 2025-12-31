"""
E2E Tests for Sprint 5: Context Optimization Integration
=========================================================

Testing context optimization components in live TUI scenarios:
- ObservationMasker: Tool output compression
- SlidingWindowCompressor: Context window management
- ThoughtSignatures: Reasoning continuity
- TokenDashboard: Visual feedback
- Enhanced commands: /compact, /context, /tokens

Sprint 5 of Phase 10: UX Excellence & Test Integration

Soli Deo Gloria
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch


# =============================================================================
# 1. OBSERVATION MASKER E2E TESTS
# =============================================================================

class TestMaskingE2E:
    """E2E tests for ObservationMasker integration."""

    def test_masker_initialization(self, masker):
        """Verify masker initializes correctly."""
        assert masker is not None
        assert hasattr(masker, 'mask_content')

    def test_masker_returns_masked_content(self, masker, sample_tool_outputs):
        """Verify masker returns MaskedContent object."""
        from tui.core.context.masking import MaskedContent
        
        result = masker.mask_content(sample_tool_outputs["bash_ls"])
        assert isinstance(result, MaskedContent)
        assert hasattr(result, 'masked_content')
        assert hasattr(result, 'original_tokens')

    def test_mask_tool_output_returns_structured_result(self, sample_tool_outputs):
        """Verify mask_tool_output returns ToolMaskingResult."""
        from tui.core.context import mask_tool_output, ToolMaskingResult
        
        result = mask_tool_output(
            output=sample_tool_outputs["grep_result"],
            tool_name="grep",
            preserve_errors=True,
        )
        
        assert isinstance(result, ToolMaskingResult)
        assert hasattr(result, 'content')
        assert hasattr(result, 'compression_ratio')
        assert hasattr(result, 'tokens_saved')

    def test_controller_uses_masking(self):
        """Verify ChatController._execute_single_tool uses masking."""
        from tui.core.chat.controller import ChatController
        
        import inspect
        source = inspect.getsource(ChatController._execute_single_tool)
        assert 'mask_tool_output' in source

    def test_masker_stats(self, masker, sample_tool_outputs):
        """Verify masker tracks stats."""
        masker.mask_content(sample_tool_outputs["bash_ls"])
        
        stats = masker.get_stats()
        assert "total_masked" in stats or "calls" in stats


# =============================================================================
# 2. SLIDING WINDOW COMPRESSOR E2E TESTS
# =============================================================================

class TestCompressorE2E:
    """E2E tests for SlidingWindowCompressor integration."""

    def test_compressor_initialization(self, context_manager):
        """Verify compressor initializes correctly."""
        assert context_manager is not None
        assert hasattr(context_manager, 'add_message')

    def test_compressor_adds_messages(self, context_manager):
        """Verify messages are added correctly."""
        context_manager.add_message("user", "Hello!")
        context_manager.add_message("assistant", "Hi there!")
        
        assert context_manager.message_count == 2

    def test_compressor_tracks_utilization(self, context_manager):
        """Verify utilization is tracked correctly."""
        for i in range(20):
            content = f"Message {i}: " + "word " * 50
            context_manager.add_message("user" if i % 2 == 0 else "assistant", content)
        
        assert context_manager.utilization > 0

    def test_compressor_has_strategies(self):
        """Verify compression strategies exist."""
        from tui.core.context import WindowStrategy
        
        assert hasattr(WindowStrategy, 'FIFO')
        assert hasattr(WindowStrategy, 'PRIORITY')
        assert hasattr(WindowStrategy, 'HIERARCHICAL')

    def test_compressor_compress_method(self, context_manager):
        """Verify compress method exists and works."""
        from tui.core.context import WindowStrategy
        
        # Add enough messages to trigger compression
        for i in range(100):
            context_manager.add_message("user", f"Message {i} " * 50)
        
        if context_manager.needs_compression():
            result = context_manager.compress(strategy=WindowStrategy.FIFO, force=True)
            assert hasattr(result, 'tokens_saved')

    def test_compressor_get_stats(self, context_manager):
        """Verify get_stats returns correct structure."""
        context_manager.add_message("user", "Test message")
        
        stats = context_manager.get_stats()
        assert isinstance(stats, dict)


# =============================================================================
# 3. THOUGHT SIGNATURES E2E TESTS
# =============================================================================

class TestSignaturesE2E:
    """E2E tests for ThoughtSignatures integration."""

    def test_signature_manager_initialization(self, thought_manager):
        """Verify manager initializes correctly."""
        assert thought_manager is not None
        assert hasattr(thought_manager, 'create_signature')

    def test_thinking_levels_exist(self):
        """Verify thinking levels are defined."""
        from tui.core.context import ThinkingLevel
        
        assert hasattr(ThinkingLevel, 'MINIMAL')
        assert hasattr(ThinkingLevel, 'LOW')
        assert hasattr(ThinkingLevel, 'MEDIUM')
        assert hasattr(ThinkingLevel, 'HIGH')

    def test_thinking_level_detection_in_controller(self):
        """Verify thinking level detection works in controller."""
        from tui.core.chat.controller import ChatController
        
        assert hasattr(ChatController, '_determine_thinking_level')

    def test_agentic_loop_references_signatures(self):
        """Verify agentic loop uses thought signatures."""
        from tui.core.chat.controller import ChatController
        import inspect
        
        source = inspect.getsource(ChatController._run_agentic_loop)
        assert 'thought_manager' in source or 'ThinkingLevel' in source


# =============================================================================
# 4. COMMAND HANDLER E2E TESTS
# =============================================================================

class TestCommandsE2E:
    """E2E tests for enhanced commands."""

    @pytest.fixture
    def handler(self):
        """Create ClaudeParityHandler with mocks."""
        from tui.handlers.claude_parity import ClaudeParityHandler
        
        mock_app = MagicMock()
        mock_app.bridge = MagicMock()
        mock_app.query_one = MagicMock(return_value=MagicMock())
        
        return ClaudeParityHandler(mock_app)

    def test_handler_has_compact_method(self, handler):
        """Verify handler has compact method."""
        assert hasattr(handler, '_handle_compact')

    def test_handler_has_context_method(self, handler):
        """Verify handler has context method."""
        assert hasattr(handler, '_handle_context')

    @pytest.mark.asyncio
    async def test_compact_command_handles_low_utilization(self, handler, mock_view):
        """Test /compact shows info when compression not needed."""
        with patch('tui.core.context.get_sliding_window') as mock_get:
            mock_compressor = MagicMock()
            mock_compressor.utilization = 0.30
            mock_compressor.config = MagicMock(max_tokens=32000)
            mock_compressor.total_tokens = 9600
            mock_compressor.message_count = 20
            mock_get.return_value = mock_compressor
            
            await handler._handle_compact("", mock_view)
            
            # Should show info message, not compress
            last_message = mock_view.get_last_message()
            assert "Context" in last_message or "30%" in last_message or "Status" in last_message


# =============================================================================
# 5. WIDGET E2E TESTS
# =============================================================================

class TestWidgetsE2E:
    """E2E tests for token dashboard widgets."""

    def test_token_meter_exists(self):
        """Verify TokenMeter widget exists."""
        from tui.widgets.token_meter import TokenMeter
        
        meter = TokenMeter()
        assert meter is not None

    def test_token_meter_renders(self):
        """Verify TokenMeter renders progress correctly."""
        from tui.widgets.token_meter import TokenMeter
        
        meter = TokenMeter()
        meter.used = 16000
        meter.limit = 32000
        
        rendered = meter.render()
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    def test_mini_token_meter_format(self):
        """Verify MiniTokenMeter format is compact."""
        from tui.widgets.token_meter import MiniTokenMeter
        
        meter = MiniTokenMeter()
        meter.used = 8000
        meter.limit = 32000
        
        rendered = meter.render()
        assert "8k" in rendered
        assert "32k" in rendered

    def test_compression_indicator_exists(self):
        """Verify CompressionIndicator exists."""
        from tui.widgets.token_meter import CompressionIndicator
        
        indicator = CompressionIndicator()
        assert indicator is not None

    def test_thinking_level_indicator_levels(self):
        """Verify ThinkingLevelIndicator shows all levels."""
        from tui.widgets.token_meter import ThinkingLevelIndicator
        
        indicator = ThinkingLevelIndicator()
        
        for level in ["minimal", "low", "medium", "high"]:
            indicator.level = level
            rendered = indicator.render()
            assert level.capitalize() in rendered

    def test_token_dashboard_exists(self):
        """Verify TokenDashboard widget exists."""
        from tui.widgets.token_meter import TokenDashboard
        
        dashboard = TokenDashboard()
        assert dashboard is not None

    def test_token_dashboard_updates(self):
        """Verify TokenDashboard updates correctly."""
        from tui.widgets.token_meter import TokenDashboard
        
        dashboard = TokenDashboard()
        dashboard.update_usage(8000, 32000)
        
        stats = dashboard.get_stats()
        assert stats["used_tokens"] == 8000
        assert stats["max_tokens"] == 32000

    def test_token_dashboard_breakdown(self):
        """Verify TokenDashboard breakdown updates."""
        from tui.widgets.token_meter import TokenDashboard
        
        dashboard = TokenDashboard()
        dashboard.update_breakdown(
            messages=4000,
            files=2000,
            summary=1000,
            system=500,
        )
        
        stats = dashboard.get_stats()
        assert stats["breakdown"]["messages"] == 4000


# =============================================================================
# 6. INTEGRATION E2E TESTS
# =============================================================================

class TestIntegrationE2E:
    """Integration tests combining multiple components."""

    def test_status_bar_uses_mini_meter(self):
        """Test StatusBar uses MiniTokenMeter."""
        from tui.widgets.status_bar import StatusBar
        
        import inspect
        source = inspect.getsource(StatusBar.compose)
        assert "MiniTokenMeter" in source

    def test_app_uses_dashboard(self):
        """Test app.py uses TokenDashboard."""
        from tui.app import QwenApp
        
        import inspect
        source = inspect.getsource(QwenApp.compose)
        assert "TokenDashboard" in source

    def test_app_has_toggle_dashboard_action(self):
        """Test app has toggle dashboard action."""
        from tui.app import QwenApp
        
        assert hasattr(QwenApp, 'action_toggle_dashboard')

    def test_controller_has_masking_integration(self):
        """Test controller integrates masking."""
        from tui.core.chat.controller import ChatController
        
        import inspect
        source = inspect.getsource(ChatController._execute_single_tool)
        assert 'mask_tool_output' in source

    def test_handler_has_context_command(self):
        """Test handler has /context command."""
        from tui.handlers.claude_parity import ClaudeParityHandler
        
        import inspect
        source = inspect.getsource(ClaudeParityHandler.handle)
        assert '/context' in source


# =============================================================================
# 7. PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance tests for context components."""

    def test_masking_is_fast(self, masker, sample_tool_outputs):
        """Test masking is fast enough."""
        import time
        
        start = time.perf_counter()
        for _ in range(100):
            masker.mask_content(sample_tool_outputs["bash_ls"])
        duration = time.perf_counter() - start
        
        assert duration < 1.0, f"Masking took {duration}s for 100 iterations"

    def test_widget_render_is_fast(self):
        """Test widget rendering is fast."""
        from tui.widgets.token_meter import TokenMeter, MiniTokenMeter
        import time
        
        meter = TokenMeter()
        meter.used = 16000
        meter.limit = 32000
        
        start = time.perf_counter()
        for _ in range(1000):
            meter.render()
        duration = time.perf_counter() - start
        
        assert duration < 0.5, f"TokenMeter render took {duration}s for 1000 iterations"

    def test_dashboard_stats_is_fast(self):
        """Test dashboard stats is fast."""
        from tui.widgets.token_meter import TokenDashboard
        import time
        
        dashboard = TokenDashboard()
        dashboard.update_usage(8000, 32000)
        
        start = time.perf_counter()
        for _ in range(1000):
            dashboard.get_stats()
        duration = time.perf_counter() - start
        
        assert duration < 0.1, f"Dashboard stats took {duration}s for 1000 iterations"
