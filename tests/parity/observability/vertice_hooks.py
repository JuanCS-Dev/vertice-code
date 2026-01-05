"""
VERTICE HOOKS - Real Pipeline Integration

This module hooks the PipelineObserver into the REAL Vertice system.
It patches key components to capture observations at each stage.

NO MOCKS - This observes actual system behavior.
"""

import functools
import time
from typing import Any, Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.parity.observability.pipeline_observer import (
    PipelineObserver,
    PipelineStage,
    get_observer,
)


class VerticeHookedClient:
    """
    Vertice client with observability hooks installed.

    This wraps the real TUIBridge and adds observation
    at every stage of the pipeline.
    """

    def __init__(self, observer: Optional[PipelineObserver] = None):
        self.observer = observer or get_observer()
        self.bridge = None
        self.original_methods = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize and hook into the real Vertice system."""
        try:
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            # Bridge initializes in __init__, no async init needed

            # Install hooks
            self._install_hooks()
            self._initialized = True
            return True

        except ImportError as e:
            print(f"Could not import Vertice: {e}")
            return False
        except Exception as e:
            print(f"Initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _install_hooks(self):
        """Install observation hooks into the pipeline."""
        if not self.bridge:
            return

        # Hook into agent router if available
        if hasattr(self.bridge, 'agent_manager'):
            self._hook_agent_router()

        # Hook into chat controller if available
        if hasattr(self.bridge, 'chat_controller'):
            self._hook_chat_controller()

        # Hook into tool executor if available
        if hasattr(self.bridge, 'tool_bridge'):
            self._hook_tool_bridge()

    def _hook_agent_router(self):
        """Hook into agent routing."""
        if hasattr(self.bridge.agent_manager, 'route'):
            original = self.bridge.agent_manager.route
            self.original_methods['route'] = original

            @functools.wraps(original)
            async def hooked_route(message: str, *args, **kwargs):
                start = time.time()
                result = await original(message, *args, **kwargs)
                duration = (time.time() - start) * 1000

                # Observe
                agent_id, confidence = result if isinstance(result, tuple) else (result, 0.8)
                self.observer.observe_agent_selection(
                    intent="inferred",
                    agent_id=agent_id,
                    reason=f"Routed with confidence {confidence:.2f}",
                    candidates=[],
                )

                return result

            self.bridge.agent_manager.route = hooked_route

    def _hook_chat_controller(self):
        """Hook into chat processing."""
        # This will depend on the actual implementation
        pass

    def _hook_tool_bridge(self):
        """Hook into tool execution."""
        if hasattr(self.bridge.tool_bridge, 'execute'):
            original = self.bridge.tool_bridge.execute
            self.original_methods['tool_execute'] = original

            @functools.wraps(original)
            async def hooked_execute(tool_name: str, args: Dict, *a, **kw):
                start = time.time()
                try:
                    result = await original(tool_name, args, *a, **kw)
                    duration = (time.time() - start) * 1000

                    self.observer.observe_tool_execution(
                        tool_name=tool_name,
                        args=args,
                        result=result,
                        success=True,
                    )
                    return result

                except Exception as e:
                    self.observer.observe_tool_execution(
                        tool_name=tool_name,
                        args=args,
                        result=None,
                        success=False,
                        error=str(e),
                    )
                    raise

            self.bridge.tool_bridge.execute = hooked_execute

    async def process_with_observation(
        self,
        prompt: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Process a prompt with full pipeline observation.

        This is the main entry point for observed execution.
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        # Start trace
        trace = self.observer.start_trace(prompt)

        result = {
            "trace_id": trace.trace_id,
            "prompt": prompt,
            "success": False,
            "output": "",
            "chunks": [],
            "stages_observed": [],
            "thinking_steps": [],
            "tasks": [],
            "tools_used": [],
            "diagnostic_report": "",
        }

        try:
            # Observe parsing
            parsed = self._parse_prompt(prompt)
            self.observer.observe_parsing(prompt, parsed)
            result["stages_observed"].append("parsing")

            # Observe intent classification
            intent, confidence = await self._classify_intent(prompt)
            self.observer.observe_intent(prompt, intent, confidence)
            result["stages_observed"].append("intent")

            # Process through bridge
            chunk_count = 0
            output = ""

            async for chunk in self.bridge.chat(prompt):
                chunk_count += 1

                # Extract content
                if hasattr(chunk, 'content'):
                    content = chunk.content
                elif isinstance(chunk, str):
                    content = chunk
                elif isinstance(chunk, dict):
                    content = chunk.get('content', '')
                else:
                    content = str(chunk)

                output += content
                result["chunks"].append(content)

                # Observe streaming
                self.observer.observe_streaming_chunk(
                    chunk_number=chunk_count,
                    content=content,
                    chunk_type=self._detect_chunk_type(chunk),
                )

                # Check for thinking markers
                if '<thinking>' in content.lower() or 'thinking:' in content.lower():
                    self.observer.observe_thinking_start(content[:100])

                # Check for tool calls
                if self._is_tool_call(chunk):
                    tool_info = self._extract_tool_info(chunk)
                    result["tools_used"].append(tool_info)

                # Print live if verbose
                if verbose:
                    print(content, end="", flush=True)

            result["output"] = output
            result["success"] = True

            # End trace
            self.observer.end_trace(success=True, result=output)

        except Exception as e:
            self.observer.observe_error(
                PipelineStage.RESULT_GENERATED,
                e,
                {"prompt": prompt[:100]},
            )
            self.observer.end_trace(success=False)
            result["error"] = str(e)

        # Generate diagnostic report
        result["diagnostic_report"] = self.observer.get_current_report()
        result["trace"] = trace

        return result

    def _parse_prompt(self, prompt: str) -> Dict:
        """Parse the prompt (extract structure)."""
        return {
            "raw": prompt,
            "length": len(prompt),
            "words": len(prompt.split()),
            "has_code": '```' in prompt,
            "has_question": '?' in prompt,
            "lines": len(prompt.split('\n')),
        }

    async def _classify_intent(self, prompt: str) -> tuple:
        """Classify intent using the router if available."""
        try:
            if hasattr(self.bridge, 'agent_manager'):
                result = await self.bridge.agent_manager.route(prompt)
                if isinstance(result, tuple):
                    return result
                return (result, 0.8)
        except Exception:
            pass

        # Fallback: simple keyword-based
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ['plan', 'design', 'architect']):
            return ('planner', 0.7)
        elif any(w in prompt_lower for w in ['review', 'check', 'analyze']):
            return ('reviewer', 0.7)
        elif any(w in prompt_lower for w in ['fix', 'debug', 'error']):
            return ('debugger', 0.7)
        else:
            return ('coder', 0.6)

    def _detect_chunk_type(self, chunk: Any) -> str:
        """Detect the type of streaming chunk."""
        if hasattr(chunk, 'tool_call'):
            return 'tool_call'
        if hasattr(chunk, 'thinking'):
            return 'thinking'
        if isinstance(chunk, dict):
            if 'tool_call' in chunk:
                return 'tool_call'
            if 'thinking' in chunk:
                return 'thinking'
        return 'text'

    def _is_tool_call(self, chunk: Any) -> bool:
        """Check if chunk represents a tool call."""
        if hasattr(chunk, 'tool_call'):
            return True
        if isinstance(chunk, dict) and 'tool_call' in chunk:
            return True
        return False

    def _extract_tool_info(self, chunk: Any) -> Dict:
        """Extract tool information from chunk."""
        if hasattr(chunk, 'tool_call'):
            tc = chunk.tool_call
            return {
                'name': getattr(tc, 'name', 'unknown'),
                'args': getattr(tc, 'args', {}),
            }
        if isinstance(chunk, dict) and 'tool_call' in chunk:
            return chunk['tool_call']
        return {'name': 'unknown', 'args': {}}

    async def cleanup(self):
        """Cleanup and restore original methods."""
        # Restore original methods
        if self.bridge:
            if hasattr(self.bridge, 'agent_manager') and 'route' in self.original_methods:
                self.bridge.agent_manager.route = self.original_methods['route']
            if hasattr(self.bridge, 'tool_bridge') and 'tool_execute' in self.original_methods:
                self.bridge.tool_bridge.execute = self.original_methods['tool_execute']

            try:
                await self.bridge.shutdown()
            except Exception:
                pass


class LivePipelineMonitor:
    """
    Live monitor that displays pipeline progress in real-time.

    Shows each stage as it happens with timing and status.
    """

    def __init__(self, observer: PipelineObserver):
        self.observer = observer
        self._install_live_hooks()

    def _install_live_hooks(self):
        """Install hooks to print live updates."""
        for stage in PipelineStage:
            self.observer.add_hook(stage, self._live_update)

    def _live_update(self, observation):
        """Print live update for an observation."""
        status = "✓" if observation.success else "✗"
        stage_name = observation.stage.value.split('_', 1)[1] if '_' in observation.stage.value else observation.stage.value

        # Color coding
        if observation.success:
            color = "\033[92m"  # Green
        else:
            color = "\033[91m"  # Red
        reset = "\033[0m"

        print(f"  {color}{status}{reset} [{observation.duration_ms:6.0f}ms] {stage_name}")

        if not observation.success and observation.error:
            print(f"      └─ ERROR: {observation.error}")

        # Show key details for important stages
        if observation.stage == PipelineStage.INTENT_CLASSIFIED:
            data = observation.output_data
            if isinstance(data, dict):
                print(f"      └─ Intent: {data.get('intent')} (confidence: {data.get('confidence', 0):.1%})")

        elif observation.stage == PipelineStage.TASKS_DECOMPOSED:
            data = observation.output_data
            if isinstance(data, dict):
                count = data.get('task_count', 0)
                print(f"      └─ Tasks generated: {count}")

        elif observation.stage == PipelineStage.TOOL_EXECUTED:
            data = observation.input_data
            if isinstance(data, dict):
                print(f"      └─ Tool: {data.get('tool')}")


def create_hooked_client() -> VerticeHookedClient:
    """Create a new hooked client instance."""
    return VerticeHookedClient()


async def run_observed_test(prompt: str, verbose: bool = True) -> Dict:
    """
    Run a single observed test.

    This is the simplest way to test with full observability.
    """
    client = create_hooked_client()

    if not await client.initialize():
        return {"error": "Failed to initialize"}

    # Install live monitor
    monitor = LivePipelineMonitor(client.observer)

    print("\n" + "=" * 70)
    print("OBSERVED PIPELINE EXECUTION")
    print("=" * 70)
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print("-" * 70)

    result = await client.process_with_observation(prompt, verbose=verbose)

    print("\n" + "-" * 70)
    print("EXECUTION COMPLETE")
    print("=" * 70)

    await client.cleanup()

    return result
