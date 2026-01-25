"""
Planner Streaming - Streaming Execution for PlannerAgent.

This module provides streaming execution capabilities:
- execute_streaming: Stream plan generation with status updates
- run: Backwards compatible alias

Claude Code Style: Generate internally, format, then stream formatted output.
"""

import asyncio
import uuid
from typing import Any, AsyncIterator, Dict, Optional, TYPE_CHECKING

from ..base import AgentResponse, AgentTask
from .formatting import format_plan_as_markdown
from .utils import robust_json_parse

if TYPE_CHECKING:
    from .agent import PlannerAgent


async def execute_streaming(
    agent: "PlannerAgent", task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """
    Streaming execution for PlannerAgent.

    Claude Code Style: Generates plan internally, then streams formatted markdown.
    Does NOT stream raw JSON tokens to UI.

    Args:
        agent: The PlannerAgent instance
        task: The task to execute

    Yields:
        Dict with format {"type": "status"|"thinking"|"result", "data": ...}
    """
    trace_id = getattr(task, "trace_id", str(uuid.uuid4()))

    try:
        # PHASE 1: Initial Status
        yield {"type": "status", "data": "📋 Loading project context..."}

        cwd = task.context.get("cwd", ".") if task.context else "."
        await asyncio.sleep(0.05)

        # PHASE 2: Build Prompt
        yield {"type": "status", "data": "🎯 Generating plan..."}

        # Detect language and add instruction
        lang_instruction = _get_language_instruction(task.request)

        prompt = _build_streaming_prompt(task.request, cwd, lang_instruction)

        # PHASE 3: Generate LLM Response (internal - NOT streamed to UI)
        response_buffer = []
        token_count = 0

        async for token in agent.llm_client.stream(
            prompt=prompt,
            system_prompt=(
                agent._get_system_prompt() if hasattr(agent, "_get_system_prompt") else None
            ),
            max_tokens=4096,
            temperature=0.3,
        ):
            response_buffer.append(token)
            token_count += 1
            # Show progress indicator every 50 tokens (Claude Code style)
            if token_count % 50 == 0:
                yield {"type": "status", "data": f"🎯 Generating plan... ({token_count} tokens)"}

        llm_response = "".join(response_buffer)

        # PHASE 4: Process and Format
        yield {"type": "status", "data": "⚙️ Processing plan..."}

        plan = robust_json_parse(llm_response) or {"raw_response": llm_response}

        # PHASE 5: Generate Formatted Markdown (Claude Code style)
        yield {"type": "status", "data": "📝 Formatting plan..."}

        formatted_markdown = format_plan_as_markdown(plan, task.request)

        # PHASE 6: Stream the formatted markdown LINE BY LINE
        lines = formatted_markdown.split("\n")
        for line in lines:
            yield {"type": "thinking", "data": line + "\n"}
            await asyncio.sleep(0.005)  # 5ms delay for smooth visual

        # PHASE 7: Return Result
        yield {"type": "status", "data": "✅ Plan complete!"}

        yield {
            "type": "result",
            "data": AgentResponse(
                success=True,
                data={
                    "plan": plan,
                    "sops": plan.get("sops", []) if isinstance(plan, dict) else [],
                },
                reasoning=f"Generated plan with {len(plan.get('sops', []) if isinstance(plan, dict) else [])} steps",
            ),
        }

    except Exception as e:
        agent.logger.exception(f"[{trace_id}] Planning error: {e}")
        yield {"type": "error", "data": {"error": str(e), "trace_id": trace_id}}


def _get_language_instruction(request: str) -> Optional[str]:
    """Get language-specific instruction for prompts."""
    try:
        from vertice_core import LanguageDetector

        return LanguageDetector.get_prompt_instruction(request)
    except ImportError:
        return None


def _build_streaming_prompt(request: str, cwd: str, lang_instruction: Optional[str]) -> str:
    """Build prompt for streaming plan generation."""
    return f"""Create an execution plan for the following request:

REQUEST: {request}

CONTEXT:
- Working Directory: {cwd}

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON object - no markdown, no code blocks, no explanations
2. DO NOT include any tool calls, function calls, or command syntax
3. DO NOT write [TOOL_CALL:...], mkdir, write_file, or any execution commands
4. Each step should be a high-level DESCRIPTION of what to do, not HOW to do it
5. The "action" field should be human-readable text, NOT code or commands

Respond with this EXACT JSON format:

{{
  "goal": "Brief description of the goal",
  "strategy_overview": "High-level approach in plain text",
  "sops": [
    {{
      "id": "step-1",
      "action": "Human-readable description of what to do",
      "role": "executor",
      "confidence_score": 0.8,
      "definition_of_done": "How to verify completion"
    }}
  ],
  "risk_assessment": "LOW|MEDIUM|HIGH",
  "rollback_strategy": "How to undo if needed",
  "estimated_duration": "Time estimate"
}}

Include 3-7 concrete steps. Each "action" must be plain text describing WHAT to do, not code.

{f'IMPORTANT: {lang_instruction}' if lang_instruction else ''}"""


async def run_streaming(agent: "PlannerAgent", task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
    """Alias for execute_streaming for backwards compatibility."""
    async for update in execute_streaming(agent, task):
        yield update


__all__ = ["execute_streaming", "run_streaming"]
