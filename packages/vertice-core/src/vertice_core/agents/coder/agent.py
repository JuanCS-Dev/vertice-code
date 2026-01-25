"""Vertice Coder Agent - Code generation via Vertex AI Gemini 3 Pro."""

from __future__ import annotations

import ast
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, AsyncIterator
import logging

from .types import CodeGenerationRequest, EvaluationResult, GeneratedCode
from .darwin_godel import DarwinGodelMixin
from agents.base import BaseAgent

logger = logging.getLogger(__name__)


class CoderAgent(DarwinGodelMixin, BaseAgent):
    """Code generation agent using Vertex AI Gemini 3 Pro."""

    name = "coder"
    description = "Code generation agent using Gemini 3 Pro."

    LANGUAGES = {
        "python": ".py",
        "typescript": ".ts",
        "javascript": ".js",
        "rust": ".rs",
        "go": ".go",
    }

    SYSTEM_PROMPT = """You are an expert code generation agent.
Your code MUST be production-ready, well-documented, and follow best practices.
Include type hints. Handle edge cases. Return clean, runnable code."""

    def __init__(self) -> None:
        super().__init__()  # Initialize BaseAgent (observability)
        self._llm = None
        self._provider = None

    async def _get_llm(self):
        """Get LLM provider directly (simplified for reliability)."""
        if self._llm is None:
            from vertice_core.providers.vertex_ai import VertexAIProvider

            self._llm = VertexAIProvider(project="vertice-ai", location="global", model_name="pro")
        return self._llm

    async def generate(
        self, request: CodeGenerationRequest, stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Generate code using Vertex AI Gemini 3 Pro directly.
        Simplified flow without router overhead.
        """
        provider = await self._get_llm()

        prompt = f"""
TASK: {request.description}
LANGUAGE: {request.language}
STYLE: {request.style}

MISSION: 
Provide the corrected, production-ready code.
Use a clean Python code block.
Include all necessary imports and type hints.
"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # Direct call to VertexAIProvider.stream_chat
        async for chunk in provider.stream_chat(messages, max_tokens=8192, temperature=0.7):
            yield chunk

    async def refactor(
        self, code: str, instructions: str, language: str = "python"
    ) -> AsyncIterator[str]:
        """Refactor existing code based on instructions."""
        llm = await self._get_llm()

        prompt = f"""
Original Code ({language}):
```{{language}}
{code}
```

Refactoring Instructions: {instructions}

Provide the refactored code with explanations.
"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        async for chunk in llm.stream_chat(messages, max_tokens=4096):
            yield chunk

    async def complete(
        self, code_prefix: str, language: str = "python", max_tokens: int = 500
    ) -> str:
        """Complete partial code."""
        llm = await self._get_llm()

        prompt = f"""Complete this {language} code:

```{language}
{code_prefix}
```

Continue naturally. Only output the completion, not the original code.
"""

        messages = [
            {"role": "system", "content": "Complete code naturally. Output only the completion."},
            {"role": "user", "content": prompt},
        ]

        result = await llm.generate(messages, max_tokens=max_tokens)
        return result

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider or "not_initialized",
            "languages": list(self.LANGUAGES.keys()),
            "self_evaluation": True,
        }

    # =========================================================================
    # SELF-EVALUATION METHODS
    # =========================================================================

    def evaluate_code(
        self,
        code: str,
        language: str = "python",
    ) -> EvaluationResult:
        """
        Evaluate generated code for correctness and quality.

        Args:
            code: The generated code to evaluate.
            language: Programming language.

        Returns:
            EvaluationResult with scores and issues.
        """
        issues: List[str] = []
        suggestions: List[str] = []

        valid_syntax = self._check_syntax(code, language, issues)
        lint_score = 0.0
        if valid_syntax:
            lint_score = self._run_lint(code, language, issues, suggestions)

        quality_score = self._calculate_quality(code, language, valid_syntax, lint_score)

        return EvaluationResult(
            valid_syntax=valid_syntax,
            lint_score=lint_score,
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
        )

    def _check_syntax(
        self,
        code: str,
        language: str,
        issues: List[str],
    ) -> bool:
        """Check code syntax validity."""
        if language == "python":
            try:
                ast.parse(code)
                return True
            except SyntaxError as e:
                issues.append(f"Syntax error at line {e.lineno}: {e.msg}")
                return False
        else:
            return bool(code.strip())

    def _run_lint(
        self,
        code: str,
        language: str,
        issues: List[str],
        suggestions: List[str],
    ) -> float:
        """Run linter and return score (0.0-1.0)."""
        if language != "python":
            return 0.8

        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                ["ruff", "check", temp_path, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = result.stdout + result.stderr
            if not output.strip():
                return 1.0

            lint_issues = [line for line in output.split("\n") if line.strip()]
            for issue in lint_issues[:5]:
                issues.append(f"Lint: {issue}")

            score = max(0.0, 1.0 - len(lint_issues) * 0.1)
            return score

        except FileNotFoundError:
            suggestions.append("Install ruff for better linting: pip install ruff")
            return 0.7
        except subprocess.TimeoutExpired:
            issues.append("Lint check timed out")
            return 0.5
        except Exception as e:
            logger.warning(f"Lint check failed: {e}")
            return 0.6
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink()
                except (FileNotFoundError, PermissionError, OSError):
                    pass

    def _calculate_quality(
        self,
        code: str,
        language: str,
        valid_syntax: bool,
        lint_score: float,
    ) -> float:
        """Calculate overall quality score."""
        if not valid_syntax:
            return 0.0

        score = lint_score * 0.5
        lines = code.split("\n")
        non_empty = [line for line in lines if line.strip()]

        if language == "python":
            has_docs = '"""' in code or "'''" in code or "#" in code
        else:
            has_docs = "//" in code or "/*" in code
        if has_docs:
            score += 0.15

        if 10 <= len(non_empty) <= 500:
            score += 0.15

        if language == "python" and (":" in code or "->" in code):
            score += 0.1

        anti_patterns = ["TODO", "FIXME", "XXX", "pass  #", "...  #"]
        if not any(p in code for p in anti_patterns):
            score += 0.1

        return min(1.0, score)

    async def generate_with_evaluation(
        self,
        request: CodeGenerationRequest,
        max_corrections: int = 2,
    ) -> GeneratedCode:
        """
        Generate code with self-evaluation and correction.

        Args:
            request: Code generation request.
            max_corrections: Maximum correction attempts.

        Returns:
            GeneratedCode with evaluation results.
        """
        code_chunks: List[str] = []

        async for chunk in self.generate(request, stream=False):
            code_chunks.append(chunk)

        code = "".join(code_chunks)
        code = self._extract_code_block(code, request.language)

        evaluation = self.evaluate_code(code, request.language)
        attempts = 0

        while not evaluation.passed and attempts < max_corrections:
            attempts += 1
            logger.info(f"Self-correction attempt {attempts}/{max_corrections}")

            code = await self._correct_code(code, request.language, evaluation.issues)
            evaluation = self.evaluate_code(code, request.language)

        return GeneratedCode(
            code=code,
            language=request.language,
            explanation=f"Generated with {attempts} corrections",
            evaluation=evaluation,
            correction_attempts=attempts,
        )

    def _extract_code_block(self, text: str, language: str) -> str:
        """Extract code from markdown code block."""
        pattern = r"```{{language}}?\n?(.*?)" "`"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    async def _correct_code(
        self,
        code: str,
        language: str,
        issues: List[str],
    ) -> str:
        """Attempt to correct code based on issues."""
        llm = await self._get_llm()

        issues_str = "\n".join(f"- {i}" for i in issues[:5])

        prompt = f"""Fix these issues in the code:

Issues:
{issues_str}

Original Code:
```{{language}}
{code}
```

Return ONLY the corrected code, no explanations.
"""

        messages = [
            {"role": "system", "content": "Fix code issues. Return only corrected code."},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await llm.generate(messages, max_tokens=4096)
            return self._extract_code_block(result, language)
        except Exception as e:
            logger.error(f"Correction failed: {e}")
            return code


# Singleton instance
coder = CoderAgent()
