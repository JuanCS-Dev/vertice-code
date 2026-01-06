from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Deque, Dict, List, Optional

from core.observability import ObservabilityMixin
from vertice_core.messaging.events import get_event_bus

from .events import (
    PrometheusTaskReceived,
    PrometheusTaskCompleted,
    PrometheusTaskFailed,
    PrometheusStepExecuted,
)
from .llm_client import GeminiClient
from .world_model import WorldModel, ActionType
from .reflection import ReflectionEngine
from .evolution import CoEvolutionLoop
from .persistence import persistence
from .governance import PrometheusGovernanceBridge
from .builtin_tools import BuiltinTools
from ..memory.memory_system import MemorySystem
from ..tools.tool_factory import ToolFactory
from ..sandbox.executor import SandboxExecutor

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of orchestrated execution."""

    task: str
    output: str
    success: bool
    score: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    execution_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "task": self.task[:100],
            "success": self.success,
            "score": self.score,
            "tools_used": self.tools_used,
            "execution_time": self.execution_time,
        }


class PrometheusOrchestrator(ObservabilityMixin):
    """Main Orchestrator for PROMETHEUS with Governance and Observability."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        agent_name: str = "Prometheus",
        event_bus: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
    ):
        self.llm = llm_client or GeminiClient()
        self.agent_name = agent_name
        self.agent_id = agent_name.lower()
        self.event_bus = event_bus or get_event_bus()

        # Initialize Governance Bridge
        self.governance = PrometheusGovernanceBridge(self.llm, mcp_client)

        # Subsystems
        self.memory = MemorySystem(agent_name=agent_name)
        self.sandbox = SandboxExecutor()
        self.tools = ToolFactory(self.llm, self.sandbox)
        self.world_model = WorldModel(self.llm)
        self.reflection = ReflectionEngine(self.llm, self.memory)
        self.evolution = CoEvolutionLoop(
            self.llm, self.tools, self.memory, self.reflection, self.sandbox
        )

        self.builtin = BuiltinTools(self)
        self._register_builtin_tools()
        self.execution_history: Deque[ExecutionResult] = deque(maxlen=500)
        self._execution_semaphore = asyncio.Semaphore(1)
        self._persistence_initialized = False

    async def _ensure_persistence(self) -> None:
        """Ensure persistence layer is active and state is loaded."""
        if self._persistence_initialized:
            return
        await persistence.initialize()
        saved = await persistence.load_state(self.agent_name)
        if saved:
            self.import_state(saved)
        self._persistence_initialized = True

    def _register_builtin_tools(self) -> None:
        """Register core tools into the factory."""
        self.tools.register_builtin("read_file", self.builtin.read_file)
        self.tools.register_builtin("write_file", self.builtin.write_file)
        self.tools.register_builtin("list_files", self.builtin.list_files)
        self.tools.register_builtin("execute_python", self.builtin.execute_python)
        self.tools.register_builtin("remember", self.builtin.remember)
        self.tools.register_builtin("recall", self.builtin.recall)

    async def execute(
        self, task: str, stream: bool = True, fast_mode: bool = True
    ) -> AsyncIterator[str]:
        """Orchestrated task execution loop."""
        async with self._execution_semaphore:
            await self._ensure_persistence()
            start_time = datetime.now()
            task_id = str(uuid.uuid4())

            self.event_bus.emit_sync(
                PrometheusTaskReceived(
                    data={
                        "task_id": task_id,
                        "request": task,
                        "complexity": "simple" if fast_mode else "complex",
                    }
                )
            )

            with self.trace_operation(
                "execute", agent_id=self.agent_id, attributes={"task_id": task_id}
            ):
                try:
                    # GOVERNANCE CHECK
                    with self.trace_operation("governance_review"):
                        yield "🏛️ **Governance** reviewing task...\n"
                        verdict = await self.governance.review_task(task, {"task_id": task_id})
                        if not verdict.approved:
                            yield f"\n🛑 **VETO** by {verdict.governor}: {verdict.reasoning}\n"
                            # Show suggestions if available
                            if hasattr(verdict, "suggestions") and verdict.suggestions:
                                yield f"💡 Suggestion: {verdict.suggestions}\n"

                            # Emit failure event for governance block
                            self.event_bus.emit_sync(
                                PrometheusTaskFailed(
                                    data={
                                        "task_id": task_id,
                                        "error": f"Governance Veto: {verdict.reasoning}",
                                        "error_type": "GovernanceVeto",
                                        "failed_at_step": 0,
                                    }
                                )
                            )
                            return

                    yield "🔥 **PROMETHEUS** executing...\n\n"

                    if fast_mode:
                        with self.trace_operation("fast_execution"):
                            output = await self._execute_task_with_context(task, {}, None)
                            yield output

                            # Emit step event
                            self.event_bus.emit_sync(
                                PrometheusStepExecuted(
                                    data={
                                        "task_id": task_id,
                                        "step_index": 1,
                                        "action": "fast_execution",
                                        "output": output[:100],
                                        "duration_ms": (datetime.now() - start_time).total_seconds()
                                        * 1000,
                                    }
                                )
                            )
                    else:
                        with self.trace_operation("contextualization"):
                            yield "📚 Retrieving context...\n"
                            ctx = self.memory.get_context_for_task(task)

                        with self.trace_operation("planning"):
                            yield "🌍 Planning approach...\n"
                            plans = await self.world_model.find_best_plan(
                                task, [ActionType.THINK, ActionType.USE_TOOL]
                            )

                        with self.trace_operation("full_execution"):
                            output = await self._execute_task_with_context(
                                task, ctx, plans[0] if plans else None
                            )
                            yield f"\n{output}\n"

                        with self.trace_operation("reflection"):
                            yield "🪞 Reflecting...\n"
                            refl = await self.reflection.critique_action(task, output[:500], {})
                            self.memory.remember_experience(
                                task, output[:200], importance=refl.score
                            )

                    duration = (datetime.now() - start_time).total_seconds()
                    self.event_bus.emit_sync(
                        PrometheusTaskCompleted(data={"task_id": task_id, "result": output[:100]})
                    )
                    yield f"\n\n✅ Done in {duration:.1f}s\n"

                except Exception as e:
                    self.event_bus.emit_sync(
                        PrometheusTaskFailed(data={"task_id": task_id, "error": str(e)})
                    )
                    yield f"\n❌ Error: {str(e)}\n"
                    raise
                finally:
                    # Auto-save after every execution
                    await persistence.save_state(self.agent_name, self.export_state())

    async def _execute_task_with_context(self, task: str, context: Dict, plan: Any) -> str:
        """Call LLM with gathered context and plan."""
        prompt = f"TASK: {task}\nCONTEXT: {context}\nTOOLS: {self.tools.list_tools()[:10]}"
        with self.trace_llm_call(model="gemini-pro"):
            response = await self.llm.generate(prompt)
            return await self._execute_inline_tools(response)

    async def _execute_inline_tools(self, response: str) -> str:
        """Parse and execute [TOOL:name:args] patterns."""
        import re

        tool_pattern = r"\[TOOL:(\w+):(.*)\]"
        for match in re.finditer(tool_pattern, response):
            name = match.group(1)
            args_str = match.group(2)
            args = {}
            if args_str:
                for pair in args_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        args[k.strip()] = v.strip()
            await self._execute_tool(name, args)
        return response

    async def _execute_tool(self, name: str, args: Dict) -> str:
        """Trace and dispatch tool execution."""
        with self.trace_tool(name, parameters=args):
            try:
                tool_map = {
                    "write_file": self.builtin.write_file,
                    "read_file": self.builtin.read_file,
                    "remember": self.builtin.remember,
                    "recall": self.builtin.recall,
                }
                if name in tool_map:
                    return await tool_map[name](**args)
                return f"Unknown tool: {name}"
            except Exception as e:
                return f"Error: {str(e)}"

    # === Compatibility Methods for Legacy Tests ===

    async def execute_simple(self, task: str) -> str:
        """Compatibility: execute task and return string."""
        output = []
        async for chunk in self.execute(task, stream=True):
            output.append(chunk)
        return "".join(output)

    async def _tool_remember(self, key: str, value: str) -> str:
        """Legacy alias for remember tool."""
        return await self.builtin.remember(key, value)

    async def _tool_recall(self, query: str) -> str:
        """Legacy alias for recall tool."""
        return await self.builtin.recall(query)

    # === State Management ===

    def export_state(self) -> Dict:
        """Export state for persistence."""
        history_list = list(self.execution_history)
        return {
            "agent_name": self.agent_name,
            "memory": self.memory.export_state(),
            "evolution": self.evolution.export_state(),
            "execution_history": [r.to_dict() for r in history_list[-100:]],
        }

    def import_state(self, state: Dict) -> None:
        """Restore state from persistence."""
        self.agent_name = state.get("agent_name", self.agent_name)
        if "memory" in state:
            self.memory.import_state(state["memory"])
        if "evolution" in state:
            self.evolution.import_state(state["evolution"])

    @property
    def is_busy(self) -> bool:
        """Check if semaphore is locked."""
        return self._execution_semaphore.locked()
