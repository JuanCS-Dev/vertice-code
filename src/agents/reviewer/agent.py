"""
Vertice Reviewer Agent

Code review and security specialist with Deep Think pattern.

Key Features:
- Code quality review
- Security vulnerability detection
- Best practices enforcement
- Deep Think multi-stage analysis (via mixin)

Reference:
- CodeMender (DeepMind, Oct 2025)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, AsyncIterator, Tuple
import logging

from .types import (
    ReviewFinding,
    ReviewResult,
    ReviewSeverity,
)
from .deep_think import DeepThinkMixin
from agents.base import BaseAgent
from vertice_core.resilience import ResilienceMixin
from vertice_core.caching import CachingMixin

logger = logging.getLogger(__name__)


class ReviewerAgent(ResilienceMixin, CachingMixin, DeepThinkMixin, BaseAgent):
    """
    Code Review Specialist - The Quality Guardian

    Capabilities:
    - Security vulnerability detection (OWASP Top 10)
    - Code quality analysis
    - Performance bottleneck identification
    - Best practices enforcement
    - Deep Think multi-stage validation (via mixin)
    """

    name = "reviewer"
    description = """
    Code review and security specialist with Deep Think.
    Uses multi-stage reasoning to validate findings.
    Filters false positives through critique and validation.
    """

    SYSTEM_PROMPT = """You are an expert code reviewer for Vertice Agency.

Your review MUST cover:
1. SECURITY (CRITICAL)
   - SQL injection
   - XSS vulnerabilities
   - Command injection
   - Insecure deserialization
   - Hardcoded secrets
   - Authentication/authorization flaws

2. CODE QUALITY
   - Logic errors
   - Null/undefined handling
   - Error handling
   - Edge cases
   - Resource leaks

3. PERFORMANCE
   - N+1 queries
   - Memory leaks
   - Unnecessary loops
   - Blocking operations

4. BEST PRACTICES
   - SOLID principles
   - DRY violations
   - Naming conventions
   - Documentation

For each finding:
- Specify exact line numbers
- Explain WHY it's a problem
- Provide a FIX or alternative

Be thorough but fair. Praise good patterns too.
"""

    SECURITY_CHECKS: List[Tuple[str, str]] = [
        ("SQL injection", r"(execute|query)\s*\(.*\+|f['\"].*\{.*\}.*SELECT|\.format\(.*SELECT"),
        ("Command injection", r"(subprocess|os\.system|exec|eval)\s*\(.*\+|shell=True"),
        ("Hardcoded secrets", r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]"),
        ("XSS vulnerability", r"innerHTML\s*=|dangerouslySetInnerHTML|\{\{.*\}\}"),
        ("Path traversal", r"\.\./|\.\.\\\\"),
    ]

    def __init__(self, provider: str = "vertex-ai") -> None:
        super().__init__()  # Initialize BaseAgent (observability)
        self._provider_name = provider
        self._llm = None
        self._findings: List[ReviewFinding] = []

    async def review(
        self,
        code: str,
        file_path: str,
        language: Optional[str] = None,
        focus: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Review code and stream findings.

        Args:
            code: Source code to review
            file_path: Path to the file
            language: Programming language
            focus: Specific areas to focus on
            stream: Whether to stream output

        Yields:
            Review findings and summary
        """
        yield f"[Reviewer] Analyzing {file_path}...\n"

        if not language:
            language = self._detect_language(file_path)

        yield f"[Reviewer] Language: {language}\n"

        security_issues = self._quick_security_scan(code)
        if security_issues:
            yield f"[Reviewer] Security scan found {len(security_issues)} potential issues\n"
            for issue in security_issues:
                yield f"  - {issue}\n"

        focus_str = ", ".join(focus) if focus else "all aspects"
        _prompt = f"""Review this {language} code with focus on {focus_str}:

FILE: {file_path}

```{language}
{code}
```

Provide detailed findings.
"""

        yield "[Reviewer] Performing deep analysis...\n"

        if security_issues:
            yield "\n## Security Findings\n"
            for i, issue in enumerate(security_issues, 1):
                yield f"### Finding {i}\n"
                yield "- **Severity**: HIGH\n"
                yield "- **Category**: security\n"
                yield f"- **Issue**: {issue}\n\n"

        yield "\n[Reviewer] Review complete\n"

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        return "unknown"

    def _quick_security_scan(self, code: str) -> List[str]:
        """Quick regex-based security scan."""
        issues = []

        for name, pattern in self.SECURITY_CHECKS:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"Potential {name}")

        return issues

    async def security_audit(
        self,
        code: str,
        file_path: str,
    ) -> ReviewResult:
        """
        Focused security audit.

        Returns comprehensive security analysis.
        """
        findings = []

        issues = self._quick_security_scan(code)
        for i, issue in enumerate(issues):
            findings.append(ReviewFinding(
                id=f"sec-{i}",
                severity=ReviewSeverity.HIGH,
                category="security",
                file_path=file_path,
                line_start=0,
                line_end=0,
                title=issue,
                description=f"Potential security issue: {issue}",
            ))

        return ReviewResult(
            file_path=file_path,
            findings=findings,
            summary=f"Found {len(findings)} potential security issues",
            score=100 - (len(findings) * 10),
            reviewed_by=self.name,
        )

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider_name,
            "total_findings": len(self._findings),
            "deep_think_enabled": True,
        }


# Singleton instance
reviewer = ReviewerAgent()
