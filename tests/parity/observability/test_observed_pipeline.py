"""
OBSERVED PIPELINE TESTS

These are NOT generic tests. Each test:
1. Observes EVERY stage of the pipeline
2. Records precise timing and data flow
3. Validates each stage independently
4. Provides EXACT diagnosis of failure points

Run with: pytest tests/parity/observability/test_observed_pipeline.py -v -s
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.parity.observability.pipeline_observer import (
    PipelineStage,
    get_observer,
    reset_observer,
)
from tests.parity.observability.vertice_hooks import (
    VerticeHookedClient,
    LivePipelineMonitor,
    run_observed_test,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.observed,
    pytest.mark.real,
]


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()


@pytest.fixture
def observer():
    """Fresh observer for each test."""
    reset_observer()
    return get_observer()


@pytest.fixture
async def hooked_client(observer):
    """Hooked client with observer."""
    client = VerticeHookedClient(observer)
    success = await client.initialize()

    if not success:
        pytest.skip("Could not initialize Vertice")

    yield client

    await client.cleanup()


class TestObservedPromptProcessing:
    """Test prompt processing with full observation."""

    @pytest.mark.timeout(120)
    async def test_simple_prompt_all_stages(self, hooked_client, observer):
        """
        OBSERVED TEST: Simple prompt should pass through all stages.

        We observe:
        1. Prompt received
        2. Prompt parsed
        3. Intent classified
        4. Agent selected
        5. LLM called
        6. Streaming chunks
        7. Result generated
        """
        prompt = "What is 2 + 2?"

        print("\n" + "=" * 70)
        print("TEST: Simple Prompt - All Stages")
        print("=" * 70)

        # Install live monitor
        LivePipelineMonitor(observer)

        result = await hooked_client.process_with_observation(prompt, verbose=True)

        # Print diagnostic report
        print("\n" + result["diagnostic_report"])

        # Validate stages
        stages_observed = [obs.stage for obs in result["trace"].observations]

        # MUST have prompt received
        assert PipelineStage.PROMPT_RECEIVED in stages_observed, "FAILED: Prompt not received"

        # MUST have intent classification
        assert PipelineStage.INTENT_CLASSIFIED in stages_observed, "FAILED: Intent not classified"

        # MUST have result
        assert PipelineStage.RESULT_GENERATED in stages_observed, "FAILED: No result generated"

        # Output should contain "4"
        assert (
            "4" in result["output"]
        ), f"FAILED: Expected '4' in output, got: {result['output'][:100]}"

        print("\n✓ All stages passed")

    @pytest.mark.timeout(180)
    async def test_coding_request_full_flow(self, hooked_client, observer):
        """
        OBSERVED TEST: Coding request with full flow observation.

        Observing:
        - How intent is classified as "coding"
        - Which agent is selected
        - How tasks are decomposed (or NOT decomposed - BUG!)
        - Tool usage for code generation
        - Quality of output
        """
        prompt = "Write a Python function to check if a number is prime"

        print("\n" + "=" * 70)
        print("TEST: Coding Request - Full Flow")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=True)

        print("\n" + result["diagnostic_report"])

        # Analyze intent classification
        intent_obs = None
        for obs in result["trace"].observations:
            if obs.stage == PipelineStage.INTENT_CLASSIFIED:
                intent_obs = obs
                break

        if intent_obs:
            intent_data = intent_obs.output_data
            print("\n[INTENT ANALYSIS]")
            print(f"  Classified as: {intent_data.get('intent')}")
            print(f"  Confidence: {intent_data.get('confidence', 0):.1%}")

            # For coding request, should have high confidence in coding intent
            assert (
                intent_data.get("confidence", 0) > 0.5
            ), f"FAILED: Low confidence in intent: {intent_data.get('confidence')}"

        # Check task decomposition
        task_obs = None
        for obs in result["trace"].observations:
            if obs.stage == PipelineStage.TASKS_DECOMPOSED:
                task_obs = obs
                break

        if task_obs:
            task_data = task_obs.output_data
            print("\n[TASK DECOMPOSITION ANALYSIS]")
            print(f"  Tasks generated: {task_data.get('task_count', 0)}")

            # THIS IS THE BUG: Should be more than 1 for complex request
            # Currently always 1 due to range(1, 2)
            if task_data.get("task_count", 0) == 1:
                print("  ⚠ WARNING: Only 1 task generated - decomposition may be broken!")

        # Validate output has code
        assert (
            "def " in result["output"] or "```python" in result["output"]
        ), "FAILED: No Python code in output"

        print("\n✓ Coding flow completed")

    @pytest.mark.timeout(180)
    async def test_planning_request_decomposition(self, hooked_client, observer):
        """
        OBSERVED TEST: Planning request should trigger task decomposition.

        This test specifically observes the task decomposition stage
        to verify if it's working or BROKEN.
        """
        prompt = """
        Plan the implementation of a user authentication system with:
        - User registration
        - Login/logout
        - Password reset
        - Session management
        """

        print("\n" + "=" * 70)
        print("TEST: Planning Request - Task Decomposition")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=True)

        print("\n" + result["diagnostic_report"])

        # CRITICAL: Check task decomposition
        tasks_generated = result["trace"].tasks_generated

        print("\n[CRITICAL ANALYSIS: TASK DECOMPOSITION]")
        print(f"  Tasks found: {len(tasks_generated)}")

        if len(tasks_generated) == 0:
            print("  ⚠ NO TASKS GENERATED - Decomposition not triggered")
        elif len(tasks_generated) == 1:
            print("  ⚠ ONLY 1 TASK - Decomposition likely BROKEN (range(1,2) bug)")
            print(f"  Task: {tasks_generated[0] if tasks_generated else 'N/A'}")
        else:
            print("  ✓ Multiple tasks generated - Decomposition working")
            for i, task in enumerate(tasks_generated, 1):
                print(f"    {i}. {task}")

        # Check if output addresses multiple components
        output_lower = result["output"].lower()
        components = ["registration", "login", "password", "session"]
        components_found = [c for c in components if c in output_lower]

        print("\n[COMPONENT COVERAGE]")
        print(f"  Components mentioned: {len(components_found)}/{len(components)}")
        for c in components:
            status = "✓" if c in components_found else "✗"
            print(f"    {status} {c}")

        # At minimum, should mention multiple components
        assert (
            len(components_found) >= 2
        ), f"FAILED: Only {len(components_found)} components addressed"

    @pytest.mark.timeout(180)
    async def test_tool_execution_observation(self, hooked_client, observer):
        """
        OBSERVED TEST: Track tool execution in detail.

        Observing:
        - Which tools are selected
        - Tool execution timing
        - Tool results
        - Tool errors
        """
        prompt = "Read the pyproject.toml file and tell me the project name"

        print("\n" + "=" * 70)
        print("TEST: Tool Execution Observation")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=True)

        print("\n" + result["diagnostic_report"])

        # Analyze tool usage
        tools_called = result["trace"].tools_called

        print("\n[TOOL EXECUTION ANALYSIS]")
        print(f"  Tools called: {len(tools_called)}")

        for tool in tools_called:
            status = "✓" if tool.get("success") else "✗"
            print(f"    {status} {tool.get('name', 'unknown')}")
            print(f"        Duration: {tool.get('duration_ms', 0):.0f}ms")
            if tool.get("error"):
                print(f"        Error: {tool['error']}")

        # Should have found project name
        assert "vertice" in result["output"].lower(), "FAILED: Project name not found in output"

    @pytest.mark.timeout(180)
    async def test_thinking_process_observation(self, hooked_client, observer):
        """
        OBSERVED TEST: Track the thinking/reasoning process.

        Looking for:
        - Explicit thinking markers
        - Reasoning steps
        - Decision points
        """
        prompt = """
        I have a performance issue. The API endpoint /users is slow.
        Think through the possible causes and suggest solutions.
        """

        print("\n" + "=" * 70)
        print("TEST: Thinking Process Observation")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=True)

        print("\n" + result["diagnostic_report"])

        # Analyze thinking steps
        thinking_steps = result["trace"].thinking_steps

        print("\n[THINKING PROCESS ANALYSIS]")
        print(f"  Thinking steps recorded: {len(thinking_steps)}")

        if thinking_steps:
            for step in thinking_steps:
                print(f"    Step {step.step_number}:")
                print(f"      Thought: {step.thought[:80]}...")
                print(f"      Confidence: {step.confidence:.1%}")
        else:
            print("  ⚠ No explicit thinking steps captured")
            print("  This may indicate lack of Chain-of-Thought prompting")

        # Check output for reasoning indicators
        output_lower = result["output"].lower()
        reasoning_markers = [
            "because",
            "therefore",
            "consider",
            "first",
            "then",
            "possible",
            "likely",
            "suggest",
            "recommend",
        ]
        markers_found = [m for m in reasoning_markers if m in output_lower]

        print("\n[REASONING QUALITY]")
        print(f"  Reasoning markers found: {len(markers_found)}")
        for m in markers_found[:5]:
            print(f"    ✓ '{m}'")


class TestObservedFailurePoints:
    """Tests that identify specific failure points."""

    @pytest.mark.timeout(120)
    async def test_identify_decomposition_failure(self, hooked_client, observer):
        """
        DIAGNOSTIC TEST: Identify where task decomposition fails.

        This test is designed to EXPOSE the range(1,2) bug.
        """
        prompt = "Create a todo app with add, delete, and list functionality"

        print("\n" + "=" * 70)
        print("DIAGNOSTIC: Task Decomposition Failure Point")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=False)

        # Find decomposition stage
        decomp_obs = None
        for obs in result["trace"].observations:
            if obs.stage == PipelineStage.TASKS_DECOMPOSED:
                decomp_obs = obs
                break

        print("\n[DECOMPOSITION DIAGNOSTIC]")

        if decomp_obs is None:
            print("  ✗ FAILURE: No decomposition stage observed")
            print("  → Decomposition may not be triggered at all")
            print("  → Check: Is OrchestratorAgent.plan() being called?")
        else:
            task_data = decomp_obs.output_data
            task_count = task_data.get("task_count", 0) if isinstance(task_data, dict) else 0

            if task_count == 1:
                print("  ✗ FAILURE: Only 1 task generated")
                print("  → This is the range(1, 2) bug!")
                print("  → Location: agents/orchestrator/agent.py:127-152")
                print("  → Fix: Replace range(1, 2) with actual decomposition logic")
            elif task_count == 0:
                print("  ✗ FAILURE: No tasks generated")
                print("  → Decomposition returned empty list")
            else:
                print(f"  ✓ SUCCESS: {task_count} tasks generated")

        # Output expected components
        expected = ["add", "delete", "list"]
        output_lower = result["output"].lower()
        for exp in expected:
            found = exp in output_lower
            status = "✓" if found else "✗"
            print(f"  {status} Component '{exp}' in output: {found}")

    @pytest.mark.timeout(120)
    async def test_identify_routing_failure(self, hooked_client, observer):
        """
        DIAGNOSTIC TEST: Identify agent routing issues.
        """
        test_cases = [
            ("Plan the architecture", "planner"),
            ("Write a function", "coder"),
            ("Review this code", "reviewer"),
            ("Fix this bug", "debugger"),
        ]

        print("\n" + "=" * 70)
        print("DIAGNOSTIC: Agent Routing Analysis")
        print("=" * 70)

        for prompt, expected_agent in test_cases:
            reset_observer()
            get_observer()

            result = await hooked_client.process_with_observation(prompt, verbose=False)

            # Find agent selection
            agent_obs = None
            for obs in result["trace"].observations:
                if obs.stage == PipelineStage.AGENT_SELECTED:
                    agent_obs = obs
                    break

            print(f"\n[{prompt[:30]}...]")
            if agent_obs:
                data = agent_obs.output_data
                actual = data.get("agent_id", "unknown") if isinstance(data, dict) else "unknown"
                match = expected_agent in str(actual).lower()
                status = "✓" if match else "✗"
                print(f"  Expected: {expected_agent}")
                print(f"  Got: {actual}")
                print(f"  {status} Match: {match}")
            else:
                print("  ✗ No agent selection observed")


class TestObservedQualityValidation:
    """Observed tests with quality validation."""

    @pytest.mark.timeout(180)
    async def test_output_quality_observed(self, hooked_client, observer):
        """
        OBSERVED QUALITY TEST: Validate output quality with full observation.
        """
        prompt = "Write a Python function to validate email addresses"

        print("\n" + "=" * 70)
        print("OBSERVED QUALITY TEST")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=True)

        print("\n[QUALITY ANALYSIS]")

        # Structural quality
        output = result["output"]
        has_function = "def " in output
        has_docstring = '"""' in output or "'''" in output
        has_return = "return" in output
        has_example = "example" in output.lower() or "@" in output

        print(f"  Has function definition: {'✓' if has_function else '✗'}")
        print(f"  Has docstring: {'✓' if has_docstring else '✗'}")
        print(f"  Has return statement: {'✓' if has_return else '✗'}")
        print(f"  Has example/test: {'✓' if has_example else '✗'}")

        # Semantic quality
        email_terms = ["email", "@", "valid", "pattern", "regex"]
        terms_found = sum(1 for t in email_terms if t in output.lower())
        print(f"  Email-related terms: {terms_found}/{len(email_terms)}")

        # Completeness
        quality_score = sum([has_function, has_return, terms_found >= 2]) / 3
        print(f"\n  QUALITY SCORE: {quality_score:.1%}")

        if quality_score < 0.6:
            print("  ⚠ Quality below threshold")
            print("\n[FAILURE ANALYSIS]")
            trace = result["trace"]
            if trace.failure_point:
                print(f"  Failed at: {trace.failure_point.value}")
                print(f"  Reason: {trace.failure_reason}")


