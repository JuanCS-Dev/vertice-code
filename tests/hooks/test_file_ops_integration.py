"""Test hooks integration with file operations tools.

Tests that WriteFileTool and EditFileTool properly execute hooks
after successful operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import logging
import asyncio

from vertice_cli.tools.file_ops import WriteFileTool, EditFileTool
from vertice_cli.hooks import HookExecutor
from vertice_cli.config.schema import QwenConfig, HooksConfig


class TestFileOpsHooksIntegration:
    """Test file operations tools execute hooks correctly."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def mock_config_with_hooks(self):
        """Create mock config with hooks."""
        config = QwenConfig()
        config.hooks = HooksConfig(
            post_write=["echo 'post_write hook executed'"],
            post_edit=["echo 'post_edit hook executed'"]
        )

        mock_loader = Mock()
        mock_loader.config = config
        return mock_loader

    @pytest.fixture
    def mock_config_no_hooks(self):
        """Create mock config without hooks."""
        config = QwenConfig()
        config.hooks = HooksConfig()

        mock_loader = Mock()
        mock_loader.config = config
        return mock_loader

    @pytest.fixture
    def executor(self):
        """Create hook executor."""
        return HookExecutor(enable_sandbox=False, timeout_seconds=5)

    # ========== WRITE TOOL INTEGRATION ==========

    @pytest.mark.asyncio
    async def test_write_tool_executes_post_write_hook(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test WriteFileTool executes post_write hooks."""
        caplog.set_level(logging.INFO)
        tool = WriteFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "test.py"

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(path=str(test_file), content="x = 1")
            assert result.success
            assert test_file.exists()

            await asyncio.sleep(0.1)

            # Check logs for hook execution
            assert "Executing post_write hook" in caplog.text
            assert "post_write hook executed" in caplog.text

        finally:
            os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_write_tool_no_hooks_configured(
        self, temp_dir, mock_config_no_hooks, caplog
    ):
        """Test WriteFileTool when no hooks configured."""
        caplog.set_level(logging.INFO)
        tool = WriteFileTool(config_loader=mock_config_no_hooks)
        test_file = temp_dir / "test.py"

        result = await tool.execute(path=str(test_file), content="x = 1")

        assert result.success
        assert test_file.exists()

        # No hooks should have been executed
        assert "Executing post_write hook" not in caplog.text

    @pytest.mark.asyncio
    async def test_write_tool_hook_failure_doesnt_block(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test WriteFileTool continues even if hook fails."""
        caplog.set_level(logging.INFO)
        mock_config_with_hooks.config.hooks.post_write = [
            "python -c 'import sys; sys.exit(1)'"
        ]
        tool = WriteFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "test.py"

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(path=str(test_file), content="x = 1")
            assert result.success
            assert test_file.exists()

            # Check logs for hook failure
            assert "Executing post_write hook" in caplog.text
            assert "failed with exit code 1" in caplog.text

        finally:
            os.chdir(old_cwd)

    # ========== EDIT TOOL INTEGRATION ==========

    @pytest.mark.asyncio
    async def test_edit_tool_executes_post_edit_hook(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test EditFileTool executes post_edit hooks."""
        caplog.set_level(logging.INFO)
        tool = EditFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "test.py"
        test_file.write_text("x = 1")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(
                path=str(test_file),
                edits=[{"search": "x = 1", "replace": "x = 2"}],
            )
            assert result.success
            assert test_file.read_text() == "x = 2"

            await asyncio.sleep(0.1)

            # Check logs for hook execution
            assert "Executing post_edit hook" in caplog.text
            assert "post_edit hook executed" in caplog.text

        finally:
            os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_edit_tool_no_hooks_configured(
        self, temp_dir, mock_config_no_hooks, caplog
    ):
        """Test EditFileTool when no hooks configured."""
        caplog.set_level(logging.INFO)
        tool = EditFileTool(config_loader=mock_config_no_hooks)
        test_file = temp_dir / "test.py"
        test_file.write_text("x = 1")

        result = await tool.execute(
            path=str(test_file),
            edits=[{"search": "x = 1", "replace": "x = 2"}],
        )

        assert result.success
        assert "Executing post_edit hook" not in caplog.text

    # ========== HOOK EXECUTOR DISABLED ==========

    @pytest.mark.asyncio
    async def test_write_tool_no_config_loader(self, temp_dir, caplog):
        """Test WriteFileTool works without a config_loader."""
        caplog.set_level(logging.INFO)
        tool = WriteFileTool(config_loader=None)
        test_file = temp_dir / "test.py"
        result = await tool.execute(path=str(test_file), content="x = 1")
        assert result.success
        assert test_file.exists()
        assert "Executing post_write hook" not in caplog.text

    @pytest.mark.asyncio
    async def test_edit_tool_no_config_loader(self, temp_dir, caplog):
        """Test EditFileTool works without a config_loader."""
        caplog.set_level(logging.INFO)
        tool = EditFileTool(config_loader=None)
        test_file = temp_dir / "test.py"
        test_file.write_text("x = 1")
        result = await tool.execute(
            path=str(test_file),
            edits=[{"search": "x = 1", "replace": "x = 2"}],
        )
        assert result.success
        assert "Executing post_edit hook" not in caplog.text

    # ========== MULTIPLE HOOKS ==========

    @pytest.mark.asyncio
    async def test_write_tool_multiple_hooks(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test WriteFileTool executes multiple hooks."""
        caplog.set_level(logging.INFO)
        mock_config_with_hooks.config.hooks.post_write = [
            "echo 'hook1'",
            "echo 'hook2'",
            "echo 'hook3'",
        ]
        tool = WriteFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "test.py"

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(path=str(test_file), content="x = 1")
            assert result.success

            await asyncio.sleep(0.1)

            # All 3 hooks should have been logged
            assert caplog.text.count("Executing post_write hook") == 3
            assert "hook1" in caplog.text
            assert "hook2" in caplog.text
            assert "hook3" in caplog.text
        finally:
            os.chdir(old_cwd)

    # ========== VARIABLE SUBSTITUTION ==========

    @pytest.mark.asyncio
    async def test_hooks_use_correct_variables(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test hooks receive correct variable substitution."""
        caplog.set_level(logging.INFO)
        mock_config_with_hooks.config.hooks.post_write = ["echo {file_path}"]
        tool = WriteFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "myfile.py"

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(path=str(test_file), content="x = 1")
            assert result.success

            await asyncio.sleep(0.1)

            assert str(test_file) in caplog.text

        finally:
            os.chdir(old_cwd)

    # ========== ERROR HANDLING ==========

    @pytest.mark.asyncio
    async def test_write_tool_hook_exception_handled(
        self, temp_dir, mock_config_with_hooks, caplog
    ):
        """Test WriteFileTool handles hook exceptions gracefully."""
        caplog.set_level(logging.INFO)
        mock_config_with_hooks.config.hooks.post_write = ["nonexistent_command_xyz"]
        tool = WriteFileTool(config_loader=mock_config_with_hooks)
        test_file = temp_dir / "test.py"

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = await tool.execute(path=str(test_file), content="x = 1")
            assert result.success
            assert test_file.exists()

            await asyncio.sleep(0.1)

            assert "error" in caplog.text.lower()
            assert "nonexistent_command_xyz" in caplog.text

        finally:
            os.chdir(old_cwd)
