"""
Temperature Configuration - Standardized Temperature Settings.

Based on Gemini CLI 2026 temperature patterns:
- Analysis tasks: 0.1-0.2 (deterministic)
- Generation tasks: 0.3-0.5 (creative but focused)
- Exploration tasks: 0.2-0.3 (balanced)

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations

from typing import Optional


# =============================================================================
# TEMPERATURE CONFIGURATION
# =============================================================================

TEMPERATURE_CONFIG = {
    # Analysis tasks (very deterministic - avoid hallucination)
    "reviewer": 0.1,
    "reviewer_analysis": 0.1,
    "testing_analysis": 0.1,
    "security_audit": 0.1,
    "security": 0.1,
    "codebase_investigator": 0.1,
    "architect_analysis": 0.1,
    # Generation tasks (creative but focused)
    "coder": 0.3,
    "coder_generation": 0.3,
    "documentation": 0.4,
    "documentation_generation": 0.4,
    "testing_generation": 0.3,
    "refactorer": 0.3,
    # Exploration tasks (balanced)
    "explorer": 0.2,
    "explorer_search": 0.2,
    "planner": 0.3,
    "planner_planning": 0.3,
    "architect": 0.2,
    "architect_feasibility": 0.2,
    # Orchestration (balanced)
    "orchestrator": 0.3,
    "prometheus": 0.3,
    "executor": 0.3,
    "curriculum": 0.4,
    # DevOps (deterministic for safety)
    "devops": 0.1,
    "devops_deployment": 0.1,
    "devops_incident": 0.2,
    # Performance (deterministic for accuracy)
    "performance": 0.1,
    "performance_analysis": 0.1,
    # Data (deterministic)
    "data": 0.2,
    "data_analysis": 0.1,
    # Default fallback
    "default": 0.3,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_temperature(
    agent_type: str, task_type: Optional[str] = None, default: float = 0.3
) -> float:
    """Get appropriate temperature for agent/task combination.

    Args:
        agent_type: Type of agent (e.g., "reviewer", "coder")
        task_type: Optional task type for more specific lookup
        default: Default temperature if not found

    Returns:
        Temperature value between 0.0 and 1.0

    Examples:
        >>> get_temperature("reviewer")
        0.1
        >>> get_temperature("coder", "generation")
        0.3
        >>> get_temperature("unknown")
        0.3
    """
    # Try specific agent_task combination first
    if task_type:
        key = f"{agent_type}_{task_type}"
        if key in TEMPERATURE_CONFIG:
            return TEMPERATURE_CONFIG[key]

    # Try agent type alone
    if agent_type in TEMPERATURE_CONFIG:
        return TEMPERATURE_CONFIG[agent_type]

    # Fall back to default
    return TEMPERATURE_CONFIG.get("default", default)


def get_analysis_temperature() -> float:
    """Get standard temperature for analysis tasks."""
    return 0.1


def get_generation_temperature() -> float:
    """Get standard temperature for generation tasks."""
    return 0.3


def get_exploration_temperature() -> float:
    """Get standard temperature for exploration tasks."""
    return 0.2


def is_deterministic_task(agent_type: str) -> bool:
    """Check if a task should use deterministic (low) temperature.

    Args:
        agent_type: Type of agent

    Returns:
        True if task should be deterministic (temp <= 0.2)
    """
    temp = get_temperature(agent_type)
    return temp <= 0.2


def get_temperature_for_llm_call(
    agent_type: str, task_type: Optional[str] = None, override: Optional[float] = None
) -> float:
    """Get temperature for an LLM call with optional override.

    This is the main function to use before making LLM calls.

    Args:
        agent_type: Type of agent making the call
        task_type: Optional specific task type
        override: Optional explicit override (takes precedence)

    Returns:
        Temperature to use for the LLM call
    """
    if override is not None:
        return max(0.0, min(1.0, override))

    return get_temperature(agent_type, task_type)


# =============================================================================
# TEMPERATURE RECOMMENDATIONS
# =============================================================================

TEMPERATURE_GUIDANCE = """
Temperature Selection Guidelines (Gemini CLI 2026 Pattern):

LOW (0.0 - 0.2): Use for tasks requiring accuracy and consistency
- Code analysis and review
- Security audits
- Performance analysis
- DevOps operations
- Bug detection

MEDIUM (0.2 - 0.4): Use for balanced tasks
- Code generation
- Documentation
- Test generation
- Planning
- Architecture decisions

HIGH (0.4 - 0.7): Use for creative tasks
- Brainstorming
- Alternative solutions
- Exploratory analysis
- Curriculum generation

AVOID (> 0.7): Generally too unpredictable for code tasks
- May generate inconsistent code
- Higher hallucination risk
- Reduced reliability
"""


__all__ = [
    "TEMPERATURE_CONFIG",
    "get_temperature",
    "get_analysis_temperature",
    "get_generation_temperature",
    "get_exploration_temperature",
    "is_deterministic_task",
    "get_temperature_for_llm_call",
    "TEMPERATURE_GUIDANCE",
]
