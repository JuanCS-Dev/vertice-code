"""
Plan Mode Tools for MCP Server
Planning mode state management and tools

This module provides planning mode functionality with state persistence
and structured task exploration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# =============================================================================
# PLAN MODE STATE MANAGEMENT
# =============================================================================


@dataclass
class PlanState:
    """Current state of plan mode."""

    active: bool = False
    plan_file: Optional[Path] = None
    started_at: Optional[datetime] = None
    task_description: str = ""
    exploration_notes: List[str] = field(default_factory=list)
    files_explored: List[str] = field(default_factory=list)
    decisions_made: List[Dict[str, str]] = field(default_factory=list)
    questions_pending: List[str] = field(default_factory=list)
    plan_content: str = ""
    approved: bool = False


# Global plan state
_plan_state = PlanState()


def get_plan_state() -> PlanState:
    """Get the current plan state."""
    return _plan_state


def reset_plan_state() -> None:
    """Reset plan state for testing."""
    global _plan_state
    _plan_state = PlanState()


# =============================================================================
# PLAN MODE TOOLS
# =============================================================================


def enter_plan_mode(
    task_description: str = "", plan_file: str = ".qwen/plans/current_plan.md"
) -> ToolResult:
    """Enter planning mode for complex tasks."""
    global _plan_state

    if _plan_state.active:
        return ToolResult(
            success=False,
            error="Already in plan mode. Use exit_plan_mode to exit first.",
        )

    try:
        plan_path = Path(plan_file)
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        _plan_state = PlanState(
            active=True,
            plan_file=plan_path,
            started_at=datetime.now(),
            task_description=task_description or "Complex task planning",
        )

        initial_content = f"""# Plan Mode Active

Started: {_plan_state.started_at}
Task: {_plan_state.task_description}

## Current Status
- **Mode**: Planning/Exploration
- **Files Explored**: 0
- **Decisions Made**: 0
- **Questions Pending**: 0

## Exploration Notes
<!-- Add exploration findings here -->

## Decisions Made
<!-- Document architectural decisions here -->

## Questions for User
<!-- List questions that need clarification -->

## Implementation Plan
<!-- Outline the implementation approach -->

