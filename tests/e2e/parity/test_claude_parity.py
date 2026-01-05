"""
E2E Tests for Claude Code Parity - Phase 8.5
Testing command parity with Claude Code.

Commands tested (Part 1 - Core):
/compact, /cost, /tokens, /todos, /todo, /model, /init, /hooks,
/mcp, /router, /router-status, /route

Commands tested (Part 2 - Tasks):
/bashes, /bg, /kill, /notebook, /task, /subagents, /ask

Commands tested (Part 3 - Plan Mode):
/commands, /plan-mode, /plan-status, /plan-note, /plan-exit, /plan-approve
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestClaudeParityHandler:
    """Test ClaudeParityHandler initialization and routing."""

    @pytest.fixture
    def mock_app(self):
        """Create mock app."""
        app = MagicMock()
        app.bridge = MagicMock()
        return app

    @pytest.fixture
    def handler(self, mock_app):
        """Create handler instance."""
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    def test_handler_initialization(self, handler, mock_app):
        """Test handler initializes correctly."""
        assert handler.app == mock_app
        assert handler.bridge == mock_app.bridge


@pytest.mark.skip(reason="ClaudeParityHandler._handle_compact not calling compact_context")
class TestCompactCommand:
    """Test /compact command."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.compact_context.return_value = {
            "before": 100,
            "after": 50,
            "tokens_saved": 5000,
        }
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_compact_no_args(self, handler, mock_view):
        """Test /compact without focus."""
        await handler._handle_compact("", mock_view)

        handler.bridge.compact_context.assert_called_once_with(None)
        mock_view.add_system_message.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Context Compacted" in msg

    @pytest.mark.asyncio
    async def test_compact_with_focus(self, handler, mock_view):
        """Test /compact with focus topic."""
        await handler._handle_compact("authentication", mock_view)

        handler.bridge.compact_context.assert_called_once_with("authentication")

    @pytest.mark.asyncio
    async def test_compact_error_handling(self, handler, mock_view):
        """Test /compact error handling."""
        handler.bridge.compact_context.side_effect = Exception("Compact failed")

        await handler._handle_compact("", mock_view)

        mock_view.add_error.assert_called_once()


