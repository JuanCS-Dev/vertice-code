"""
Tests for HooksManager - Claude Code-style file operation hooks.

Tests cover:
- Initialization and lazy loading
- Hook configuration (CRUD operations)
- Hook execution
- Persistence (load/save config)
- Statistics

Based on pytest patterns from Anthropic's Claude Code.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from vertice_tui.core.hooks_manager import HooksManager


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / ".juancs"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def hooks_manager(temp_config_dir):
    """Create HooksManager with temp config."""
    return HooksManager(config_dir=temp_config_dir)


@pytest.fixture
def hooks_manager_with_config(temp_config_dir):
    """Create HooksManager with pre-existing config."""
    config_file = temp_config_dir / "hooks.json"
    config_file.write_text(
        json.dumps(
            {
                "post_write": {
                    "enabled": True,
                    "description": "Run after file write",
                    "commands": ["ruff check $FILE", "ruff format $FILE"],
                },
                "post_edit": {
                    "enabled": False,
                    "description": "Run after file edit",
                    "commands": [],
                },
                "post_delete": {
                    "enabled": False,
                    "description": "Run after file delete",
                    "commands": [],
                },
                "pre_commit": {
                    "enabled": True,
                    "description": "Run before git commit",
                    "commands": ["pytest -x"],
                },
            }
        )
    )
    return HooksManager(config_dir=temp_config_dir)


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================


class TestHooksManagerInit:
    """Tests for HooksManager initialization."""

    def test_init_default_config_dir(self):
        """Test default config directory is ~/.vertice."""
        manager = HooksManager()
        assert manager._config_dir == Path.home() / ".vertice"

    def test_init_custom_config_dir(self, temp_config_dir):
        """Test custom config directory."""
        manager = HooksManager(config_dir=temp_config_dir)
        assert manager._config_dir == temp_config_dir

    def test_init_lazy_loading(self, temp_config_dir):
        """Test config is not loaded until first access."""
        manager = HooksManager(config_dir=temp_config_dir)
        assert manager._initialized is False
        assert manager._hooks_config == {}

    def test_init_config_path(self, temp_config_dir):
        """Test config file path."""
        manager = HooksManager(config_dir=temp_config_dir)
        assert manager._config_path == temp_config_dir / "hooks.json"


# =============================================================================
# LAZY INITIALIZATION TESTS
# =============================================================================


class TestLazyInitialization:
    """Tests for lazy initialization behavior."""

    def test_ensure_initialized_sets_defaults(self, hooks_manager):
        """Test lazy init sets default hook types."""
        hooks_manager._ensure_initialized()

        assert hooks_manager._initialized is True
        assert "post_write" in hooks_manager._hooks_config
        assert "post_edit" in hooks_manager._hooks_config
        assert "post_delete" in hooks_manager._hooks_config
        assert "pre_commit" in hooks_manager._hooks_config

    def test_ensure_initialized_only_once(self, hooks_manager):
        """Test initialization only happens once."""
        hooks_manager._ensure_initialized()
        hooks_manager._hooks_config["post_write"]["enabled"] = True

        # Second call should not reset
        hooks_manager._ensure_initialized()
        assert hooks_manager._hooks_config["post_write"]["enabled"] is True

    def test_default_hooks_disabled(self, hooks_manager):
        """Test all hooks start disabled by default."""
        hooks_manager._ensure_initialized()

        for hook_name, hook_config in hooks_manager._hooks_config.items():
            assert hook_config["enabled"] is False
            assert hook_config["commands"] == []

    def test_default_hooks_have_descriptions(self, hooks_manager):
        """Test all hooks have descriptions."""
        hooks_manager._ensure_initialized()

        for hook_name, hook_config in hooks_manager._hooks_config.items():
            assert "description" in hook_config
            assert len(hook_config["description"]) > 0


# =============================================================================
# LOAD CONFIG TESTS
# =============================================================================


class TestLoadConfig:
    """Tests for loading configuration from file."""

    def test_load_existing_config(self, hooks_manager_with_config):
        """Test loading pre-existing config file."""
        hooks = hooks_manager_with_config.get_hooks()

        assert hooks["post_write"]["enabled"] is True
        assert "ruff check $FILE" in hooks["post_write"]["commands"]

    def test_load_partial_config(self, temp_config_dir):
        """Test loading config with only some hooks defined."""
        config_file = temp_config_dir / "hooks.json"
        config_file.write_text(
            json.dumps({"post_write": {"enabled": True, "commands": ["echo test"]}})
        )

        manager = HooksManager(config_dir=temp_config_dir)
        hooks = manager.get_hooks()

        # post_write should be updated
        assert hooks["post_write"]["enabled"] is True
        # Other hooks should have defaults
        assert hooks["pre_commit"]["enabled"] is False

    def test_load_nonexistent_config(self, temp_config_dir):
        """Test graceful handling of missing config file."""
        manager = HooksManager(config_dir=temp_config_dir)
        hooks = manager.get_hooks()

        # Should have defaults
        assert "post_write" in hooks
        assert hooks["post_write"]["enabled"] is False

    def test_load_invalid_json(self, temp_config_dir):
        """Test graceful handling of invalid JSON."""
        config_file = temp_config_dir / "hooks.json"
        config_file.write_text("invalid json {{{")

        manager = HooksManager(config_dir=temp_config_dir)
        hooks = manager.get_hooks()

        # Should fall back to defaults
        assert "post_write" in hooks

    def test_load_ignores_unknown_hooks(self, temp_config_dir):
        """Test unknown hooks in config are ignored."""
        config_file = temp_config_dir / "hooks.json"
        config_file.write_text(
            json.dumps(
                {
                    "unknown_hook": {"enabled": True, "commands": ["evil"]},
                    "post_write": {"enabled": True, "commands": ["safe"]},
                }
            )
        )

        manager = HooksManager(config_dir=temp_config_dir)
        hooks = manager.get_hooks()

        assert "unknown_hook" not in hooks
        assert hooks["post_write"]["enabled"] is True


# =============================================================================
# SAVE CONFIG TESTS
# =============================================================================


class TestSaveConfig:
    """Tests for saving configuration to file."""

    def test_save_creates_config_file(self, temp_config_dir):
        """Test saving creates config file."""
        manager = HooksManager(config_dir=temp_config_dir)
        manager.set_hook("post_write", ["ruff check $FILE"])

        config_file = temp_config_dir / "hooks.json"
        assert config_file.exists()

    def test_save_creates_config_dir(self, tmp_path):
        """Test saving creates config directory if missing."""
        config_dir = tmp_path / "new_dir" / ".juancs"
        manager = HooksManager(config_dir=config_dir)
        manager.set_hook("post_write", ["echo test"])

        assert config_dir.exists()
        assert (config_dir / "hooks.json").exists()

    def test_save_preserves_all_hooks(self, temp_config_dir):
        """Test saving preserves all hook configurations."""
        manager = HooksManager(config_dir=temp_config_dir)
        manager.set_hook("post_write", ["cmd1"])
        manager.set_hook("pre_commit", ["cmd2"])

        # Reload and verify
        config_file = temp_config_dir / "hooks.json"
        saved = json.loads(config_file.read_text())

        assert "post_write" in saved
        assert "pre_commit" in saved
        assert "post_edit" in saved
        assert "post_delete" in saved

    def test_save_json_format(self, temp_config_dir):
        """Test saved JSON is properly formatted."""
        manager = HooksManager(config_dir=temp_config_dir)
        manager.set_hook("post_write", ["ruff check $FILE"])

        config_file = temp_config_dir / "hooks.json"
        content = config_file.read_text()

        # Should be indented (pretty printed)
        assert "\n" in content
        assert "  " in content  # 2-space indent


# =============================================================================
# GET_HOOKS TESTS
# =============================================================================


class TestGetHooks:
    """Tests for get_hooks method."""

    def test_get_hooks_returns_shallow_copy(self, hooks_manager):
        """Test get_hooks returns a shallow copy (top-level keys)."""
        hooks1 = hooks_manager.get_hooks()
        # Adding new key to copy doesn't affect original
        hooks1["new_key"] = {"test": True}

        hooks2 = hooks_manager.get_hooks()
        # New key should not exist in fresh copy
        assert "new_key" not in hooks2

    def test_get_hooks_all_types(self, hooks_manager):
        """Test get_hooks returns all hook types."""
        hooks = hooks_manager.get_hooks()

        assert len(hooks) == 4
        assert set(hooks.keys()) == {"post_write", "post_edit", "post_delete", "pre_commit"}


# =============================================================================
# GET_HOOK TESTS
# =============================================================================


class TestGetHook:
    """Tests for get_hook method."""

    def test_get_existing_hook(self, hooks_manager):
        """Test getting existing hook config."""
        hook = hooks_manager.get_hook("post_write")

        assert hook is not None
        assert "enabled" in hook
        assert "commands" in hook
        assert "description" in hook

    def test_get_nonexistent_hook(self, hooks_manager):
        """Test getting non-existent hook returns None."""
        hook = hooks_manager.get_hook("invalid_hook")
        assert hook is None


# =============================================================================
# SET_HOOK TESTS
# =============================================================================


class TestSetHook:
    """Tests for set_hook method."""

    def test_set_hook_commands(self, hooks_manager):
        """Test setting hook commands."""
        result = hooks_manager.set_hook("post_write", ["ruff check $FILE", "ruff format $FILE"])

        assert result is True
        hook = hooks_manager.get_hook("post_write")
        assert hook["commands"] == ["ruff check $FILE", "ruff format $FILE"]

    def test_set_hook_enables_automatically(self, hooks_manager):
        """Test setting commands enables hook automatically."""
        hooks_manager.set_hook("post_write", ["echo test"])

        hook = hooks_manager.get_hook("post_write")
        assert hook["enabled"] is True

    def test_set_hook_empty_commands_disables(self, hooks_manager):
        """Test setting empty commands disables hook."""
        hooks_manager.set_hook("post_write", ["echo test"])
        hooks_manager.set_hook("post_write", [])

        hook = hooks_manager.get_hook("post_write")
        assert hook["enabled"] is False
        assert hook["commands"] == []

    def test_set_hook_invalid_name(self, hooks_manager):
        """Test setting invalid hook name returns False."""
        result = hooks_manager.set_hook("invalid_hook", ["echo test"])
        assert result is False

    def test_set_hook_persists(self, temp_config_dir):
        """Test set_hook saves to config file."""
        manager = HooksManager(config_dir=temp_config_dir)
        manager.set_hook("post_write", ["test command"])

        # Create new manager and verify persistence
        manager2 = HooksManager(config_dir=temp_config_dir)
        hook = manager2.get_hook("post_write")
        assert hook["commands"] == ["test command"]


# =============================================================================
# ENABLE_HOOK TESTS
# =============================================================================


class TestEnableHook:
    """Tests for enable_hook method."""

    def test_enable_hook(self, hooks_manager):
        """Test enabling a hook."""
        result = hooks_manager.enable_hook("post_write", True)

        assert result is True
        assert hooks_manager.is_hook_enabled("post_write") is True

    def test_disable_hook(self, hooks_manager_with_config):
        """Test disabling a hook."""
        result = hooks_manager_with_config.enable_hook("post_write", False)

        assert result is True
        assert hooks_manager_with_config.is_hook_enabled("post_write") is False

    def test_enable_invalid_hook(self, hooks_manager):
        """Test enabling invalid hook returns False."""
        result = hooks_manager.enable_hook("invalid_hook", True)
        assert result is False

    def test_enable_hook_persists(self, temp_config_dir):
        """Test enable_hook saves to config file."""
        manager = HooksManager(config_dir=temp_config_dir)
        manager.enable_hook("post_write", True)

        # Create new manager and verify persistence
        manager2 = HooksManager(config_dir=temp_config_dir)
        assert manager2.is_hook_enabled("post_write") is True


# =============================================================================
# ADD_COMMAND TESTS
# =============================================================================


class TestAddCommand:
    """Tests for add_command method."""

    def test_add_command(self, hooks_manager):
        """Test adding a command to hook."""
        result = hooks_manager.add_command("post_write", "ruff check $FILE")

        assert result is True
        commands = hooks_manager.get_hook_commands("post_write")
        assert "ruff check $FILE" in commands

    def test_add_command_enables_hook(self, hooks_manager):
        """Test adding command enables hook."""
        hooks_manager.add_command("post_write", "echo test")
        assert hooks_manager.is_hook_enabled("post_write") is True

    def test_add_command_no_duplicates(self, hooks_manager):
        """Test adding duplicate command is idempotent."""
        hooks_manager.add_command("post_write", "echo test")
        hooks_manager.add_command("post_write", "echo test")

        commands = hooks_manager.get_hook_commands("post_write")
        assert commands.count("echo test") == 1

    def test_add_command_invalid_hook(self, hooks_manager):
        """Test adding to invalid hook returns False."""
        result = hooks_manager.add_command("invalid_hook", "echo test")
        assert result is False

    def test_add_multiple_commands(self, hooks_manager):
        """Test adding multiple commands."""
        hooks_manager.add_command("post_write", "cmd1")
        hooks_manager.add_command("post_write", "cmd2")
        hooks_manager.add_command("post_write", "cmd3")

        commands = hooks_manager.get_hook_commands("post_write")
        assert commands == ["cmd1", "cmd2", "cmd3"]


# =============================================================================
# REMOVE_COMMAND TESTS
# =============================================================================


class TestRemoveCommand:
    """Tests for remove_command method."""

    def test_remove_command(self, hooks_manager):
        """Test removing a command from hook."""
        hooks_manager.set_hook("post_write", ["cmd1", "cmd2", "cmd3"])
        result = hooks_manager.remove_command("post_write", "cmd2")

        assert result is True
        commands = hooks_manager.get_hook_commands("post_write")
        assert "cmd2" not in commands
        assert "cmd1" in commands
        assert "cmd3" in commands

    def test_remove_last_command_disables(self, hooks_manager):
        """Test removing last command disables hook."""
        hooks_manager.set_hook("post_write", ["only_cmd"])
        hooks_manager.remove_command("post_write", "only_cmd")

        assert hooks_manager.is_hook_enabled("post_write") is False

    def test_remove_nonexistent_command(self, hooks_manager):
        """Test removing non-existent command is safe."""
        hooks_manager.set_hook("post_write", ["cmd1"])
        result = hooks_manager.remove_command("post_write", "cmd2")

        assert result is True
        commands = hooks_manager.get_hook_commands("post_write")
        assert commands == ["cmd1"]

    def test_remove_command_invalid_hook(self, hooks_manager):
        """Test removing from invalid hook returns False."""
        result = hooks_manager.remove_command("invalid_hook", "echo test")
        assert result is False


# =============================================================================
# IS_HOOK_ENABLED TESTS
# =============================================================================


class TestIsHookEnabled:
    """Tests for is_hook_enabled method."""

    def test_disabled_by_default(self, hooks_manager):
        """Test hooks are disabled by default."""
        assert hooks_manager.is_hook_enabled("post_write") is False

    def test_enabled_after_set(self, hooks_manager):
        """Test hook is enabled after setting commands."""
        hooks_manager.set_hook("post_write", ["echo test"])
        assert hooks_manager.is_hook_enabled("post_write") is True

    def test_invalid_hook(self, hooks_manager):
        """Test invalid hook returns False."""
        assert hooks_manager.is_hook_enabled("invalid_hook") is False


# =============================================================================
# GET_HOOK_COMMANDS TESTS
# =============================================================================


class TestGetHookCommands:
    """Tests for get_hook_commands method."""

    def test_empty_by_default(self, hooks_manager):
        """Test commands are empty by default."""
        commands = hooks_manager.get_hook_commands("post_write")
        assert commands == []

    def test_returns_commands(self, hooks_manager_with_config):
        """Test returns configured commands."""
        commands = hooks_manager_with_config.get_hook_commands("post_write")
        assert "ruff check $FILE" in commands
        assert "ruff format $FILE" in commands

    def test_invalid_hook(self, hooks_manager):
        """Test invalid hook returns empty list."""
        commands = hooks_manager.get_hook_commands("invalid_hook")
        assert commands == []


# =============================================================================
# EXECUTE_HOOK TESTS
# =============================================================================


class TestExecuteHook:
    """Tests for execute_hook method."""

    @pytest.mark.asyncio
    async def test_execute_disabled_hook(self, hooks_manager):
        """Test executing disabled hook returns skipped."""
        result = await hooks_manager.execute_hook("post_write", "/path/to/file.py")

        assert result["success"] is True
        assert result["skipped"] is True

    @pytest.mark.asyncio
    async def test_execute_invalid_hook(self, hooks_manager):
        """Test executing invalid hook returns error."""
        result = await hooks_manager.execute_hook("invalid_hook", "/path/to/file.py")

        assert result["success"] is False
        assert "Unknown hook" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_hook_no_commands(self, hooks_manager):
        """Test executing hook with no commands returns skipped."""
        hooks_manager.enable_hook("post_write", True)  # Enable but no commands
        result = await hooks_manager.execute_hook("post_write", "/path/to/file.py")

        assert result["success"] is True
        assert result["skipped"] is True

    @pytest.mark.asyncio
    async def test_execute_hook_import_error(self, hooks_manager):
        """Test graceful handling when hooks module unavailable."""
        hooks_manager.set_hook("post_write", ["echo test"])

        with patch.dict("sys.modules", {"vertice_cli.hooks": None}):
            # Force reimport error
            hooks_manager._hooks_executor = None
            result = await hooks_manager.execute_hook("post_write", "/path/to/file.py")

            # Should handle import error
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_hook_with_executor(self, hooks_manager):
        """Test executing hook with mocked executor."""
        hooks_manager.set_hook("post_write", ["ruff check $FILE"])

        # Mock the executor
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.command = "ruff check /path/to/file.py"
        mock_result.stdout = "All checks passed"
        mock_result.stderr = ""
        mock_result.error = None
        mock_result.execution_time_ms = 150

        mock_executor = AsyncMock()
        mock_executor.execute_hooks = AsyncMock(return_value=[mock_result])

        hooks_manager._hooks_executor = mock_executor

        # Mock the imports
        with patch.object(hooks_manager, "_hooks_executor", mock_executor):
            with patch("vertice_tui.core.hooks_manager.HooksManager._ensure_initialized"):
                hooks_manager._initialized = True
                hooks_manager._hooks_config = {
                    "post_write": {"enabled": True, "commands": ["ruff check $FILE"]}
                }

                # Need to mock the lazy import too
                mock_hook_event = MagicMock()
                mock_hook_context = MagicMock()

                with patch.dict(
                    "sys.modules",
                    {
                        "vertice_cli.hooks": MagicMock(
                            HookEvent=mock_hook_event,
                            HookContext=mock_hook_context,
                            HookExecutor=MagicMock,
                        )
                    },
                ):
                    await hooks_manager.execute_hook("post_write", "/path/to/file.py")


# =============================================================================
# GET_STATS TESTS
# =============================================================================


class TestGetStats:
    """Tests for get_stats method."""

    def test_no_executor_stats(self, hooks_manager):
        """Test stats when no executor initialized."""
        stats = hooks_manager.get_stats()

        assert stats["total_executions"] == 0
        assert stats["no_executor"] is True

    def test_stats_with_executor(self, hooks_manager):
        """Test stats with mocked executor."""
        mock_executor = MagicMock()
        mock_executor.get_stats.return_value = {
            "total_executions": 10,
            "successful": 8,
            "failed": 2,
        }

        hooks_manager._ensure_initialized()
        hooks_manager._hooks_executor = mock_executor

        stats = hooks_manager.get_stats()

        assert stats["total_executions"] == 10
        assert stats["successful"] == 8


# =============================================================================
# HOOK_TYPES CLASS ATTRIBUTE TESTS
# =============================================================================


class TestHookTypes:
    """Tests for HOOK_TYPES class attribute."""

    def test_hook_types_defined(self):
        """Test all expected hook types are defined."""
        assert "post_write" in HooksManager.HOOK_TYPES
        assert "post_edit" in HooksManager.HOOK_TYPES
        assert "post_delete" in HooksManager.HOOK_TYPES
        assert "pre_commit" in HooksManager.HOOK_TYPES

    def test_hook_types_have_descriptions(self):
        """Test all hook types have descriptions."""
        for hook_name, description in HooksManager.HOOK_TYPES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_hook_types_immutable(self):
        """Test HOOK_TYPES is a dict (can be used as reference)."""
        assert isinstance(HooksManager.HOOK_TYPES, dict)
        assert len(HooksManager.HOOK_TYPES) == 4


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_special_characters_in_commands(self, hooks_manager):
        """Test commands with special characters."""
        commands = [
            "echo 'hello world'",
            "ruff check $FILE",
            'bash -c "test command"',
            "python -c 'import sys; print(sys.path)'",
        ]
        hooks_manager.set_hook("post_write", commands)

        saved = hooks_manager.get_hook_commands("post_write")
        assert saved == commands

    def test_unicode_in_commands(self, hooks_manager):
        """Test commands with unicode characters."""
        hooks_manager.set_hook("post_write", ["echo 'Hello 世界 🎉'"])

        commands = hooks_manager.get_hook_commands("post_write")
        assert "世界" in commands[0]

    def test_empty_string_command(self, hooks_manager):
        """Test handling of empty string command."""
        hooks_manager.set_hook("post_write", ["", "valid command"])

        commands = hooks_manager.get_hook_commands("post_write")
        assert "" in commands  # Preserved as-is

    def test_very_long_command(self, hooks_manager):
        """Test handling of very long command."""
        long_cmd = "echo " + "a" * 10000
        hooks_manager.set_hook("post_write", [long_cmd])

        commands = hooks_manager.get_hook_commands("post_write")
        assert len(commands[0]) == len(long_cmd)

    def test_many_commands(self, hooks_manager):
        """Test handling many commands."""
        commands = [f"cmd_{i}" for i in range(100)]
        hooks_manager.set_hook("post_write", commands)

        saved = hooks_manager.get_hook_commands("post_write")
        assert len(saved) == 100

    def test_concurrent_access_safe(self, temp_config_dir):
        """Test multiple managers can access same config."""
        manager1 = HooksManager(config_dir=temp_config_dir)
        manager2 = HooksManager(config_dir=temp_config_dir)

        manager1.set_hook("post_write", ["cmd1"])

        # manager2 should see the changes after re-init
        manager2._initialized = False
        manager2._hooks_config = {}
        commands = manager2.get_hook_commands("post_write")
        assert commands == ["cmd1"]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestHooksIntegration:
    """Integration tests for HooksManager."""

    def test_full_lifecycle(self, temp_config_dir):
        """Test complete lifecycle: create, configure, persist, reload."""
        # Create and configure
        manager1 = HooksManager(config_dir=temp_config_dir)
        manager1.set_hook("post_write", ["ruff check $FILE"])
        manager1.add_command("post_write", "ruff format $FILE")
        manager1.set_hook("pre_commit", ["pytest -x"])

        # Verify config
        assert manager1.is_hook_enabled("post_write") is True
        assert len(manager1.get_hook_commands("post_write")) == 2

        # Reload and verify persistence
        manager2 = HooksManager(config_dir=temp_config_dir)
        assert manager2.is_hook_enabled("post_write") is True
        commands = manager2.get_hook_commands("post_write")
        assert "ruff check $FILE" in commands
        assert "ruff format $FILE" in commands

        # Modify and verify
        manager2.remove_command("post_write", "ruff format $FILE")
        commands = manager2.get_hook_commands("post_write")
        assert "ruff format $FILE" not in commands

        # Disable and verify
        manager2.enable_hook("post_write", False)
        assert manager2.is_hook_enabled("post_write") is False

    def test_multiple_hook_types(self, hooks_manager):
        """Test configuring multiple hook types."""
        hooks_manager.set_hook("post_write", ["ruff check $FILE"])
        hooks_manager.set_hook("post_edit", ["eslint $FILE"])
        hooks_manager.set_hook("pre_commit", ["pytest -x", "mypy ."])

        hooks = hooks_manager.get_hooks()

        assert hooks["post_write"]["enabled"] is True
        assert hooks["post_edit"]["enabled"] is True
        assert hooks["pre_commit"]["enabled"] is True
        assert hooks["post_delete"]["enabled"] is False  # Not configured
