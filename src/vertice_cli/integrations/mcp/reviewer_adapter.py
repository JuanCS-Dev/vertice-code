"""
Reviewer MCP Adapter - Expose ReviewerAgent via MCP protocol.

Tools:
- reviewer_review: Review code for issues
- reviewer_security_audit: Focused security audit
- reviewer_get_status: Get agent status
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewerMCPAdapter:
    """Adapter to expose ReviewerAgent tools via MCP.
    
    REUSES existing `reviewer` singleton from `agents.reviewer.agent`.
    Does NOT create a new agent instance.
    """

    def __init__(self):
        self._mcp_tools: Dict[str, Any] = {}
        self._reviewer = None

    def _get_reviewer(self):
        """Lazy import to avoid circular dependencies."""
        if self._reviewer is None:
            from agents.reviewer.agent import reviewer
            self._reviewer = reviewer
        return self._reviewer

    def register_all(self, mcp_server) -> None:
        """Register all Reviewer tools as MCP tools."""

        @mcp_server.tool(name="reviewer_review")
        async def reviewer_review(
            code: str,
            file_path: str,
            language: Optional[str] = None,
            focus: Optional[str] = None,
        ) -> dict:
            """Review code for issues, security, and quality."""
            try:
                reviewer = self._get_reviewer()
                focus_list = focus.split(",") if focus else None
                
                result_chunks = []
                async for chunk in reviewer.review(
                    code=code,
                    file_path=file_path,
                    language=language,
                    focus=focus_list,
                    stream=True,
                ):
                    result_chunks.append(chunk)
                
                return {
                    "success": True,
                    "tool": "reviewer_review",
                    "review": "".join(result_chunks),
                    "file_path": file_path,
                }
            except Exception as e:
                logger.error(f"reviewer_review error: {e}")
                return {"success": False, "tool": "reviewer_review", "error": str(e)}

        @mcp_server.tool(name="reviewer_security_audit")
        async def reviewer_security_audit(
            code: str,
            file_path: str,
        ) -> dict:
            """Perform focused security audit on code."""
            try:
                reviewer = self._get_reviewer()
                result = await reviewer.security_audit(code, file_path)
                
                return {
                    "success": True,
                    "tool": "reviewer_security_audit",
                    "file_path": result.file_path,
                    "score": result.score,
                    "findings_count": len(result.findings),
                    "findings": [
                        {
                            "id": f.id,
                            "severity": f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
                            "title": f.title,
                            "description": f.description,
                        }
                        for f in result.findings
                    ],
                    "summary": result.summary,
                }
            except Exception as e:
                logger.error(f"reviewer_security_audit error: {e}")
                return {"success": False, "tool": "reviewer_security_audit", "error": str(e)}

        @mcp_server.tool(name="reviewer_get_status")
        async def reviewer_get_status() -> dict:
            """Get Reviewer agent status."""
            try:
                reviewer = self._get_reviewer()
                status = reviewer.get_status()
                
                return {
                    "success": True,
                    "tool": "reviewer_get_status",
                    "status": status,
                }
            except Exception as e:
                logger.error(f"reviewer_get_status error: {e}")
                return {"success": False, "tool": "reviewer_get_status", "error": str(e)}

        # Register all tools
        self._mcp_tools.update({
            "reviewer_review": reviewer_review,
            "reviewer_security_audit": reviewer_security_audit,
            "reviewer_get_status": reviewer_get_status,
        })

        logger.info(f"Registered {len(self._mcp_tools)} Reviewer MCP tools")

    def list_registered_tools(self) -> list:
        """List all registered MCP tools."""
        return list(self._mcp_tools.keys())


__all__ = ["ReviewerMCPAdapter"]
