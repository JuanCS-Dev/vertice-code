"""
PIPELINE OBSERVER - Eagle Eye Observability

Hooks into EVERY stage of the Vertice pipeline to provide
detailed diagnostics on WHERE and WHY the system fails.

This is NOT a mock - this observes REAL execution.
"""

import asyncio
import time
import json
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
from enum import Enum
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class PipelineStage(Enum):
    """All observable stages in the pipeline."""

    PROMPT_RECEIVED = "1_prompt_received"
    PROMPT_PARSED = "2_prompt_parsed"
    INTENT_CLASSIFIED = "3_intent_classified"
    AGENT_SELECTED = "4_agent_selected"
    TASKS_DECOMPOSED = "5_tasks_decomposed"
    TOOLS_IDENTIFIED = "6_tools_identified"
    CONTEXT_LOADED = "7_context_loaded"
    LLM_CALLED = "8_llm_called"
    THINKING_STARTED = "9_thinking_started"
    THINKING_STEP = "9a_thinking_step"
    THINKING_COMPLETED = "9b_thinking_completed"
    TOOL_EXECUTED = "10_tool_executed"
    STREAMING_CHUNK = "11_streaming_chunk"
    TODO_UPDATED = "12_todo_updated"
    RESULT_GENERATED = "13_result_generated"
    ERROR_OCCURRED = "99_error"


@dataclass
class StageObservation:
    """Observation of a single pipeline stage."""

    stage: PipelineStage
    timestamp: float
    duration_ms: float
    success: bool
    input_data: Any
    output_data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "stage": self.stage.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "input_summary": self._summarize(self.input_data),
            "output_summary": self._summarize(self.output_data),
            "metadata": self.metadata,
            "error": self.error,
        }

    def _summarize(self, data: Any, max_len: int = 200) -> str:
        """Summarize data for logging."""
        if data is None:
            return "None"
        s = str(data)
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s


@dataclass
class ThinkingStep:
    """A single step in the tree of thoughts."""

    step_number: int
    thought: str
    reasoning: str
    confidence: float
    alternatives_considered: List[str] = field(default_factory=list)
    decision: Optional[str] = None


