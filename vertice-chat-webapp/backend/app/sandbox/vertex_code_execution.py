"""
Vertex AI managed code execution (Code Interpreter).

This module provides a *remote* execution path using Google's managed sandbox via
the Google Gen AI SDK on Vertex AI. No local `exec()`/`eval()` is ever performed.

Only Gemini 3 models are supported here (policy + stability):
- gemini-3-pro-preview
- gemini-3-flash-preview
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from app.sandbox.executor import ExecutionResult


@dataclass(frozen=True)
class VertexCodeExecutionConfig:
    project: str
    location: str
    model: str


def _extract_code_execution_output(response: object) -> tuple[str, Optional[str], Optional[int]]:
    """
    Best-effort extractor for Google Gen AI SDK responses.

    Returns: (stdout, error, exit_code)
    """
    # Fast path: some responses expose a `.text` convenience property.
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text, None, 0

    stdout_parts: list[str] = []
    error: Optional[str] = None
    exit_code: Optional[int] = None

    candidates = getattr(response, "candidates", None)
    if not candidates:
        return "", "No candidates returned by model.", 1

    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if not parts:
            continue

        for part in parts:
            code_exec = getattr(part, "code_execution_result", None)
            if code_exec is not None:
                outcome = getattr(code_exec, "outcome", None)
                output = getattr(code_exec, "output", None)
                if isinstance(output, str) and output:
                    stdout_parts.append(output)

                # Map outcome to exit_code in a stable way.
                outcome_str = str(outcome) if outcome is not None else ""
                if "OUTCOME_OK" in outcome_str:
                    exit_code = 0
                else:
                    exit_code = 1
                    if error is None:
                        error = f"Code execution outcome: {outcome_str or 'UNKNOWN'}"

    if stdout_parts and exit_code is None:
        exit_code = 0

    if not stdout_parts and error is None:
        error = "Model did not return code execution output."
        exit_code = 1

    return "".join(stdout_parts), error, exit_code


async def execute_python_via_vertex_code_execution(
    *,
    code: str,
    timeout: float,
    config: VertexCodeExecutionConfig,
) -> ExecutionResult:
    """
    Execute Python code via Vertex AI managed sandbox (Code Interpreter).

    Security posture:
    - Never executes code locally.
    - If SDK/config/auth is missing, fails closed with an error in the result.
    """
    start = time.perf_counter()

    try:
        from google import genai
        from google.genai import types
    except Exception as e:  # pragma: no cover
        elapsed = time.perf_counter() - start
        return ExecutionResult(
            stdout="",
            stderr="",
            exit_code=1,
            execution_time=elapsed,
            error=f"google-genai SDK not available: {e}",
        )

    prompt = (
        "Execute the following Python code in the managed sandbox and return only the runtime output.\n\n"
        "```python\n"
        f"{code}\n"
        "```\n"
    )

    tools = [types.Tool(code_execution=types.ToolCodeExecution())]
    gen_config = types.GenerateContentConfig(
        tools=tools,
        temperature=0.0,
        max_output_tokens=2048,
    )

    def _call():
        client = genai.Client(vertexai=True, project=config.project, location=config.location)
        return client.models.generate_content(
            model=config.model, contents=prompt, config=gen_config
        )

    try:
        response = await asyncio.wait_for(asyncio.to_thread(_call), timeout=timeout)
        stdout, error, exit_code = _extract_code_execution_output(response)
        elapsed = time.perf_counter() - start
        return ExecutionResult(
            stdout=stdout,
            stderr="",
            exit_code=exit_code,
            execution_time=elapsed,
            error=error,
        )
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start
        return ExecutionResult(
            stdout="",
            stderr="",
            exit_code=1,
            execution_time=elapsed,
            error=f"Remote execution timed out after {timeout:.2f}s",
        )
    except Exception as e:
        elapsed = time.perf_counter() - start
        return ExecutionResult(
            stdout="",
            stderr="",
            exit_code=1,
            execution_time=elapsed,
            error=f"Remote execution failed: {e}",
        )
