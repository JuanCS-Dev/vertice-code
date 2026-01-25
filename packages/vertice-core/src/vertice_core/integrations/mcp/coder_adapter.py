"""
Coder MCP Adapter - Expose CoderAgent via MCP protocol.

Tools:
- coder_generate: Generate code from request
- coder_refactor: Refactor existing code
- coder_complete: Complete partial code
- coder_evaluate: Evaluate code quality
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CoderMCPAdapter:
    """Adapter to expose CoderAgent tools via MCP.

    REUSES existing `coder` singleton from `agents.coder.agent`.
    Does NOT create a new agent instance.
    """

    def __init__(self):
        self._mcp_tools: Dict[str, Any] = {}
        self._coder = None

    def _get_coder(self):
        """Lazy import to avoid circular dependencies."""
        if self._coder is None:
            from agents.coder.agent import coder

            self._coder = coder
        return self._coder

    def register_all(self, mcp_server) -> None:
        """Register all Coder tools as MCP tools."""

        @mcp_server.tool(name="coder_generate")
        async def coder_generate(
            task: str,
            language: str = "python",
            requirements: str = "",
        ) -> dict:
            """Generate code based on task description."""
            try:
                from agents.coder.types import CodeGenerationRequest

                coder = self._get_coder()
                request = CodeGenerationRequest(
                    task=task,
                    language=language,
                    requirements=requirements.split(",") if requirements else [],
                )

                result_chunks = []
                async for chunk in coder.generate(request, stream=True):
                    result_chunks.append(chunk)

                return {
                    "success": True,
                    "tool": "coder_generate",
                    "code": "".join(result_chunks),
                    "language": language,
                }
            except Exception as e:
                logger.error(f"coder_generate error: {e}")
                return {"success": False, "tool": "coder_generate", "error": str(e)}

        @mcp_server.tool(name="coder_refactor")
        async def coder_refactor(
            code: str,
            instructions: str,
            language: str = "python",
        ) -> dict:
            """Refactor existing code based on instructions."""
            try:
                coder = self._get_coder()
                result = await coder.refactor(code, instructions, language)

                return {
                    "success": True,
                    "tool": "coder_refactor",
                    "refactored_code": result,
                    "language": language,
                }
            except Exception as e:
                logger.error(f"coder_refactor error: {e}")
                return {"success": False, "tool": "coder_refactor", "error": str(e)}

        @mcp_server.tool(name="coder_complete")
        async def coder_complete(
            code_prefix: str,
            language: str = "python",
            max_tokens: int = 500,
        ) -> dict:
            """Complete partial code."""
            try:
                coder = self._get_coder()
                result = await coder.complete(code_prefix, language, max_tokens)

                return {
                    "success": True,
                    "tool": "coder_complete",
                    "completion": result,
                    "language": language,
                }
            except Exception as e:
                logger.error(f"coder_complete error: {e}")
                return {"success": False, "tool": "coder_complete", "error": str(e)}

        @mcp_server.tool(name="coder_evaluate")
        async def coder_evaluate(
            code: str,
            language: str = "python",
        ) -> dict:
            """Evaluate code for correctness and quality."""
            try:
                coder = self._get_coder()
                result = await coder.evaluate_code(code, language)

                return {
                    "success": True,
                    "tool": "coder_evaluate",
                    "valid_syntax": result.valid_syntax,
                    "lint_score": result.lint_score,
                    "quality_score": result.quality_score,
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                }
            except Exception as e:
                logger.error(f"coder_evaluate error: {e}")
                return {"success": False, "tool": "coder_evaluate", "error": str(e)}

        # Register all tools
        self._mcp_tools.update(
            {
                "coder_generate": coder_generate,
                "coder_refactor": coder_refactor,
                "coder_complete": coder_complete,
                "coder_evaluate": coder_evaluate,
            }
        )

        logger.info(f"Registered {len(self._mcp_tools)} Coder MCP tools")

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())


__all__ = ["CoderMCPAdapter"]