@dataclass
class PipelineTrace:
    """Complete trace of a pipeline execution."""

    trace_id: str
    prompt: str
    started_at: float
    completed_at: Optional[float] = None
    observations: List[StageObservation] = field(default_factory=list)
    thinking_steps: List[ThinkingStep] = field(default_factory=list)
    tasks_generated: List[Dict] = field(default_factory=list)
    tools_called: List[Dict] = field(default_factory=list)
    todos_created: List[Dict] = field(default_factory=list)
    final_result: Optional[str] = None
    success: bool = False
    failure_point: Optional[PipelineStage] = None
    failure_reason: Optional[str] = None

    def add_observation(self, obs: StageObservation):
        """Add an observation to the trace."""
        self.observations.append(obs)
        if not obs.success and self.failure_point is None:
            self.failure_point = obs.stage
            self.failure_reason = obs.error

    def get_stage_duration(self, stage: PipelineStage) -> Optional[float]:
        """Get duration of a specific stage."""
        for obs in self.observations:
            if obs.stage == stage:
                return obs.duration_ms
        return None

    def get_total_duration(self) -> float:
        """Get total execution duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return sum(obs.duration_ms for obs in self.observations)

    def get_diagnostic_report(self) -> str:
        """Generate detailed diagnostic report."""
        lines = [
            "=" * 70,
            "PIPELINE DIAGNOSTIC REPORT",
            "=" * 70,
            f"Trace ID: {self.trace_id}",
            f"Prompt: {self.prompt[:100]}{'...' if len(self.prompt) > 100 else ''}",
            f"Total Duration: {self.get_total_duration():.0f}ms",
            f"Success: {self.success}",
            "",
            "STAGE BREAKDOWN:",
            "-" * 70,
        ]

        for obs in self.observations:
            status = "✓" if obs.success else "✗"
            lines.append(
                f"  {status} {obs.stage.value}: {obs.duration_ms:.0f}ms"
            )
            if not obs.success:
                lines.append(f"      ERROR: {obs.error}")

        if self.thinking_steps:
            lines.extend([
                "",
                "THINKING PROCESS:",
                "-" * 70,
            ])
            for step in self.thinking_steps:
                lines.append(f"  Step {step.step_number}: {step.thought[:80]}...")
                lines.append(f"    Confidence: {step.confidence:.1%}")
                if step.decision:
                    lines.append(f"    Decision: {step.decision}")

        if self.tasks_generated:
            lines.extend([
                "",
                "TASKS GENERATED:",
                "-" * 70,
            ])
            for i, task in enumerate(self.tasks_generated, 1):
                lines.append(f"  {i}. {task.get('description', 'Unknown')[:60]}")

        if self.tools_called:
            lines.extend([
                "",
                "TOOLS CALLED:",
                "-" * 70,
            ])
            for tool in self.tools_called:
                status = "✓" if tool.get('success') else "✗"
                lines.append(
                    f"  {status} {tool.get('name', 'Unknown')}: {tool.get('duration_ms', 0):.0f}ms"
                )

        if self.failure_point:
            lines.extend([
                "",
                "FAILURE ANALYSIS:",
                "-" * 70,
                f"  Failed at: {self.failure_point.value}",
                f"  Reason: {self.failure_reason}",
            ])

        lines.append("=" * 70)
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export trace as JSON."""
        return json.dumps({
            "trace_id": self.trace_id,
            "prompt": self.prompt,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.get_total_duration(),
            "success": self.success,
            "failure_point": self.failure_point.value if self.failure_point else None,
            "failure_reason": self.failure_reason,
            "observations": [obs.to_dict() for obs in self.observations],
            "thinking_steps": [
                {
                    "step": s.step_number,
                    "thought": s.thought,
                    "confidence": s.confidence,
                    "decision": s.decision,
                }
                for s in self.thinking_steps
            ],
            "tasks_generated": self.tasks_generated,
            "tools_called": self.tools_called,
            "todos_created": self.todos_created,
        }, indent=2)


