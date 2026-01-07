"""Security scanning tool using Bandit."""

import logging

from vertice_cli.tools.base import Tool, ToolCategory, ToolResult
from vertice_cli.core.execution.sandbox import SandboxExecution

logger = logging.getLogger(__name__)


class SecurityScanTool(Tool):
    """Static security analysis using Bandit."""

    def __init__(self):
        super().__init__()
        self.category = ToolCategory.SYSTEM
        self.description = "Scan Python code for security vulnerabilities using Bandit."
        self.parameters = {
            "path": {
                "type": "string",
                "description": "File or directory to scan",
                "required": True,
            }
        }

    async def _execute_validated(self, path: str) -> ToolResult:
        sandbox = SandboxExecution(cpu_time_limit=30, memory_limit_mb=512)

        # -r: recursive
        # -q: quiet (only errors)
        # -f text: simple text output
        # -ll: log level (only HIGH/MEDIUM confidence?) No, let's keep default
        cmd = ["bandit", "-r", path, "-q", "-f", "text"]

        logger.info(f"Running security scan: {' '.join(cmd)}")

        result = await sandbox.run(cmd)

        # Bandit exit codes:
        # 0: No issues found
        # 1: Issues found
        success = result.returncode == 0
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        if not output.strip() and success:
            output = "No security issues found."

        return ToolResult(
            success=success,
            data=output.strip(),
            error=None if success else "Security issues detected",
            metadata={"returncode": result.returncode},
        )