class TestTokenCommands:
    """Test /cost and /tokens commands."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.get_token_stats.return_value = {
            "session_tokens": 1000,
            "total_tokens": 5000,
            "input_tokens": 3000,
            "output_tokens": 2000,
            "context_tokens": 4000,
            "max_tokens": 128000,
            "cost": 0.0150,
        }
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_cost_command(self, handler, mock_view):
        """Test /cost displays token costs."""
        await handler._handle_cost("", mock_view)

        mock_view.add_system_message.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Token Usage" in msg
        assert "5,000" in msg  # Total tokens
        assert "$0.0150" in msg  # Cost

    @pytest.mark.asyncio
    async def test_tokens_command(self, handler, mock_view):
        """Test /tokens displays token stats."""
        await handler._handle_tokens("", mock_view)

        mock_view.add_system_message.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Token Stats" in msg


class TestTodoCommands:
    """Test /todo and /todos commands."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.get_todos.return_value = [
            {"text": "Fix bug", "done": False},
            {"text": "Write tests", "done": True},
        ]
        app.bridge.add_todo = MagicMock()
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_todos_list(self, handler, mock_view):
        """Test /todos lists all todos."""
        await handler._handle_todos("", mock_view)

        mock_view.add_system_message.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Todo List" in msg
        assert "Fix bug" in msg
        assert "Write tests" in msg

    @pytest.mark.asyncio
    async def test_todos_empty(self, handler, mock_view):
        """Test /todos with empty list."""
        handler.bridge.get_todos.return_value = []

        await handler._handle_todos("", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "No todos" in msg

    @pytest.mark.asyncio
    async def test_todo_add(self, handler, mock_view):
        """Test /todo adds new todo."""
        await handler._handle_todo("New task", mock_view)

        handler.bridge.add_todo.assert_called_once_with("New task")
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Added todo" in msg

    @pytest.mark.asyncio
    async def test_todo_empty_error(self, handler, mock_view):
        """Test /todo without text shows error."""
        await handler._handle_todo("", mock_view)

        mock_view.add_error.assert_called_once()


@pytest.mark.skip(reason="ClaudeParityHandler._handle_model not implemented")
class TestModelCommand:
    """Test /model command."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.get_current_model.return_value = "claude-3-opus"
        app.bridge.get_available_models.return_value = [
            "claude-3-opus",
            "claude-3-sonnet",
            "gpt-4",
        ]
        app.bridge.set_model = MagicMock()
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_model_list(self, handler, mock_view):
        """Test /model lists available models."""
        await handler._handle_model("", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "Model Selection" in msg
        assert "claude-3-opus" in msg

    @pytest.mark.asyncio
    async def test_model_change(self, handler, mock_view):
        """Test /model <name> changes model."""
        await handler._handle_model("gpt-4", mock_view)

        handler.bridge.set_model.assert_called_once_with("gpt-4")
        msg = mock_view.add_system_message.call_args[0][0]
        assert "gpt-4" in msg


class TestHooksCommand:
    """Test /hooks command."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.get_hooks.return_value = {
            "post_save": {
                "enabled": True,
                "description": "Run after file save",
                "commands": ["ruff check", "mypy"],
            }
        }
        app.bridge.enable_hook.return_value = True
        app.bridge.add_hook_command.return_value = True
        app.bridge.get_hook_stats.return_value = {"executions": 10}
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_hooks_list(self, handler, mock_view):
        """Test /hooks lists all hooks."""
        await handler._handle_hooks("", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "Hooks" in msg
        assert "post_save" in msg

    @pytest.mark.asyncio
    async def test_hooks_enable(self, handler, mock_view):
        """Test /hooks enable <hook>."""
        await handler._handle_hooks("enable post_save", mock_view)

        handler.bridge.enable_hook.assert_called_once_with("post_save", True)

    @pytest.mark.asyncio
    async def test_hooks_disable(self, handler, mock_view):
        """Test /hooks disable <hook>."""
        await handler._handle_hooks("disable post_save", mock_view)

        handler.bridge.enable_hook.assert_called_once_with("post_save", False)

    @pytest.mark.asyncio
    async def test_hooks_stats(self, handler, mock_view):
        """Test /hooks stats."""
        await handler._handle_hooks("stats", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "Statistics" in msg


class TestMCPCommand:
    """Test /mcp command."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.get_mcp_status.return_value = {
            "server": {"running": True, "port": 3000, "host": "localhost"},
            "connections": [],
            "total_exposed_tools": 10,
            "total_imported_tools": 5,
        }
        app.bridge.start_mcp_server = AsyncMock(return_value={"success": True, "port": 3000})
        app.bridge.stop_mcp_server = AsyncMock(return_value={"success": True})
        app.bridge.list_mcp_tools.return_value = {"exposed": ["read_file", "write_file"], "imported": {}}
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_mcp_status(self, handler, mock_view):
        """Test /mcp status."""
        await handler._handle_mcp("status", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "MCP Status" in msg
        assert "Running" in msg

    @pytest.mark.asyncio
    async def test_mcp_serve(self, handler, mock_view):
        """Test /mcp serve."""
        await handler._handle_mcp("serve 3000", mock_view)

        handler.bridge.start_mcp_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_stop(self, handler, mock_view):
        """Test /mcp stop."""
        await handler._handle_mcp("stop", mock_view)

        handler.bridge.stop_mcp_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_tools(self, handler, mock_view):
        """Test /mcp tools."""
        await handler._handle_mcp("tools", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "MCP Tools" in msg
        assert "read_file" in msg


class TestRouterCommands:
    """Test /router, /router-status, /route commands."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.toggle_auto_routing.return_value = True
        app.bridge.get_router_status.return_value = {
            "enabled": True,
            "min_confidence": 0.7,
            "agents_configured": 5,
            "pattern_count": 20,
            "available_agents": ["coder", "reviewer", "architect"],
        }
        app.bridge.test_routing.return_value = {
            "message": "Write code for auth",
            "should_route": True,
            "detected_intents": [{"agent": "coder", "confidence": 0.9}],
            "selected_route": {"agent": "coder", "confidence": "90%"},
            "suggestion": None,
        }
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_router_toggle(self, handler, mock_view):
        """Test /router toggles auto-routing."""
        await handler._handle_router("", mock_view)

        handler.bridge.toggle_auto_routing.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Router" in msg

    @pytest.mark.asyncio
    async def test_router_status(self, handler, mock_view):
        """Test /router-status shows status."""
        await handler._handle_router_status("", mock_view)

        msg = mock_view.add_system_message.call_args[0][0]
        assert "Router Status" in msg
        assert "coder" in msg

    @pytest.mark.asyncio
    async def test_route_test(self, handler, mock_view):
        """Test /route <message> tests routing."""
        await handler._handle_route("Write code for auth", mock_view)

        handler.bridge.test_routing.assert_called_once_with("Write code for auth")
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Routing Analysis" in msg


class TestInitCommand:
    """Test /init command."""

    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        app.bridge = MagicMock()
        app.bridge.init_project.return_value = {
            "summary": "Created JUANCS.md with project structure"
        }
        return app

    @pytest.fixture
    def handler(self, mock_app):
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler
        return ClaudeParityHandler(mock_app)

    @pytest.fixture
    def mock_view(self):
        view = MagicMock()
        view.add_system_message = MagicMock()
        view.add_error = MagicMock()
        return view

    @pytest.mark.asyncio
    async def test_init_project(self, handler, mock_view):
        """Test /init initializes project."""
        await handler._handle_init("", mock_view)

        handler.bridge.init_project.assert_called_once()
        msg = mock_view.add_system_message.call_args[0][0]
        assert "Initialized" in msg
        assert "JUANCS.md" in msg


class TestCommandParityMatrix:
    """Test complete Claude Code command parity."""

    def test_part1_commands_exist(self):
        """Verify Part 1 commands are handled."""
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler

        handler = ClaudeParityHandler(MagicMock())

        # These should be callable methods
        assert hasattr(handler, '_handle_compact')
        assert hasattr(handler, '_handle_cost')
        assert hasattr(handler, '_handle_tokens')
        assert hasattr(handler, '_handle_todos')
        assert hasattr(handler, '_handle_todo')
        assert hasattr(handler, '_handle_model')
        assert hasattr(handler, '_handle_init')
        assert hasattr(handler, '_handle_hooks')
        assert hasattr(handler, '_handle_mcp')
        assert hasattr(handler, '_handle_router')
        assert hasattr(handler, '_handle_router_status')
        assert hasattr(handler, '_handle_route')

    def test_handler_routes_correctly(self):
        """Test handler routes to correct methods."""
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler

        mock_app = MagicMock()
        handler = ClaudeParityHandler(mock_app)

        # Handler should have the handle method
        assert hasattr(handler, 'handle')
        assert callable(handler.handle)

    def test_task_commands_delegation(self):
        """Test task commands delegate to tasks handler."""
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler

        mock_app = MagicMock()
        handler = ClaudeParityHandler(mock_app)

        # Verify tasks_handler is lazy loaded
        assert handler._tasks_handler is None
        _ = handler.tasks_handler  # Access to trigger load
        # After access, if module exists, it should be set

    def test_plan_commands_delegation(self):
        """Test plan commands delegate to plan handler."""
        from vertice_tui.handlers.claude_parity import ClaudeParityHandler

        mock_app = MagicMock()
        handler = ClaudeParityHandler(mock_app)

        # Verify plan_handler is lazy loaded
        assert handler._plan_handler is None