class PipelineObserver:
    """
    Eagle Eye Observer for the Vertice Pipeline.

    Hooks into every stage and provides detailed diagnostics.
    """

    def __init__(self):
        self.current_trace: Optional[PipelineTrace] = None
        self.all_traces: List[PipelineTrace] = []
        self._stage_start_time: float = 0
        self._hooks: Dict[PipelineStage, List[Callable]] = {
            stage: [] for stage in PipelineStage
        }

    def start_trace(self, prompt: str) -> PipelineTrace:
        """Start a new pipeline trace."""
        import uuid

        trace = PipelineTrace(
            trace_id=str(uuid.uuid4())[:8],
            prompt=prompt,
            started_at=time.time(),
        )
        self.current_trace = trace
        self.all_traces.append(trace)

        self._observe(
            PipelineStage.PROMPT_RECEIVED,
            input_data=prompt,
            output_data={"length": len(prompt), "words": len(prompt.split())},
            success=True,
        )

        return trace

    def end_trace(self, success: bool, result: Optional[str] = None):
        """End the current trace."""
        if self.current_trace:
            self.current_trace.completed_at = time.time()
            self.current_trace.success = success
            self.current_trace.final_result = result

            self._observe(
                PipelineStage.RESULT_GENERATED,
                input_data=None,
                output_data=result[:500] if result else None,
                success=success,
            )

    def observe_parsing(self, raw_input: str, parsed_output: Dict):
        """Observe prompt parsing stage."""
        self._observe(
            PipelineStage.PROMPT_PARSED,
            input_data=raw_input,
            output_data=parsed_output,
            success=parsed_output is not None,
            metadata={"tokens_estimated": len(raw_input.split())},
        )

    def observe_intent(
        self,
        text: str,
        intent: str,
        confidence: float,
        alternatives: List[str] = None
    ):
        """Observe intent classification stage."""
        self._observe(
            PipelineStage.INTENT_CLASSIFIED,
            input_data=text,
            output_data={
                "intent": intent,
                "confidence": confidence,
                "alternatives": alternatives or [],
            },
            success=confidence > 0.3,
            metadata={
                "confidence_level": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
            },
        )

    def observe_agent_selection(
        self,
        intent: str,
        agent_id: str,
        reason: str,
        candidates: List[str] = None
    ):
        """Observe agent selection stage."""
        self._observe(
            PipelineStage.AGENT_SELECTED,
            input_data={"intent": intent},
            output_data={
                "agent_id": agent_id,
                "reason": reason,
                "candidates_considered": candidates or [],
            },
            success=agent_id is not None,
        )

    def observe_task_decomposition(
        self,
        request: str,
        tasks: List[Dict],
        decomposition_method: str = "unknown"
    ):
        """Observe task decomposition stage."""
        if self.current_trace:
            self.current_trace.tasks_generated = tasks

        self._observe(
            PipelineStage.TASKS_DECOMPOSED,
            input_data=request,
            output_data={
                "task_count": len(tasks),
                "tasks": [t.get("description", str(t))[:50] for t in tasks],
            },
            success=len(tasks) > 0,
            metadata={
                "method": decomposition_method,
                "is_multi_task": len(tasks) > 1,
            },
        )

    def observe_tool_identification(
        self,
        task: str,
        tools: List[str],
        selection_method: str = "unknown"
    ):
        """Observe tool identification stage."""
        self._observe(
            PipelineStage.TOOLS_IDENTIFIED,
            input_data=task,
            output_data={"tools": tools},
            success=True,
            metadata={"method": selection_method},
        )

    def observe_llm_call(
        self,
        prompt: str,
        model: str,
        provider: str,
        tokens_in: int = 0,
        tokens_out: int = 0
    ):
        """Observe LLM call stage."""
        self._observe(
            PipelineStage.LLM_CALLED,
            input_data={"prompt_length": len(prompt), "model": model},
            output_data={"provider": provider, "tokens_in": tokens_in, "tokens_out": tokens_out},
            success=True,
            metadata={"model": model, "provider": provider},
        )

    def observe_thinking_start(self, initial_thought: str):
        """Observe start of thinking/reasoning process."""
        self._observe(
            PipelineStage.THINKING_STARTED,
            input_data=None,
            output_data=initial_thought,
            success=True,
        )

    def observe_thinking_step(
        self,
        step_number: int,
        thought: str,
        reasoning: str,
        confidence: float,
        alternatives: List[str] = None,
        decision: str = None
    ):
        """Observe a single thinking step."""
        step = ThinkingStep(
            step_number=step_number,
            thought=thought,
            reasoning=reasoning,
            confidence=confidence,
            alternatives_considered=alternatives or [],
            decision=decision,
        )

        if self.current_trace:
            self.current_trace.thinking_steps.append(step)

        self._observe(
            PipelineStage.THINKING_STEP,
            input_data={"step": step_number},
            output_data={
                "thought": thought[:100],
                "confidence": confidence,
                "decision": decision,
            },
            success=True,
            metadata={"alternatives_count": len(alternatives or [])},
        )

    def observe_thinking_complete(self, final_reasoning: str, total_steps: int):
        """Observe completion of thinking process."""
        self._observe(
            PipelineStage.THINKING_COMPLETED,
            input_data={"total_steps": total_steps},
            output_data=final_reasoning,
            success=True,
        )

    def observe_tool_execution(
        self,
        tool_name: str,
        args: Dict,
        result: Any,
        success: bool,
        error: str = None
    ):
        """Observe tool execution."""
        tool_record = {
            "name": tool_name,
            "args": str(args)[:100],
            "success": success,
            "error": error,
            "duration_ms": self._get_stage_duration(),
        }

        if self.current_trace:
            self.current_trace.tools_called.append(tool_record)

        self._observe(
            PipelineStage.TOOL_EXECUTED,
            input_data={"tool": tool_name, "args": args},
            output_data=result if success else error,
            success=success,
            error=error,
        )

    def observe_streaming_chunk(
        self,
        chunk_number: int,
        content: str,
        chunk_type: str = "text"
    ):
        """Observe streaming chunk."""
        self._observe(
            PipelineStage.STREAMING_CHUNK,
            input_data={"chunk_number": chunk_number},
            output_data={"content_length": len(content), "type": chunk_type},
            success=True,
            metadata={"chunk_type": chunk_type},
        )

    def observe_todo_update(
        self,
        action: str,
        todo_item: Dict,
        all_todos: List[Dict]
    ):
        """Observe todo list update."""
        if self.current_trace:
            self.current_trace.todos_created = all_todos

        self._observe(
            PipelineStage.TODO_UPDATED,
            input_data={"action": action, "item": todo_item},
            output_data={"total_todos": len(all_todos)},
            success=True,
        )

    def observe_error(
        self,
        stage: PipelineStage,
        error: Exception,
        context: Dict = None
    ):
        """Observe an error at any stage."""
        self._observe(
            PipelineStage.ERROR_OCCURRED,
            input_data={"stage": stage.value, "context": context},
            output_data=None,
            success=False,
            error=str(error),
            metadata={"original_stage": stage.value},
        )

        if self.current_trace:
            self.current_trace.failure_point = stage
            self.current_trace.failure_reason = str(error)

    def add_hook(self, stage: PipelineStage, callback: Callable):
        """Add a hook to be called when a stage is observed."""
        self._hooks[stage].append(callback)

    def _observe(
        self,
        stage: PipelineStage,
        input_data: Any,
        output_data: Any,
        success: bool,
        error: str = None,
        metadata: Dict = None
    ):
        """Internal method to record an observation."""
        duration = self._get_stage_duration()
        self._stage_start_time = time.time()

        obs = StageObservation(
            stage=stage,
            timestamp=time.time(),
            duration_ms=duration,
            success=success,
            input_data=input_data,
            output_data=output_data,
            metadata=metadata or {},
            error=error,
            stack_trace=traceback.format_exc() if error else None,
        )

        if self.current_trace:
            self.current_trace.add_observation(obs)

        # Call hooks
        for hook in self._hooks[stage]:
            try:
                hook(obs)
            except Exception as e:
                print(f"Hook error: {e}")

    def _get_stage_duration(self) -> float:
        """Get duration since last stage."""
        if self._stage_start_time == 0:
            self._stage_start_time = time.time()
            return 0
        return (time.time() - self._stage_start_time) * 1000

    def get_current_report(self) -> str:
        """Get diagnostic report for current trace."""
        if self.current_trace:
            return self.current_trace.get_diagnostic_report()
        return "No active trace"

    def export_trace(self, filepath: str):
        """Export current trace to file."""
        if self.current_trace:
            with open(filepath, "w") as f:
                f.write(self.current_trace.to_json())

    def get_failure_analysis(self) -> Dict:
        """Analyze failures across all traces."""
        failures_by_stage = {}
        total_traces = len(self.all_traces)
        failed_traces = [t for t in self.all_traces if not t.success]

        for trace in failed_traces:
            if trace.failure_point:
                stage = trace.failure_point.value
                if stage not in failures_by_stage:
                    failures_by_stage[stage] = {
                        "count": 0,
                        "reasons": [],
                    }
                failures_by_stage[stage]["count"] += 1
                if trace.failure_reason:
                    failures_by_stage[stage]["reasons"].append(trace.failure_reason)

        return {
            "total_traces": total_traces,
            "successful": total_traces - len(failed_traces),
            "failed": len(failed_traces),
            "success_rate": (total_traces - len(failed_traces)) / total_traces if total_traces > 0 else 0,
            "failures_by_stage": failures_by_stage,
        }


# Global observer instance
_global_observer: Optional[PipelineObserver] = None


def get_observer() -> PipelineObserver:
    """Get the global pipeline observer."""
    global _global_observer
    if _global_observer is None:
        _global_observer = PipelineObserver()
    return _global_observer


def reset_observer():
    """Reset the global observer."""
    global _global_observer
    _global_observer = PipelineObserver()
