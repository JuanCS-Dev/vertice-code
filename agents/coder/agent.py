"""
Vertice Coder Agent

Fast code generation specialist using free-tier LLMs.
Optimized for bulk operations and rapid prototyping.

Primary Model: Groq (Llama 3.3 70B) - 14,400 req/day FREE
Fallback: Cerebras, Vertex AI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, AsyncIterator
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeGenerationRequest:
    """Request for code generation."""
    description: str
    language: str = "python"
    style: str = "clean"  # clean, verbose, minimal
    include_tests: bool = False
    include_docs: bool = True


@dataclass
class GeneratedCode:
    """Generated code result."""
    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    tokens_used: int = 0


class CoderAgent:
    """
    Code Generation Specialist

    Capabilities:
    - Rapid code generation (using Groq for speed)
    - Multi-language support
    - Test generation
    - Code completion
    - Refactoring suggestions

    Optimized for:
    - High throughput (bulk operations)
    - Low latency (first token < 500ms)
    - Cost efficiency (free tier priority)
    """

    name = "coder"
    description = """
    Fast code generation agent. Specializes in
    clean, production-ready code with minimal latency.
    Uses Groq (Llama 3.3 70B) for ultra-fast inference.
    """

    # Supported languages and their templates
    LANGUAGES = {
        "python": {
            "extension": ".py",
            "comment": "#",
            "docstring": '"""',
        },
        "typescript": {
            "extension": ".ts",
            "comment": "//",
            "docstring": "/**",
        },
        "javascript": {
            "extension": ".js",
            "comment": "//",
            "docstring": "/**",
        },
        "rust": {
            "extension": ".rs",
            "comment": "//",
            "docstring": "///",
        },
        "go": {
            "extension": ".go",
            "comment": "//",
            "docstring": "//",
        },
    }

    SYSTEM_PROMPT = """You are an expert code generation agent.

Your code MUST be:
- Production-ready and error-free
- Well-documented with clear comments
- Following language best practices
- Secure (no vulnerabilities)
- Efficient (no unnecessary complexity)

NEVER:
- Use placeholder implementations
- Skip error handling
- Hardcode secrets
- Use deprecated APIs

ALWAYS:
- Include type hints (Python) or types (TS)
- Handle edge cases
- Return clean, runnable code
"""

    def __init__(self):
        self._llm = None
        self._provider = None

    async def _get_llm(self):
        """Get LLM client with fallback chain."""
        if self._llm is None:
            from providers import get_router
            router = get_router()
            self._llm = router
        return self._llm

    async def generate(
        self,
        request: CodeGenerationRequest,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Generate code based on request.

        Uses Groq for maximum speed.
        Falls back to Cerebras or Vertex AI if needed.
        """
        llm = await self._get_llm()

        prompt = f"""
Language: {request.language}
Style: {request.style}
Include Tests: {request.include_tests}
Include Docs: {request.include_docs}

Task: {request.description}

Generate clean, production-ready code.
"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            async for chunk in llm.stream_chat(
                messages,
                complexity="simple",  # Use fast provider
                max_tokens=4096,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            yield f"[Error] Code generation failed: {e}"

    async def refactor(
        self,
        code: str,
        instructions: str,
        language: str = "python"
    ) -> AsyncIterator[str]:
        """Refactor existing code based on instructions."""
        llm = await self._get_llm()

        prompt = f"""
Original Code ({language}):
```{language}
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
        self,
        code_prefix: str,
        language: str = "python",
        max_tokens: int = 500
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
        }


# Singleton instance
coder = CoderAgent()
