"""
Unit tests for Sandbox Executor
"""

import pytest
from app.sandbox.executor import SandboxExecutor, SandboxConfig, ExecutionResult


class TestSandboxExecutor:
    """Test suite for Sandbox Executor."""

    @pytest.fixture
    def config(self):
        """Create test sandbox config."""
        return SandboxConfig(
            allowed_read_dirs=["/tmp"],
            allowed_write_dirs=["/tmp"],
            allowed_hosts=[],
            block_network=True,
            max_execution_time=5,  # Short timeout for tests
            max_memory_mb=128,
            max_cpu_percent=25,
        )

    @pytest.fixture
    def executor(self, config):
        """Create sandbox executor for testing."""
        return SandboxExecutor(config)

    @pytest.mark.asyncio
    async def test_execute_python_simple_code(self, executor):
        """Test execution of simple Python code."""
        code = """
print("Hello, World!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""

        result = await executor.execute_python(code)

        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
        assert "2 + 2 = 4" in result.stdout
        assert result.stderr == ""
        assert result.error is None
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_python_with_error(self, executor):
        """Test execution of code that raises an exception."""
        code = """
raise ValueError("Test error")
"""

        result = await executor.execute_python(code)

        assert result.exit_code != 0
        assert "ValueError" in result.stderr or "ValueError" in result.stdout
        assert result.error is None  # Should be clean exit

    @pytest.mark.asyncio
    async def test_execute_python_timeout(self, executor):
        """Test execution timeout."""
        code = """
import time
time.sleep(10)  # Sleep longer than timeout
"""

        result = await executor.execute_python(code, timeout=1.0)

        assert result.exit_code != 0
        assert result.error == "Timeout after 1.0s"
        assert result.execution_time >= 1.0

    @pytest.mark.asyncio
    async def test_execute_python_with_working_dir(self, executor, tmp_path):
        """Test execution with custom working directory."""
        working_dir = str(tmp_path)

        code = """
import os
print(f"Current dir: {os.getcwd()}")
"""

        result = await executor.execute_python(code, working_dir=working_dir)

        assert result.exit_code == 0
        assert working_dir in result.stdout

    def test_config_validation(self):
        """Test sandbox config validation."""
        # Valid config should not raise
        config = SandboxConfig(
            allowed_read_dirs=["/tmp"],
            allowed_write_dirs=["/tmp"],
            allowed_hosts=[],
        )
        executor = SandboxExecutor(config)
        assert executor.config == config

    def test_config_validation_invalid_timeout(self):
        """Test config validation with invalid timeout."""
        config = SandboxConfig(
            allowed_read_dirs=["/tmp"],
            allowed_write_dirs=["/tmp"],
            allowed_hosts=[],
            max_execution_time=0,
        )
        with pytest.raises(ValueError, match="max_execution_time must be positive"):
            SandboxExecutor(config)

    def test_config_validation_invalid_memory(self):
        """Test config validation with invalid memory."""
        config = SandboxConfig(
            allowed_read_dirs=["/tmp"],
            allowed_write_dirs=["/tmp"],
            allowed_hosts=[],
            max_memory_mb=0,
        )
        with pytest.raises(ValueError, match="max_memory_mb must be positive"):
            SandboxExecutor(config)

    def test_config_validation_invalid_cpu(self):
        """Test config validation with invalid CPU percentage."""
        config = SandboxConfig(
            allowed_read_dirs=["/tmp"],
            allowed_write_dirs=["/tmp"],
            allowed_hosts=[],
            max_cpu_percent=150,
        )
        with pytest.raises(ValueError, match="max_cpu_percent must be between 1 and 100"):
            SandboxExecutor(config)

    @pytest.mark.asyncio
    async def test_execution_result_structure(self, executor):
        """Test that execution results have correct structure."""
        code = "print('test')"

        result = await executor.execute_python(code)

        assert isinstance(result, ExecutionResult)
        assert isinstance(result.stdout, str)
        assert isinstance(result.stderr, str)
        assert isinstance(result.exit_code, (int, type(None)))
        assert isinstance(result.execution_time, float)
        assert isinstance(result.error, (str, type(None)))
