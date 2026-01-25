"""
SecurityAgent - The Penetration Tester - Offensive Security Specialist.

This agent performs security audits on codebases, detecting vulnerabilities,
exposed secrets, and dependency risks. It follows OWASP guidelines and
provides actionable remediation advice.

Capabilities:
    - Vulnerability scanning (SQL, XSS, Command Injection, eval)
    - Secret detection (API keys, AWS credentials, tokens)
    - Dependency auditing (CVE scanning via pip-audit)
    - OWASP Top 10 compliance scoring

Architecture:
    SecurityAgent extends BaseAgent with READ_ONLY + BASH_EXEC capabilities.
    It uses pattern matching, AST analysis, and external tools (pip-audit).

Philosophy (Boris Cherny):
    "Security is not a feature. It's a non-negotiable."
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from ..base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)
from .types import Vulnerability
from .patterns import compile_security_patterns
from .detectors import (
    detect_sql_injection,
    detect_command_injection,
    detect_path_traversal,
    detect_weak_crypto,
    detect_unsafe_deserialization,
    detect_eval_usage,
)
from .secrets import detect_secrets
from .dependencies import check_dependencies
from .report import (
    calculate_owasp_score,
    generate_report,
    vuln_to_dict,
    secret_to_dict,
    dep_to_dict,
)

logger = logging.getLogger(__name__)


class SecurityAgent(BaseAgent):
    """The Penetration Tester - Offensive Security Specialist.

    This agent scans code for security vulnerabilities, exposed secrets,
    and vulnerable dependencies. It provides OWASP-compliant scoring and
    actionable remediation advice.

    Capabilities:
        - READ_ONLY: Read files and directory structures
        - BASH_EXEC: Run security tools (pip-audit, bandit)

    Type Safety:
        All vulnerability data is strongly typed via dataclasses.
        Pattern matching uses compiled regex for performance.
    """

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Any,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SecurityAgent with scanning patterns.

        Args:
            llm_client: LLM client for reasoning.
            mcp_client: MCP client for tool access.
            config: Optional configuration.
        """
        super().__init__(
            role=AgentRole.SECURITY,
            capabilities=[AgentCapability.READ_ONLY, AgentCapability.BASH_EXEC],
            llm_client=llm_client,
            mcp_client=mcp_client,
        )

        # Compile regex patterns for performance
        self._patterns = compile_security_patterns()

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute security audit on specified files or directory.

        Args:
            task: Contains context with root_dir or metadata with target_file.

        Returns:
            AgentResponse with vulnerabilities, secrets, dependencies, and OWASP score.
        """
        try:
            # Determine scan scope
            target_path = Path(task.context.get("root_dir", "."))
            if "target_file" in task.metadata:
                target_path = Path(task.metadata["target_file"])

            # Phase 1: Scan for vulnerabilities
            vulnerabilities = await self._scan_vulnerabilities(target_path)

            # Phase 2: Detect secrets
            secrets = await detect_secrets(target_path, self._patterns)

            # Phase 3: Check dependencies (if requirements.txt exists)
            dep_vulns = await check_dependencies(target_path)

            # Phase 4: Calculate OWASP score
            owasp_score = calculate_owasp_score(vulnerabilities, secrets, dep_vulns)

            # Compile report
            report = generate_report(vulnerabilities, secrets, dep_vulns, owasp_score)

            return AgentResponse(
                success=True,
                data={
                    "report": report,
                    "vulnerabilities": [vuln_to_dict(v) for v in vulnerabilities],
                    "secrets": [secret_to_dict(s) for s in secrets],
                    "dependencies": [dep_to_dict(d) for d in dep_vulns],
                    "owasp_score": owasp_score,
                },
                reasoning=f"Security scan complete: {len(vulnerabilities)} vulnerabilities, "
                f"{len(secrets)} secrets, {len(dep_vulns)} vulnerable dependencies. "
                f"OWASP Score: {owasp_score}/100",
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                reasoning=f"Security scan failed: {str(e)}",
                error=str(e),
            )

    async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Stream security scan with progressive updates.

        Yields status updates as each security phase completes.

        Args:
            task: Task with target to scan

        Yields:
            StreamingChunk dicts with scan progress
        """
        from vertice_core.agents.protocol import StreamingChunk, StreamingChunkType

        try:
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="🔒 SecurityAgent starting scan..."
            ).to_dict()

            target_path = Path(task.context.get("root_dir", "."))
            if "target_file" in task.metadata:
                target_path = Path(task.metadata["target_file"])

            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data=f"📁 Target: {target_path}"
            ).to_dict()

            # Phase 1: Vulnerabilities
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="🔍 Phase 1: Scanning for vulnerabilities..."
            ).to_dict()

            vulnerabilities = await self._scan_vulnerabilities(target_path)
            yield StreamingChunk(
                type=StreamingChunkType.THINKING,
                data=f"Found {len(vulnerabilities)} vulnerabilities\n",
            ).to_dict()

            # Phase 2: Secrets
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="🔐 Phase 2: Detecting secrets..."
            ).to_dict()

            secrets = await detect_secrets(target_path, self._patterns)
            yield StreamingChunk(
                type=StreamingChunkType.THINKING, data=f"Found {len(secrets)} exposed secrets\n"
            ).to_dict()

            # Phase 3: Dependencies
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="📦 Phase 3: Checking dependencies..."
            ).to_dict()

            dep_vulns = await check_dependencies(target_path)
            yield StreamingChunk(
                type=StreamingChunkType.THINKING,
                data=f"Found {len(dep_vulns)} vulnerable dependencies\n",
            ).to_dict()

            # Phase 4: OWASP Score
            owasp_score = calculate_owasp_score(vulnerabilities, secrets, dep_vulns)

            verdict_emoji = "✅" if owasp_score >= 80 else "⚠️" if owasp_score >= 50 else "❌"
            yield StreamingChunk(
                type=StreamingChunkType.VERDICT,
                data=f"\n\n{verdict_emoji} **OWASP Score: {owasp_score}/100**",
            ).to_dict()

            yield StreamingChunk(
                type=StreamingChunkType.RESULT,
                data={
                    "owasp_score": owasp_score,
                    "vulnerabilities": len(vulnerabilities),
                    "secrets": len(secrets),
                    "dep_vulns": len(dep_vulns),
                },
            ).to_dict()

        except Exception as e:
            yield StreamingChunk(
                type=StreamingChunkType.ERROR, data=f"Security scan failed: {str(e)}"
            ).to_dict()

    async def _scan_vulnerabilities(self, target: Path) -> List[Vulnerability]:
        """Scan for code vulnerabilities using pattern matching and AST analysis.

        Args:
            target: File or directory to scan.

        Returns:
            List of detected vulnerabilities.
        """
        vulnerabilities: List[Vulnerability] = []

        if target.is_file():
            files = [target]
        else:
            files = list(target.rglob("*.py"))

        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Pattern-based detection
                vulnerabilities.extend(detect_sql_injection(file, lines, content, self._patterns))
                vulnerabilities.extend(
                    detect_command_injection(file, lines, content, self._patterns)
                )
                vulnerabilities.extend(detect_path_traversal(file, lines, self._patterns))
                vulnerabilities.extend(detect_weak_crypto(file, lines, self._patterns))
                vulnerabilities.extend(detect_unsafe_deserialization(file, lines, self._patterns))

                # AST-based detection (eval/exec)
                vulnerabilities.extend(detect_eval_usage(file, content))

            except (OSError, UnicodeDecodeError) as e:
                logger.debug(f"Skipping {file} in vulnerability scan: {e}")
                continue

        return vulnerabilities


__all__ = ["SecurityAgent"]
