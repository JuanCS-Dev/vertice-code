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
    """Build Claude-optimized planning prompt with structured reasoning."""
    return f"""You are Claude, an expert project planner. Create a detailed, executable plan for this software development task.

TASK REQUEST: {task_request}

CURRENT CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE SPECIALIZED AGENTS: {", ".join(agents)}

PLANNING METHODOLOGY:
Think step-by-step through the complete solution:

1. UNDERSTAND: What exactly needs to be accomplished?
2. BREAK DOWN: Divide into atomic, verifiable steps
3. SEQUENCE: Order steps with proper dependencies
4. PARALLELIZE: Identify steps that can run simultaneously
5. VALIDATE: Add checkpoints for critical transitions
6. RECOVER: Plan rollback strategies for failures

PLANNING PRINCIPLES:
- Each step = One agent + One clear action
- Every step needs measurable success criteria
- Dependencies must be explicit and minimal
- Parallel execution maximizes efficiency
- Checkpoints prevent cascading failures
- Rollback ensures safe failure recovery

EXECUTION PLAN SCHEMA:
{{
  "sops": [
    {{
      "id": "step-1",
      "role": "architect|executor|tester|etc",
      "action": "Precise action description",
      "objective": "Why this step matters",
      "definition_of_done": "Concrete success criteria",
      "dependencies": ["step-id"],
      "cost": 1.0,
      "priority": "low|medium|high",
      "checkpoint": "validation|testing|deployment"
    }}
  ]
}}

OUTPUT: Return ONLY the JSON object, no additional text or explanation."""


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
