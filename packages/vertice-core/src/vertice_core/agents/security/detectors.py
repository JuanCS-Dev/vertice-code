"""
Security Detectors - Vulnerability detection methods.

Pattern matching and AST analysis for security vulnerabilities.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

from .types import SeverityLevel, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)


class EvalExecDetector(ast.NodeVisitor):
    """AST-based detector for eval/exec usage."""

    def __init__(self) -> None:
        """Initialize detector with empty findings."""
        self.findings: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Check for eval/exec calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                self.findings.append((node.lineno, f"{node.func.id}() usage detected"))
        self.generic_visit(node)

    @classmethod
    def detect(cls, code: str) -> List[Tuple[int, str]]:
        """Detect eval/exec usage in code.

        Args:
            code: Python source code to analyze.

        Returns:
            List of (line_number, description) tuples.
        """
        try:
            tree = ast.parse(code)
            detector = cls()
            detector.visit(tree)
            return detector.findings
        except SyntaxError:
            return []


def detect_sql_injection(
    file: Path,
    lines: List[str],
    content: str,
    patterns: Dict[str, re.Pattern],
) -> List[Vulnerability]:
    """Detect SQL injection vulnerabilities.

    Covers:
    - Direct f-string in execute()
    - F-string SQL assigned to variable then executed
    - String concatenation in SQL queries
    - Variable interpolation in SQL strings

    Args:
        file: Path to the file being scanned.
        lines: List of lines in the file.
        content: Full file content.
        patterns: Compiled regex patterns.

    Returns:
        List of detected vulnerabilities.
    """
    vulns = []

    for i, line in enumerate(lines, 1):
        matched = False
        description = ""

        if patterns["sql_inject"].search(line):
            matched = True
            description = "SQL query uses %s formatting, vulnerable to injection"
        elif patterns["sql_format"].search(line):
            matched = True
            description = "SQL query uses .format(), vulnerable to injection"
        elif patterns["sql_fstring"].search(line):
            matched = True
            description = "SQL query uses f-string in execute(), vulnerable to injection"
        elif patterns["sql_fstring_var"].search(line):
            matched = True
            description = "SQL query built with f-string, vulnerable to injection"
        elif patterns["sql_concat"].search(line):
            matched = True
            description = "SQL query built with string concatenation, vulnerable to injection"
        elif patterns["sql_interpolation"].search(line):
            matched = True
            description = "SQL query contains variable interpolation, vulnerable to injection"

        if matched:
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.SQL_INJECTION,
                    severity=SeverityLevel.CRITICAL,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description=description,
                    remediation="Use parameterized queries (e.g., cursor.execute(query, (param,)))",
                    cwe_id="CWE-89",
                )
            )

    return vulns


def detect_command_injection(
    file: Path,
    lines: List[str],
    content: str,
    patterns: Dict[str, re.Pattern],
) -> List[Vulnerability]:
    """Detect command injection vulnerabilities.

    Args:
        file: Path to the file being scanned.
        lines: List of lines in the file.
        content: Full file content.
        patterns: Compiled regex patterns.

    Returns:
        List of detected vulnerabilities.
    """
    vulns = []

    for i, line in enumerate(lines, 1):
        # Check for shell=True in subprocess
        if patterns["shell_true"].search(line):
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.COMMAND_INJECTION,
                    severity=SeverityLevel.CRITICAL,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="subprocess call with shell=True allows command injection",
                    remediation="Use shell=False and pass command as list: ['cmd', 'arg1']",
                    cwe_id="CWE-78",
                )
            )

        # Check for os.system usage
        if "os.system" in line:
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.COMMAND_INJECTION,
                    severity=SeverityLevel.HIGH,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="os.system() is unsafe, allows command injection",
                    remediation="Use subprocess.run() with shell=False",
                    cwe_id="CWE-78",
                )
            )

    return vulns


def detect_path_traversal(
    file: Path,
    lines: List[str],
    patterns: Dict[str, re.Pattern],
) -> List[Vulnerability]:
    """Detect path traversal vulnerabilities.

    Args:
        file: Path to the file being scanned.
        lines: List of lines in the file.
        patterns: Compiled regex patterns.

    Returns:
        List of detected vulnerabilities.
    """
    vulns = []

    for i, line in enumerate(lines, 1):
        if patterns["path_traversal"].search(line) and ".." in line:
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.PATH_TRAVERSAL,
                    severity=SeverityLevel.MEDIUM,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="Path concatenation may allow directory traversal",
                    remediation="Use Path().resolve() and validate against base directory",
                    cwe_id="CWE-22",
                )
            )

    return vulns


def detect_weak_crypto(
    file: Path,
    lines: List[str],
    patterns: Dict[str, re.Pattern],
) -> List[Vulnerability]:
    """Detect usage of weak cryptographic algorithms.

    Args:
        file: Path to the file being scanned.
        lines: List of lines in the file.
        patterns: Compiled regex patterns.

    Returns:
        List of detected vulnerabilities.
    """
    vulns = []

    for i, line in enumerate(lines, 1):
        if patterns["md5"].search(line) or patterns["sha1"].search(line):
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.WEAK_CRYPTO,
                    severity=SeverityLevel.MEDIUM,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="MD5/SHA1 are cryptographically broken",
                    remediation="Use SHA-256 or SHA-3 for hashing",
                    cwe_id="CWE-327",
                )
            )

    return vulns


def detect_unsafe_deserialization(
    file: Path,
    lines: List[str],
    patterns: Dict[str, re.Pattern],
) -> List[Vulnerability]:
    """Detect unsafe deserialization (pickle, yaml.load).

    Args:
        file: Path to the file being scanned.
        lines: List of lines in the file.
        patterns: Compiled regex patterns.

    Returns:
        List of detected vulnerabilities.
    """
    vulns = []

    for i, line in enumerate(lines, 1):
        if patterns["pickle"].search(line):
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.UNSAFE_DESERIALIZATION,
                    severity=SeverityLevel.HIGH,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="pickle.load() can execute arbitrary code",
                    remediation="Use json.load() or validate pickle source",
                    cwe_id="CWE-502",
                )
            )

        if patterns["yaml_unsafe"].search(line) and "SafeLoader" not in line:
            vulns.append(
                Vulnerability(
                    type=VulnerabilityType.UNSAFE_DESERIALIZATION,
                    severity=SeverityLevel.HIGH,
                    file=str(file),
                    line=i,
                    code_snippet=line.strip(),
                    description="yaml.load() without SafeLoader can execute code",
                    remediation="Use yaml.safe_load() instead",
                    cwe_id="CWE-502",
                )
            )

    return vulns


def detect_eval_usage(file: Path, content: str) -> List[Vulnerability]:
    """Detect eval/exec usage via EvalExecDetector.

    Args:
        file: Path to the file being scanned.
        content: Full file content.

    Returns:
        List of detected vulnerabilities.
    """
    detections = EvalExecDetector.detect(content)
    vulns = []
    for lineno, description in detections:
        vulns.append(
            Vulnerability(
                type=VulnerabilityType.EVAL_USAGE,
                severity=SeverityLevel.CRITICAL,
                file=str(file),
                line=lineno,
                code_snippet=description,
                description=description,
                remediation="Avoid eval/exec. Use ast.literal_eval() for safe evaluation",
                cwe_id="CWE-95",
            )
        )
    return vulns


__all__ = [
    "EvalExecDetector",
    "detect_sql_injection",
    "detect_command_injection",
    "detect_path_traversal",
    "detect_weak_crypto",
    "detect_unsafe_deserialization",
    "detect_eval_usage",
]
