"""Pytest execution tool for TDD loop."""

import logging

from vertice_cli.tools.base import Tool, ToolCategory, ToolResult
from vertice_cli.core.execution.sandbox import SandboxExecution

logger = logging.getLogger(__name__)


class RunPytestTool(Tool):
    """Executes pytest on a specific file or directory."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.EXECUTION
        self.description = "Execute unit tests using pytest. Returns test results."
        self.parameters = {
            "test_path": {
                "type": "string",
                "description": "Path to test file or directory",
                "required": True,
            },
            "verbose": {
                "type": "boolean",
                "description": "Enable verbose output (-v)",
                "default": True,
            },
        }

    async def _execute_validated(self, test_path: str, verbose: bool = True) -> ToolResult:
        """Run pytest."""
        cmd = ["pytest", test_path]
        if verbose:
            cmd.append("-v")

        # Use Sandbox to prevent infinite loops or memory bombs
        sandbox = SandboxExecution(
            cpu_time_limit=60,  # 60s timeout for tests
            memory_limit_mb=2048,  # 2GB RAM limit (pytest overhead)
        )

        logger.info(f"Running tests in sandbox: {' '.join(cmd)}")

        result = await sandbox.run(cmd)

        success = result.returncode == 0
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        # Truncate if too long (LLM context limit protection)
        if len(output) > 20000:
            output = output[:10000] + "\n...[OUTPUT TRUNCATED]...\n" + output[-10000:]

        error_msg = None
        if result.timed_out:
            error_msg = "Tests timed out after 60s"
            success = False
        elif not success:
            error_msg = "Tests failed (non-zero exit code)"

        return ToolResult(
            success=success,
            data=output,
            error=error_msg,
            metadata={"returncode": result.returncode, "timed_out": result.timed_out},
        )
