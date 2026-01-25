"""
Workflow Visualization Module.

Provides real-time workflow visualization with research-driven UX patterns.

Architecture (Modular Refactoring):
- types.py: Domain models (StepStatus, WorkflowStep, Checkpoint)
- renderers.py: Rich terminal rendering functions
- visualizer.py: Core WorkflowVisualizer class
- tracker.py: ParallelExecutionTracker for concurrent execution

All public symbols are re-exported here for backward compatibility.
"""

from .types import StepStatus, WorkflowStep, Checkpoint
from .visualizer import WorkflowVisualizer
from .tracker import ParallelExecutionTracker
from .renderers import (
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
    # Types
    "StepStatus",
    "WorkflowStep",
    "Checkpoint",
    # Core classes
    "WorkflowVisualizer",
    "ParallelExecutionTracker",
    # Render functions
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