---
*Use exit_plan_mode when ready for approval*
"""

        plan_path.write_text(initial_content, encoding="utf-8")

        return ToolResult(
            success=True,
            data={
                "status": "plan_mode_active",
                "plan_file": str(plan_path),
                "message": "Entered plan mode. Explore codebase and use add_plan_note to document findings.",
            },
            metadata={
                "started_at": _plan_state.started_at.isoformat(),
                "task_description": _plan_state.task_description,
            },
        )

    except Exception as e:
        logger.error(f"EnterPlanMode error: {e}")
        return ToolResult(success=False, error=str(e))


def exit_plan_mode() -> ToolResult:
    """Exit planning mode and present plan for approval."""
    global _plan_state

    if not _plan_state.active:
        return ToolResult(
            success=False,
            error="Not currently in plan mode. Use enter_plan_mode first.",
        )

    try:
        if _plan_state.plan_file and _plan_state.plan_file.exists():
            plan_content = _plan_state.plan_file.read_text(encoding="utf-8")
        else:
            plan_content = "Plan file not found"

        duration = datetime.now() - (_plan_state.started_at or datetime.now())

        result_data = {
            "status": "plan_mode_exited",
            "plan_content": plan_content,
            "duration_seconds": duration.total_seconds(),
            "files_explored": len(_plan_state.files_explored),
            "decisions_made": len(_plan_state.decisions_made),
            "questions_pending": len(_plan_state.questions_pending),
            "approved": _plan_state.approved,
        }

        reset_plan_state()

        return ToolResult(
            success=True,
            data=result_data,
            metadata={
                "plan_file": str(_plan_state.plan_file) if _plan_state.plan_file else None,
                "duration": str(duration),
            },
        )

    except Exception as e:
        logger.error(f"ExitPlanMode error: {e}")
        return ToolResult(success=False, error=str(e))


def add_plan_note(note: str, category: str = "exploration") -> ToolResult:
    """Add a note to the current plan."""
    global _plan_state

    if not _plan_state.active:
        return ToolResult(
            success=False,
            error="Not in plan mode. Use enter_plan_mode first.",
        )

    try:
        valid_categories = ["exploration", "decision", "question", "file"]
        if category not in valid_categories:
            category = "exploration"

        timestamp = datetime.now().isoformat()

        if category == "exploration":
            _plan_state.exploration_notes.append(f"{timestamp}: {note}")
        elif category == "decision":
            _plan_state.decisions_made.append({"timestamp": timestamp, "decision": note})
        elif category == "question":
            _plan_state.questions_pending.append(note)
        elif category == "file":
            _plan_state.files_explored.append(note)

        if _plan_state.plan_file:
            try:
                content = _plan_state.plan_file.read_text(encoding="utf-8")
                if "## Exploration Notes" in content:
                    content = content.replace(
                        "## Exploration Notes",
                        f"## Exploration Notes\n- {timestamp}: {note} ({category})",
                        1,
                    )
                    _plan_state.plan_file.write_text(content, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not update plan file: {e}")

        return ToolResult(
            success=True,
            data={
                "note_added": note,
                "category": category,
                "total_notes": len(_plan_state.exploration_notes) + len(_plan_state.decisions_made),
            },
            metadata={"timestamp": timestamp},
        )

    except Exception as e:
        logger.error(f"AddPlanNote error: {e}")
        return ToolResult(success=False, error=str(e))


def get_plan_status() -> ToolResult:
    """Get current plan mode status."""
    global _plan_state

    if not _plan_state.active:
        return ToolResult(
            success=True,
            data={
                "active": False,
                "message": "Not in plan mode",
            },
        )

    duration = datetime.now() - (_plan_state.started_at or datetime.now())

    return ToolResult(
        success=True,
        data={
            "active": True,
            "task_description": _plan_state.task_description,
            "started_at": _plan_state.started_at.isoformat() if _plan_state.started_at else None,
            "duration_seconds": duration.total_seconds(),
            "files_explored": len(_plan_state.files_explored),
            "decisions_made": len(_plan_state.decisions_made),
            "questions_pending": len(_plan_state.questions_pending),
            "exploration_notes": len(_plan_state.exploration_notes),
            "plan_file": str(_plan_state.plan_file) if _plan_state.plan_file else None,
        },
        metadata={"plan_mode": True},
    )


# Create and register plan mode tools
plan_mode_tools = [
    create_validated_tool(
        name="enter_plan_mode",
        description="Enter planning mode for complex tasks requiring exploration",
        category="context",
        parameters={
            "task_description": {
                "type": "string",
                "description": "Brief description of the task to plan",
                "default": "",
            },
            "plan_file": {
                "type": "string",
                "description": "Path for the plan file",
                "default": ".qwen/plans/current_plan.md",
            },
        },
        required_params=[],
        execute_func=enter_plan_mode,
    ),
    create_validated_tool(
        name="exit_plan_mode",
        description="Exit planning mode and present plan for approval",
        category="context",
        parameters={},
        required_params=[],
        execute_func=exit_plan_mode,
    ),
    create_validated_tool(
        name="add_plan_note",
        description="Add a note to the current plan during planning mode",
        category="context",
        parameters={
            "note": {"type": "string", "description": "Note content to add", "required": True},
            "category": {
                "type": "string",
                "description": "Note category",
                "default": "exploration",
                "enum": ["exploration", "decision", "question", "file"],
            },
        },
        required_params=["note"],
        execute_func=add_plan_note,
    ),
    create_validated_tool(
        name="get_plan_status",
        description="Get current plan mode status and progress",
        category="context",
        parameters={},
        required_params=[],
        execute_func=get_plan_status,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in plan_mode_tools:
    register_tool(tool)
