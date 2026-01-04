"""
planner/prompts.py: Prompt Templates and Fallback Plans.

Contains prompt templates for LLM interactions and fallback plans
when LLM generation fails.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .models import SOPStep


def build_planning_prompt(task_request: str, context: Dict[str, Any], agents: List[str]) -> str:
    """Build comprehensive planning prompt for LLM."""
    return f"""
Generate a detailed execution plan for this task:

TASK: {task_request}

CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE AGENTS: {', '.join(agents)}

REQUIREMENTS:
1. Break into atomic steps (one agent, one action)
2. Each step must have clear "definition_of_done"
3. Specify dependencies between steps
4. Mark which steps can run in parallel
5. Add checkpoints for critical transitions
6. Include rollback strategy

OUTPUT SCHEMA:
{{
  "sops": [
    {{
      "id": "step-1",
      "role": "agent_name",
      "action": "What to do",
      "objective": "Why",
      "definition_of_done": "Success criteria",
      "dependencies": [],
      "cost": 1.0,
      "priority": "high",
      "checkpoint": "validation"
    }}
  ]
}}

RESPOND WITH PURE JSON ONLY.
"""


def build_clarifying_questions_prompt(task_request: str, context: Dict[str, Any]) -> str:
    """Build prompt for generating clarifying questions."""
    return f"""Analyze this task and generate 2-3 clarifying questions that would help create a better plan.

TASK: {task_request}

CONTEXT: {json.dumps(context, indent=2) if context else "None provided"}

Generate questions in this JSON format:
{{
  "questions": [
    {{
      "question": "The question text",
      "category": "scope|approach|constraints|preferences",
      "options": ["Option 1", "Option 2", "Option 3"],
      "required": true/false
    }}
  ]
}}

Focus on:
1. SCOPE: What's included/excluded from the task?
2. APPROACH: Which implementation strategy to use?
3. CONSTRAINTS: Any limitations or requirements?
4. PREFERENCES: Code style, testing preferences, etc?

Respond with ONLY the JSON, no explanation."""


def build_exploration_prompt(task_request: str, context: Dict[str, Any]) -> str:
    """Build prompt for exploration mode analysis."""
    return f"""Analyze this task in EXPLORATION mode (read-only).

TASK: {task_request}

CONTEXT:
{json.dumps(context, indent=2)}

Provide:
1. UNDERSTANDING: What is being requested?
2. SCOPE: What files/systems are involved?
3. COMPLEXITY: How complex is this task? (Simple/Medium/Complex)
4. RISKS: What could go wrong?
5. QUESTIONS: What clarifications would help?
6. APPROACH: Suggested high-level approach

Respond in JSON format."""


def generate_basic_plan(agents: List[str]) -> List[SOPStep]:
    """
    Generate a basic fallback plan when LLM fails.

    Returns a simple three-step plan: analyze, implement, test.
    """
    return [
        SOPStep(
            id="step-1",
            role="architect",
            action="Analyze requirements and design solution",
            objective="Create technical plan",
            definition_of_done="Architecture documented",
            cost=2.0,
        ),
        SOPStep(
            id="step-2",
            role="coder",
            action="Implement the solution",
            objective="Write working code",
            definition_of_done="Code compiles and runs",
            dependencies=["step-1"],
            cost=5.0,
        ),
        SOPStep(
            id="step-3",
            role="tester",
            action="Write and run tests",
            objective="Verify correctness",
            definition_of_done="All tests pass",
            dependencies=["step-2"],
            cost=3.0,
        ),
    ]


__all__ = [
    "build_planning_prompt",
    "build_clarifying_questions_prompt",
    "build_exploration_prompt",
    "generate_basic_plan",
]
