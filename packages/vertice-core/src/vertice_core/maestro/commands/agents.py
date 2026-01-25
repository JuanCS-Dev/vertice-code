"""
Maestro Agent Commands - Agent operation CLI commands.

Commands for plan, review, explore, sofia, and governance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from async_typer import AsyncTyper

from vertice_core.maestro_governance import render_sofia_counsel

from ..bootstrap import ensure_initialized
from ..executor import execute_agent_task
from ..formatters import (
    OutputFormat,
    console,
    render_blast_radius,
    render_error,
    render_explore_map,
    render_governance_status,
    render_plan,
    render_review_results,
)
from ..state import state

logger = logging.getLogger(__name__)

# Sub-app for agent commands
agent_app = AsyncTyper(help="Agent commands")


@agent_app.async_command("plan")
async def agent_plan(
    goal: Annotated[str, typer.Argument(help="What do you want to accomplish?")],
    output: Annotated[
        OutputFormat, typer.Option("--output", "-o", help="Output format")
    ] = OutputFormat.TABLE,
    context_file: Annotated[
        Optional[Path], typer.Option("--context", "-c", help="Context file")
    ] = None,
) -> None:
    """
    Generate execution plan using the Planner agent.

    Example:
        maestro agent plan "Implement user authentication with JWT"
        maestro agent plan "Refactor database layer" --output json
    """
    await ensure_initialized()

    context = {}
    if context_file and context_file.exists():
        pass  # Load context from file

    result = await execute_agent_task("planner", goal, context)
    render_plan(result, output)


@agent_app.async_command("review")
async def agent_review(
    target: Annotated[str, typer.Argument(help="File or directory to review")],
    deep: Annotated[bool, typer.Option("--deep", help="Deep analysis mode")] = False,
    fix: Annotated[bool, typer.Option("--fix", help="Auto-fix issues")] = False,
) -> None:
    """
    Review code using the Reviewer agent.

    Example:
        maestro agent review src/auth.py
        maestro agent review . --deep
    """
    await ensure_initialized()

    target_path = Path(target)
    if not target_path.exists():
        render_error(f"Path not found: {target}")
        raise typer.Exit(1)

    context = {"files": [str(target_path)], "deep_mode": deep, "auto_fix": fix}

    result = await execute_agent_task("reviewer", f"Review {target}", context)
    render_review_results(result)


@agent_app.async_command("explore")
async def agent_explore(
    operation: Annotated[
        str, typer.Argument(help="Operation: map, blast-radius, search, insights")
    ],
    target: Annotated[Optional[str], typer.Argument(help="Target entity/file")] = None,
    root: Annotated[Path, typer.Option("--root", "-r", help="Repository root")] = Path("."),
) -> None:
    """
    Explore codebase using the Explorer agent.

    Operations:
        map          - Build repository knowledge graph
        blast-radius - Analyze impact of changes
        search       - Semantic code search
        insights     - Generate architectural insights

    Example:
        maestro agent explore map
        maestro agent explore blast-radius "authenticate_user"
        maestro agent explore search "database transaction handlers"
    """
    await ensure_initialized()

    context = {"operation": operation, "root_dir": str(root)}

    if target:
        context["target"] = target

    prompt = f"{operation} {target or ''}"
    result = await execute_agent_task("explorer", prompt, context)

    # Render based on operation
    if operation == "map":
        render_explore_map(result)
    elif operation == "blast-radius":
        render_blast_radius(result, target or "")
    else:
        console.print(result)


@agent_app.async_command("sofia")
async def agent_sofia(
    question: Annotated[
        str, typer.Argument(help="Ethical question or dilemma to consult Sofia about")
    ],
) -> None:
    """
    Consult Sofia (Wise Counselor) for ethical guidance.

    Sofia provides philosophical counsel using Socratic method and virtue ethics
    from Early Christianity (Pre-Nicene, 50-325 AD).

    Example:
        maestro agent sofia "Should I implement aggressive caching that might compromise user privacy?"
        maestro agent sofia "How do I balance feature velocity with code quality?"
    """
    await ensure_initialized()

    if not state.governance:
        render_error("Sofia not available", "Governance system not initialized")
        raise typer.Exit(1)

    console.print("\n[bold magenta]Consulting Sofia (Wise Counselor)...[/bold magenta]")
    console.print(
        "[dim]Sofia will deliberate on your question using virtue ethics and Socratic method[/dim]\n"
    )

    try:
        result = await state.governance.ask_sofia(question)
        render_sofia_counsel(result)

    except Exception as e:
        render_error("Sofia consultation failed", str(e))
        logger.exception("Sofia command error")
        raise typer.Exit(1)


@agent_app.async_command("governance")
async def agent_governance_status() -> None:
    """
    Show governance system status.

    Displays status of Justica (governance) and Sofia (counselor) systems,
    including configuration and availability.

    Example:
        maestro agent governance
    """
    await ensure_initialized()

    if not state.governance:
        console.print("[yellow]Governance system not initialized[/yellow]")
        raise typer.Exit(1)

    status = state.governance.get_governance_status()
    render_governance_status(status)

    # Show usage hint
    console.print("\n[dim]Commands:[/dim]")
    console.print(
        '[dim]  - maestro agent sofia "<question>"  - Consult Sofia for ethical guidance[/dim]'
    )
    console.print("[dim]  - maestro agent plan/review/explore  - All protected by governance[/dim]")