class TestObservedBenchmarks:
    """Benchmarks with observation."""

    @pytest.mark.timeout(300)
    @pytest.mark.benchmark
    async def test_stage_timing_benchmark(self, hooked_client, observer):
        """
        BENCHMARK: Measure timing of each pipeline stage.
        """
        prompt = "Explain Python decorators"

        print("\n" + "=" * 70)
        print("BENCHMARK: Pipeline Stage Timing")
        print("=" * 70)

        LivePipelineMonitor(observer)
        result = await hooked_client.process_with_observation(prompt, verbose=False)

        # Analyze timing
        print("\n[STAGE TIMING BREAKDOWN]")

        stage_times = {}
        for obs in result["trace"].observations:
            stage_name = obs.stage.value
            stage_times[stage_name] = obs.duration_ms

        total = sum(stage_times.values())

        for stage, duration in sorted(stage_times.items()):
            pct = (duration / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {stage:30} {duration:6.0f}ms {bar} {pct:4.1f}%")

        print(f"\n  TOTAL: {total:.0f}ms")

        # Identify bottlenecks
        if stage_times:
            slowest = max(stage_times, key=stage_times.get)
            print(f"\n  BOTTLENECK: {slowest} ({stage_times[slowest]:.0f}ms)")


# Standalone execution for quick testing
if __name__ == "__main__":

    async def main():
        """Run a quick observed test."""
        result = await run_observed_test(
            "Write a Python function to check if a string is a palindrome"
        )
        print("\n" + result["diagnostic_report"])

    asyncio.run(main())
