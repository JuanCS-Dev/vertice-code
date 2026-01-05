"""Type checking tool using mypy."""

import logging
from typing import Any, Dict

from vertice_cli.tools.base import Tool, ToolCategory, ToolResult
from vertice_cli.core.execution.sandbox import SandboxExecution

logger = logging.getLogger(__name__)


class TypeCheckTool(Tool):
    """Static type checker using Mypy."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.EXECUTION
        self.description = "Check Python code for type errors using Mypy."
        self.parameters = {
            "path": {
                "type": "string",
                "description": "File or directory to check",
                "required": True,
            }
        }

    async def _execute_validated(self, path: str) -> ToolResult:
        sandbox = SandboxExecution(cpu_time_limit=60, memory_limit_mb=1024)

        # Run mypy with sensible defaults for incremental adoption
        cmd = [
            "mypy",
            path,
            "--ignore-missing-imports",
            "--no-error-summary",
            "--show-column-numbers",
            "--no-color-output",
        ]

        logger.info(f"Running type check: {' '.join(cmd)}")

        result = await sandbox.run(cmd)

        # Mypy returns 0 on success, non-zero on issues
        success = result.returncode == 0
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        if len(output) > 10000:
            output = output[:5000] + "\n...[TRUNCATED]...\n" + output[-5000:]

        return ToolResult(
            success=success,
            data=output.strip(),
            error=None if success else "Type errors detected",
            metadata={"returncode": result.returncode},
        )
