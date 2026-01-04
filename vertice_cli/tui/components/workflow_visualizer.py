"""
Visual Workflow System - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- workflow/types.py: Domain models (StepStatus, WorkflowStep)
- workflow/renderers.py: Rich terminal rendering functions
- workflow/visualizer.py: Core WorkflowVisualizer class
- workflow/tracker.py: ParallelExecutionTracker

All symbols are re-exported here for backward compatibility.
Import from 'workflow' subpackage for new code.
"""

# Re-export all public symbols for backward compatibility
from .workflow import (
    # Types
    StepStatus,
    WorkflowStep,
    Checkpoint,
    # Core classes
    WorkflowVisualizer,
    ParallelExecutionTracker,
    # Render functions (for direct use)
    get_status_style,
    render_progress_bar,
    render_dependency_tree,
    render_progress_table,
    render_metrics,
    render_minimap,
    render_streaming_view,
    render_diff_view,
    render_ai_suggestions,
    render_checkpoint_view,
)

__all__ = [
    "StepStatus",
    "WorkflowStep",
    "Checkpoint",
    "WorkflowVisualizer",
    "ParallelExecutionTracker",
    "get_status_style",
    "render_progress_bar",
    "render_dependency_tree",
    "render_progress_table",
    "render_metrics",
    "render_minimap",
    "render_streaming_view",
    "render_diff_view",
    "render_ai_suggestions",
    "render_checkpoint_view",
]
