"""
Workflow Visualizer - Core visualization engine.

Real-time workflow visualization with research-driven UX patterns:
- Streaming token updates (Cursor/Claude inspiration)
- Mini-map overview (Windsurf inspiration)
- Diff-style change visualization (GitHub Copilot)
- Rich error context + AI suggestions
- Checkpoint visualization (Cursor Composer)

Constitutional Compliance:
- P1 (Completude): Full workflow state tracking
- P2 (Validacao): Visual validation of execution flow
- P3 (Ceticismo): Shows actual vs expected progress
- P6 (Eficiencia): Minimal overhead (<5ms per update)
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from .types import StepStatus, WorkflowStep
from . import renderers


class WorkflowVisualizer:
    """
    Real-time workflow visualization system.

    Features (Research-Driven):
    - Streaming token updates
    - Mini-map overview
    - Diff-style change visualization
    - Rich error context + AI suggestions
    - Checkpoint visualization
    - Multi-modal feedback synthesis

    Performance (60fps optimized):
    - Differential rendering
    - State hashing
    - Render caching
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize workflow visualizer.

        Args:
            console: Rich Console instance for output
        """
        self.console = console or Console()
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.start_time: Optional[datetime] = None

        # Streaming callback
        self.streaming_callback: Optional[Callable[[str, str], None]] = None

        # Checkpoints tracking
        self.checkpoints: Dict[str, Dict] = {}

        # Layout for multi-panel view
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="minimap", size=5),
            Layout(name="main"),
            Layout(name="details", size=10),
        )

        # Performance: Render caching (60fps optimization)
        self._cache: Dict[str, Tuple[Any, str]] = {}
        self._dirty_flags: Set[str] = {"minimap", "main", "details"}
        self._last_render_time: float = 0.0
        self._target_fps: int = 60
        self._frame_budget_ms: float = 1000.0 / self._target_fps

    def add_step(
        self, step_id: str, name: str, dependencies: Optional[List[str]] = None
    ) -> WorkflowStep:
        """Add a workflow step."""
        step = WorkflowStep(id=step_id, name=name, dependencies=dependencies or [])
        self.steps[step_id] = step
        return step

    def update_step(
        self,
        step_id: str,
        status: Optional[StepStatus] = None,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        ai_suggestion: Optional[str] = None,
    ) -> None:
        """Update step state (Enhanced with AI suggestions)."""
        if step_id not in self.steps:
            return

        step = self.steps[step_id]

        if status:
            step.status = status
            if status == StepStatus.RUNNING and not step.start_time:
                step.start_time = datetime.now()
            elif status in (StepStatus.COMPLETED, StepStatus.FAILED):
                step.end_time = datetime.now()
                if step_id not in self.execution_order:
                    self.execution_order.append(step_id)

        if progress is not None:
            step.progress = max(0.0, min(1.0, progress))

        if error:
            step.error = error

        if ai_suggestion:
            step.ai_suggestion = ai_suggestion

        # Mark affected views as dirty
        self._dirty_flags.update({"minimap", "main", "details"})

    def stream_token(self, step_id: str, token: str) -> None:
        """Stream token update for real-time LLM output visualization."""
        if step_id not in self.steps:
            return

        step = self.steps[step_id]
        step.add_streaming_token(token)

        if self.streaming_callback:
            self.streaming_callback(step_id, token)

    def add_change(self, step_id: str, change_type: str, before: str, after: str) -> None:
        """Track change diff-style."""
        if step_id not in self.steps:
            return

        step = self.steps[step_id]
        step.add_change(change_type, before, after)

    def create_checkpoint(self, description: str) -> str:
        """Create checkpoint for undo/rollback. Returns checkpoint ID."""
        checkpoint_id = f"cp_{int(time.time())}"
        self.checkpoints[checkpoint_id] = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "steps_state": {
                sid: {
                    "status": step.status.value,
                    "progress": step.progress,
                    "error": step.error,
                }
                for sid, step in self.steps.items()
            },
        }
        return checkpoint_id

    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to checkpoint (undo support)."""
        if checkpoint_id not in self.checkpoints:
            return False

        checkpoint = self.checkpoints[checkpoint_id]
        steps_state = checkpoint["steps_state"]

        for step_id, state in steps_state.items():
            if step_id in self.steps:
                step = self.steps[step_id]
                step.status = StepStatus(state["status"])
                step.progress = state["progress"]
                step.error = state["error"]

        return True

    def _compute_state_hash(self, section: str) -> str:
        """Compute hash of current state for cache validation."""
        if section == "minimap":
            state = [(s.status.value, s.progress) for s in self.steps.values()]
        elif section == "main":
            state = [
                (s.id, s.status.value, s.progress, s.error, s.duration) for s in self.steps.values()
            ]
        elif section == "details":
            running = [sid for sid, s in self.steps.items() if s.status == StepStatus.RUNNING]
            if running:
                step = self.steps[running[0]]
                state = (
                    running[0],
                    len(step.streaming_tokens),
                    len(step.changes),
                    step.ai_suggestion,
                )
            else:
                state = list(self.checkpoints.keys())
        else:
            state = []

        return hashlib.md5(str(state).encode()).hexdigest()

    def render_full_view(self) -> Layout:
        """
        Render complete workflow visualization (60fps optimized).

        Performance improvements:
        - Differential rendering: Only update changed sections
        - State hashing: Skip render if state unchanged
        - Frame budget: ~16.67ms per frame
        """
        frame_start = time.time()

        # Minimap (only if dirty)
        if "minimap" in self._dirty_flags:
            state_hash = self._compute_state_hash("minimap")
            cache_key = "minimap"

            if cache_key not in self._cache or self._cache[cache_key][1] != state_hash:
                rendered = renderers.render_minimap(self.steps)
                self._cache[cache_key] = (rendered, state_hash)
            else:
                rendered = self._cache[cache_key][0]

            self.layout["minimap"].update(rendered)
            self._dirty_flags.discard("minimap")

        # Main view (most expensive - always cache)
        if "main" in self._dirty_flags:
            state_hash = self._compute_state_hash("main")
            cache_key = "main"

            if cache_key not in self._cache or self._cache[cache_key][1] != state_hash:
                main_group = renderers.create_main_view(
                    self.steps, self.execution_order, self.start_time
                )
                self._cache[cache_key] = (main_group, state_hash)
            else:
                main_group = self._cache[cache_key][0]

            self.layout["main"].update(main_group)
            self._dirty_flags.discard("main")

        # Details view (context-aware)
        if "details" in self._dirty_flags:
            state_hash = self._compute_state_hash("details")
            cache_key = "details"

            if cache_key not in self._cache or self._cache[cache_key][1] != state_hash:
                details_group = renderers.create_details_view(self.steps, self.checkpoints)
                self._cache[cache_key] = (details_group, state_hash)
            else:
                details_group = self._cache[cache_key][0]

            self.layout["details"].update(details_group)
            self._dirty_flags.discard("details")

        # Track frame time
        frame_time_ms = (time.time() - frame_start) * 1000
        self._last_render_time = frame_time_ms

        return self.layout

    def live_display(self, target_fps: int = 60) -> Live:
        """
        Create live-updating display (60fps optimized).

        Args:
            target_fps: Target frames per second

        Returns:
            Rich Live context manager
        """
        self._target_fps = target_fps
        self._frame_budget_ms = 1000.0 / target_fps

        return Live(self.render_full_view(), console=self.console, refresh_per_second=target_fps)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        actual_fps = 1000.0 / self._last_render_time if self._last_render_time > 0 else 0

        return {
            "last_frame_time_ms": round(self._last_render_time, 2),
            "target_frame_time_ms": round(self._frame_budget_ms, 2),
            "cache_size": len(self._cache),
            "current_fps": round(actual_fps, 1),
            "target_fps": self._target_fps,
            "performance_ok": self._last_render_time < self._frame_budget_ms,
        }

    # Delegate rendering to renderers module
    def render_dependency_tree(self):
        """Render workflow as dependency tree."""
        return renderers.render_dependency_tree(self.steps, self.start_time)

    def render_progress_table(self):
        """Render progress summary table."""
        return renderers.render_progress_table(self.steps, self.execution_order)

    def render_metrics(self):
        """Render overall workflow metrics."""
        return renderers.render_metrics(self.steps, self.start_time)

    def render_minimap(self):
        """Render mini-map overview."""
        return renderers.render_minimap(self.steps)

    def render_streaming_view(self, step_id: str):
        """Render streaming tokens for a step."""
        step = self.steps.get(step_id)
        return renderers.render_streaming_view(step)

    def render_diff_view(self, step_id: str):
        """Render changes diff-style for a step."""
        step = self.steps.get(step_id)
        return renderers.render_diff_view(step)

    def render_ai_suggestions(self, step_id: str):
        """Render AI suggestions for a step."""
        step = self.steps.get(step_id)
        return renderers.render_ai_suggestions(step)

    def render_checkpoint_view(self):
        """Render checkpoints view."""
        return renderers.render_checkpoint_view(self.checkpoints)


__all__ = ["WorkflowVisualizer"]
