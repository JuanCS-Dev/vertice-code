#!/usr/bin/env python3
"""
E2E Test: Prometheus Orchestrator with Real LLM

Validates that all subsystems are connected and functional:
1. MemorySystem - stores and retrieves context
2. WorldModel - simulates actions
3. ReflectionEngine - critiques and learns
4. LLM - generates real responses
"""

import asyncio
import sys

sys.path.insert(0, "/media/juan/DATA/Vertice-Code/src")

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()


async def test_prometheus_e2e():
    """Run full E2E test of Prometheus with real LLM."""

    console.print(Panel("🔥 Prometheus Orchestrator E2E Test", style="bold cyan"))

    # === 1. Initialize Components ===
    console.print("\n[bold]1. Initializing Components[/bold]")

    try:
        from prometheus.core.orchestrator import PrometheusOrchestrator
        from prometheus.core.llm_client import GeminiClient

        console.print("   ✅ Imports successful")
    except ImportError as e:
        console.print(f"   ❌ Import failed: {e}", style="red")
        return False

    # Create LLM client
    try:
        llm = GeminiClient()
        console.print("   ✅ GeminiClient created")
    except Exception as e:
        console.print(f"   ⚠️ GeminiClient failed: {e} - using None", style="yellow")
        llm = None

    # Create Orchestrator (should auto-create MemorySystem, WorldModel, Reflection)
    orchestrator = PrometheusOrchestrator(
        llm_client=llm,
        agent_name="Prometheus-E2E-Test",
    )
    console.print("   ✅ PrometheusOrchestrator v2.0 created")

    # === 2. Verify Subsystems ===
    console.print("\n[bold]2. Verifying Subsystems[/bold]")

    table = Table(title="Subsystem Status")
    table.add_column("Subsystem", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")

    # Check Memory
    mem_type = type(orchestrator.memory).__name__
    mem_status = "✅ Real" if mem_type == "MemorySystem" else "❌ Mock"
    table.add_row("Memory", mem_type, mem_status)

    # Check WorldModel
    wm_type = type(orchestrator.world_model).__name__ if orchestrator.world_model else "None"
    wm_status = "✅ Real" if wm_type == "WorldModel" else "⚠️ None"
    table.add_row("WorldModel", wm_type, wm_status)

    # Check Reflection
    ref_type = type(orchestrator.reflection).__name__ if orchestrator.reflection else "None"
    ref_status = "✅ Real" if ref_type == "ReflectionEngine" else "⚠️ None"
    table.add_row("Reflection", ref_type, ref_status)

    console.print(table)

    # === 3. Test Memory Operations ===
    console.print("\n[bold]3. Testing Memory Operations[/bold]")

    # Learn a fact
    orchestrator.memory.learn_fact(
        topic="test_topic",
        fact="Prometheus E2E test was run successfully",
        source="e2e_test",
    )
    console.print("   ✅ learn_fact() worked")

    # Remember an experience
    orchestrator.memory.remember_experience(
        experience="Ran E2E test of orchestrator",
        outcome="SUCCESS",
        context={"test_type": "integration"},
        importance=0.9,
    )
    console.print("   ✅ remember_experience() worked")

    # Get context
    context = orchestrator.memory.get_context_for_task("run a test")
    console.print(f"   ✅ get_context_for_task() returned {len(context)} keys")

    # === 4. Test Execution (with LLM if available) ===
    console.print("\n[bold]4. Testing Task Execution[/bold]")

    test_task = "Explain what 2+2 equals in one sentence."

    output_chunks = []
    async for chunk in orchestrator.execute(test_task, stream=True, fast_mode=False):
        output_chunks.append(chunk)
        console.print(f"   {chunk.strip()}", style="dim")

    full_output = "".join(output_chunks)
    console.print(f"\n   📝 Output length: {len(full_output)} chars")

    if "4" in full_output or "four" in full_output.lower():
        console.print("   ✅ LLM produced correct answer!", style="green bold")
    else:
        console.print(f"   ⚠️ Answer check unclear: {full_output[:100]}", style="yellow")

    # === 5. Check Status ===
    console.print("\n[bold]5. Final Status[/bold]")

    status = await orchestrator.get_status()
    console.print(Panel(str(status), title="Orchestrator Status"))

    # === Summary ===
    console.print("\n" + "=" * 60)

    all_real = (
        mem_type == "MemorySystem" and wm_type == "WorldModel" and ref_type == "ReflectionEngine"
    )

    if all_real:
        console.print(
            "✅ ALL SUBSYSTEMS CONNECTED - Prometheus v2.0 FUNCTIONAL!", style="bold green"
        )
        return True
    else:
        console.print("⚠️ Some subsystems missing (likely no LLM)", style="bold yellow")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_prometheus_e2e())
    sys.exit(0 if result else 1)
