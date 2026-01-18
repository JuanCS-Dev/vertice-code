"""
TUI Stability Test Suite - Swiss Watch Validation.

Comprehensive tests for TUI stability:
- Import validation (all handlers, widgets, core modules)
- Bridge initialization
- Command routing
- Error recovery

Run with: pytest tests/tui/test_stability_suite.py -v
"""

from __future__ import annotations

import pytest


class TestTUIImports:
    """Validate all TUI components import without errors."""

    def test_app_imports(self) -> None:
        """Test main app module imports."""
        from vertice_tui.app import VerticeApp

        assert VerticeApp is not None

    @pytest.mark.parametrize(
        "handler",
        [
            "basic",
            "agents",
            "claude_parity",
            "session",
            "operations",
            "context_commands",
            "a2a",
            "autoaudit",
        ],
    )
    def test_handlers_import(self, handler: str) -> None:
        """Test all handlers import successfully."""
        import importlib

        module = importlib.import_module(f"vertice_tui.handlers.{handler}")
        assert module is not None

    @pytest.mark.parametrize(
        "widget",
        [
            "response_view",
            "autocomplete",
            "status_bar",
            "token_meter",
            "loading",
            "fuzzy_search_modal",
            "modal",
            "breadcrumb",
        ],
    )
    def test_widgets_import(self, widget: str) -> None:
        """Test all widgets import successfully."""
        import importlib

        module = importlib.import_module(f"vertice_tui.widgets.{widget}")
        assert module is not None

    @pytest.mark.parametrize(
        "core_module",
        [
            "bridge",
            "llm_client",
            "governance",
            "safe_executor",
            "agentic_prompt",
            "formatting",
            "openresponses_events",
        ],
    )
    def test_core_modules_import(self, core_module: str) -> None:
        """Test all core modules import successfully."""
        import importlib

        module = importlib.import_module(f"vertice_tui.core.{core_module}")
        assert module is not None


class TestBridgeInitialization:
    """Validate Bridge initializes correctly."""

    def test_bridge_singleton(self) -> None:
        """Test bridge singleton creation."""
        from vertice_tui.core.bridge import get_bridge

        bridge = get_bridge()
        assert bridge is not None

    def test_bridge_connected(self) -> None:
        """Test bridge reports connection status."""
        from vertice_tui.core.bridge import get_bridge

        bridge = get_bridge()
        # is_connected should return bool without crashing
        assert isinstance(bridge.is_connected, bool)

    def test_bridge_has_tools(self) -> None:
        """Test bridge has tool bridge initialized."""
        from vertice_tui.core.bridge import get_bridge

        bridge = get_bridge()
        assert bridge.tools is not None
        assert bridge.tools.get_tool_count() >= 0

    def test_bridge_has_agents(self) -> None:
        """Test bridge has agent manager initialized."""
        from vertice_tui.core.bridge import get_bridge

        bridge = get_bridge()
        assert bridge.agents is not None


class TestCommandRouter:
    """Validate command router functionality."""

    def test_router_imports(self) -> None:
        """Test router can be imported."""
        from vertice_tui.handlers.router import CommandRouter

        assert CommandRouter is not None

    def test_router_has_handlers(self) -> None:
        """Test router has lazy handler properties."""
        from vertice_tui.handlers.router import CommandRouter

        # Create mock app with required attributes
        class MockApp:
            bridge = None

        router = CommandRouter(MockApp())

        # Verify handler properties exist
        assert hasattr(router, "basic")
        assert hasattr(router, "agents")
        assert hasattr(router, "autoaudit")


class TestAutoAuditIntegration:
    """Validate AutoAudit service integration."""

    def test_autoaudit_imports(self) -> None:
        """Test autoaudit modules import."""
        from vertice_tui.core.autoaudit import AutoAuditService
        from vertice_tui.core.autoaudit import SCENARIOS

        assert AutoAuditService is not None
        assert len(SCENARIOS) > 0

    def test_autoaudit_handler_imports(self) -> None:
        """Test autoaudit handler imports."""
        from vertice_tui.handlers.autoaudit import AutoAuditHandler

        assert AutoAuditHandler is not None


class TestHelpContent:
    """Validate help content includes all commands."""

    def test_help_has_autoaudit(self) -> None:
        """Test /autoaudit appears in help commands."""
        from vertice_tui.constants.help_topics import HELP_COMMANDS

        assert "/autoaudit" in HELP_COMMANDS

    def test_help_topics_complete(self) -> None:
        """Test all help topics are accessible."""
        from vertice_tui.constants.help_topics import HELP_TOPICS

        assert "" in HELP_TOPICS  # Main help
        assert "commands" in HELP_TOPICS
        assert "agents" in HELP_TOPICS
        assert "tools" in HELP_TOPICS
        assert "keys" in HELP_TOPICS
        assert "tips" in HELP_TOPICS
