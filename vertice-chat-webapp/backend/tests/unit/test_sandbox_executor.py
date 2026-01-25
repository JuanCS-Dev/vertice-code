"""
Unit tests for Sandbox Executor
"""

import pytest
from app.sandbox.executor import LocalCodeExecutionDisabledError, SandboxConfig, SandboxExecutor


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
    async def test_execute_python_is_disabled(self, executor):
        """Local execution must be disabled (RCE hard-block)."""
        code = """
print("Hello, World!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        with pytest.raises(LocalCodeExecutionDisabledError):
            await executor.execute_python(code)

    @pytest.mark.asyncio
    async def test_execute_python_with_error_is_disabled(self, executor):
        """Even erroring code must not run locally."""
        code = """
raise ValueError("Test error")
"""
        with pytest.raises(LocalCodeExecutionDisabledError):
            await executor.execute_python(code)

    @pytest.mark.asyncio
    async def test_execute_python_timeout_is_disabled(self, executor):
        """Timeouts are irrelevant if execution is disabled."""
        code = """
import time
time.sleep(10)  # Sleep longer than timeout
"""
        with pytest.raises(LocalCodeExecutionDisabledError):
            await executor.execute_python(code, timeout=1.0)

    @pytest.mark.asyncio
    async def test_execute_python_with_working_dir_is_disabled(self, executor, tmp_path):
        """Working dir should not matter when disabled."""
        working_dir = str(tmp_path)

        code = """
import os
print(f"Current dir: {os.getcwd()}")
"""
        with pytest.raises(LocalCodeExecutionDisabledError):
            await executor.execute_python(code, working_dir=working_dir)

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
    async def test_execution_result_structure_is_disabled(self, executor):
        """No ExecutionResult is produced when disabled; we raise instead."""
        code = "print('test')"

        with pytest.raises(LocalCodeExecutionDisabledError):
            await executor.execute_python(code)
