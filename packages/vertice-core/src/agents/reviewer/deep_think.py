"""
Deep Think Security Analysis

Multi-stage validation inspired by Google CodeMender.

Pattern:
1. Static Analysis - Pattern matching, AST inspection
2. Deep Reasoning - Think through security implications
3. Critique - Self-review findings for accuracy
4. Validation - Filter false positives

Reference:
- CodeMender (DeepMind, Oct 2025)
"""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional
import logging

from .types import (
    DeepThinkResult,
    DeepThinkStage,
    ReviewFinding,
    ReviewSeverity,
    ThinkingStep,
)

if TYPE_CHECKING:
    from .types import ReviewResult

logger = logging.getLogger(__name__)


class DeepThinkMixin:
    """
    Mixin providing Deep Think security analysis.

    Add to ReviewerAgent via multiple inheritance.
    """

    SECURITY_CHECKS: List[Tuple[str, str]]

    async def deep_think_review(
        self,
        code: str,
        file_path: str,
        language: Optional[str] = None,
    ) -> "ReviewResult":
        """
        Perform Deep Think security review.

        Args:
            code: Source code to review.
            file_path: Path to the file.
            language: Programming language.

        Returns:
            ReviewResult with validated findings.
        """
        from .types import ReviewResult

        if not language:
            language = self._detect_language(file_path)  # type: ignore

        thinking_steps: List[ThinkingStep] = []
        all_findings: List[ReviewFinding] = []

        logger.info(f"[Deep Think] Stage 1: Static Analysis - {file_path}")
        static_findings, static_steps = self._stage_static_analysis(code, file_path, language)
        all_findings.extend(static_findings)
        thinking_steps.extend(static_steps)

        logger.info("[Deep Think] Stage 2: Deep Reasoning")
        reasoned_findings, reasoning_steps = self._stage_deep_reasoning(
            code, all_findings, language
        )
        thinking_steps.extend(reasoning_steps)

        logger.info("[Deep Think] Stage 3: Critique")
        critiqued_findings, critique_steps = self._stage_critique(reasoned_findings, code)
        thinking_steps.extend(critique_steps)

        logger.info("[Deep Think] Stage 4: Validation")
        validated, rejected, validation_steps = self._stage_validation(critiqued_findings)
        thinking_steps.extend(validation_steps)

        if validated:
            avg_confidence = sum(f.confidence for f in validated) / len(validated)
        else:
            avg_confidence = 1.0

        deep_think = DeepThinkResult(
            thinking_steps=thinking_steps,
            validated_findings=validated,
            rejected_findings=rejected,
            reasoning_summary=self._build_reasoning_summary(thinking_steps),
            confidence_score=avg_confidence,
        )

        score = self._calculate_score(validated)

        return ReviewResult(
            file_path=file_path,
            findings=validated,
            summary=f"Deep Think review: {len(validated)} validated, {len(rejected)} filtered",
            score=score,
            reviewed_by="reviewer:deep_think",
            deep_think=deep_think,
        )

    def _stage_static_analysis(
        self,
        code: str,
        file_path: str,
        language: str,
    ) -> Tuple[List[ReviewFinding], List[ThinkingStep]]:
        """Stage 1: Static Analysis."""
        findings: List[ReviewFinding] = []
        steps: List[ThinkingStep] = []
        lines = code.split("\n")

        for name, pattern in self.SECURITY_CHECKS:
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            for match in matches:
                line_num = code[: match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                finding = ReviewFinding(
                    id=f"static-{len(findings)}",
                    severity=ReviewSeverity.HIGH,
                    category="security",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    title=f"Potential {name}",
                    description=f"Pattern match detected: {name}",
                    code_snippet=line_content.strip(),
                    confidence=0.6,
                )
                findings.append(finding)

                steps.append(
                    ThinkingStep(
                        stage=DeepThinkStage.STATIC_ANALYSIS,
                        thought=f"Pattern '{name}' matched at line {line_num}",
                        confidence=0.6,
                        evidence=[line_content.strip()],
                    )
                )

        if language == "python":
            ast_findings, ast_steps = self._analyze_python_ast(code, file_path)
            findings.extend(ast_findings)
            steps.extend(ast_steps)

        return findings, steps

    def _analyze_python_ast(
        self,
        code: str,
        file_path: str,
    ) -> Tuple[List[ReviewFinding], List[ThinkingStep]]:
        """Analyze Python code using AST."""
        findings: List[ReviewFinding] = []
        steps: List[ThinkingStep] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            findings.append(
                ReviewFinding(
                    id="ast-syntax-error",
                    severity=ReviewSeverity.CRITICAL,
                    category="syntax",
                    file_path=file_path,
                    line_start=e.lineno or 0,
                    line_end=e.lineno or 0,
                    title="Syntax Error",
                    description=str(e.msg),
                    confidence=1.0,
                )
            )
            return findings, steps

        dangerous_calls = {
            "eval": "Arbitrary code execution",
            "exec": "Arbitrary code execution",
            "compile": "Code injection risk",
            "os.system": "Command injection",
            "subprocess.call": "Command injection with shell=True",
            "pickle.loads": "Insecure deserialization",
            "__import__": "Dynamic import risk",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in dangerous_calls:
                    finding = ReviewFinding(
                        id=f"ast-{len(findings)}",
                        severity=ReviewSeverity.HIGH,
                        category="security",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        title=f"Dangerous function: {func_name}",
                        description=dangerous_calls[func_name],
                        confidence=0.7,
                    )
                    findings.append(finding)

                    steps.append(
                        ThinkingStep(
                            stage=DeepThinkStage.STATIC_ANALYSIS,
                            thought=f"AST found dangerous call to {func_name}",
                            confidence=0.7,
                            evidence=[f"Line {node.lineno}: {func_name}()"],
                        )
                    )

        return findings, steps

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract function name from AST Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    def _stage_deep_reasoning(
        self,
        code: str,
        findings: List[ReviewFinding],
        language: str,
    ) -> Tuple[List[ReviewFinding], List[ThinkingStep]]:
        """Stage 2: Deep Reasoning."""
        steps: List[ThinkingStep] = []
        lines = code.split("\n")

        for finding in findings:
            start = max(0, finding.line_start - 3)
            end = min(len(lines), finding.line_end + 3)
            context = lines[start:end]

            is_sanitized = self._check_sanitization(context)
            is_in_comment = self._is_in_comment(lines, finding.line_start - 1, language)
            is_test_code = "test" in finding.file_path.lower()

            original_confidence = finding.confidence

            if is_sanitized:
                finding.confidence -= 0.3
                finding.reasoning = "Input appears to be sanitized"
            if is_in_comment:
                finding.confidence -= 0.5
                finding.reasoning = "Code is commented out"
            if is_test_code:
                finding.confidence -= 0.2
                finding.reasoning = "In test file - may be intentional"

            if "user input" in code.lower() or "request" in code.lower():
                if finding.category == "security":
                    finding.confidence += 0.1
                    finding.reasoning = "Handles user input - higher risk"

            finding.confidence = max(0.0, min(1.0, finding.confidence))

            steps.append(
                ThinkingStep(
                    stage=DeepThinkStage.DEEP_REASONING,
                    thought=f"Analyzed {finding.title}: confidence {original_confidence:.2f} -> {finding.confidence:.2f}",
                    confidence=finding.confidence,
                    evidence=[
                        f"Sanitized: {is_sanitized}",
                        f"Commented: {is_in_comment}",
                        f"Test code: {is_test_code}",
                    ],
                )
            )

        return findings, steps

    def _check_sanitization(self, context_lines: List[str]) -> bool:
        """Check if the code context shows sanitization."""
        sanitization_patterns = [
            r"escape\(",
            r"sanitize\(",
            r"validate\(",
            r"parameterized",
            r"prepared_statement",
            r"quote\(",
            r"html\.escape",
            r"bleach\.",
            r"markupsafe",
            r"\?",
        ]
        context = "\n".join(context_lines).lower()
        return any(re.search(p, context) for p in sanitization_patterns)

    def _is_in_comment(
        self,
        lines: List[str],
        line_idx: int,
        language: str,
    ) -> bool:
        """Check if line is in a comment."""
        if line_idx < 0 or line_idx >= len(lines):
            return False
        line = lines[line_idx].strip()

        if language == "python":
            return line.startswith("#")
        elif language in ("javascript", "typescript", "go", "rust", "java"):
            return line.startswith("//")

        return False

    def _stage_critique(
        self,
        findings: List[ReviewFinding],
        code: str,
    ) -> Tuple[List[ReviewFinding], List[ThinkingStep]]:
        """Stage 3: Critique."""
        steps: List[ThinkingStep] = []

        for finding in findings:
            critique_notes = []

            if not finding.code_snippet:
                critique_notes.append("Missing code snippet evidence")
                finding.confidence -= 0.1

            if not finding.suggestion:
                finding.suggestion = self._generate_suggestion(finding)
                critique_notes.append("Generated suggestion")

            if finding.severity == ReviewSeverity.CRITICAL:
                if finding.category not in ("security", "syntax"):
                    critique_notes.append("CRITICAL severity but not security issue")
                    finding.confidence -= 0.2

            finding.confidence = max(0.0, min(1.0, finding.confidence))

            steps.append(
                ThinkingStep(
                    stage=DeepThinkStage.CRITIQUE,
                    thought=f"Critiqued {finding.title}: {', '.join(critique_notes) or 'OK'}",
                    confidence=finding.confidence,
                    evidence=critique_notes,
                )
            )

        return findings, steps

    def _generate_suggestion(self, finding: ReviewFinding) -> str:
        """Generate a fix suggestion based on finding type."""
        suggestions = {
            "SQL injection": "Use parameterized queries or ORM methods",
            "Command injection": "Use subprocess with list args, avoid shell=True",
            "Hardcoded secrets": "Use environment variables or secret manager",  # pragma: allowlist secret
            "XSS vulnerability": "Sanitize output with html.escape() or template escaping",
            "Path traversal": "Validate and normalize paths, use pathlib",
            "eval": "Avoid eval(), use ast.literal_eval() for safe evaluation",
            "exec": "Avoid exec(), find alternative approaches",
        }

        for key, suggestion in suggestions.items():
            if key.lower() in finding.title.lower():
                return suggestion

        return "Review and fix the identified issue"

    def _stage_validation(
        self,
        findings: List[ReviewFinding],
    ) -> Tuple[List[ReviewFinding], List[ReviewFinding], List[ThinkingStep]]:
        """Stage 4: Validation - Filter false positives."""
        CONFIDENCE_THRESHOLD = 0.5

        validated: List[ReviewFinding] = []
        rejected: List[ReviewFinding] = []
        steps: List[ThinkingStep] = []

        for finding in findings:
            if finding.confidence >= CONFIDENCE_THRESHOLD:
                finding.validated = True
                validated.append(finding)
                steps.append(
                    ThinkingStep(
                        stage=DeepThinkStage.VALIDATION,
                        thought=f"VALIDATED: {finding.title} (confidence: {finding.confidence:.2f})",
                        confidence=finding.confidence,
                        evidence=[f"Above threshold: {CONFIDENCE_THRESHOLD}"],
                    )
                )
            else:
                rejected.append(finding)
                steps.append(
                    ThinkingStep(
                        stage=DeepThinkStage.VALIDATION,
                        thought=f"REJECTED (false positive): {finding.title} (confidence: {finding.confidence:.2f})",
                        confidence=finding.confidence,
                        evidence=[f"Below threshold: {CONFIDENCE_THRESHOLD}"],
                    )
                )

        return validated, rejected, steps

    def _build_reasoning_summary(self, steps: List[ThinkingStep]) -> str:
        """Build a summary of the thinking process."""
        stage_counts: Dict[str, int] = {}
        for step in steps:
            stage_counts[step.stage.value] = stage_counts.get(step.stage.value, 0) + 1

        parts = []
        for stage, count in stage_counts.items():
            parts.append(f"{stage}: {count} steps")

        return " | ".join(parts)

    def _calculate_score(self, findings: List[ReviewFinding]) -> float:
        """Calculate review score based on findings."""
        if not findings:
            return 100.0

        severity_weights = {
            ReviewSeverity.CRITICAL: 25,
            ReviewSeverity.HIGH: 15,
            ReviewSeverity.MEDIUM: 8,
            ReviewSeverity.LOW: 3,
            ReviewSeverity.INFO: 1,
        }

        deductions = sum(severity_weights.get(f.severity, 5) for f in findings)
        return max(0.0, 100.0 - deductions)
