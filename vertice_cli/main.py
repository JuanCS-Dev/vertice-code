"""
Vértice - Unified Entry Point
==============================

Single command with multiple modes:
    vertice                 # Interactive TUI (default - 30 FPS)
    vertice chat "message"  # One-shot message
    vertice -p "prompt"     # Headless mode (CI/CD)
    vertice serve           # MCP server mode
    vertice shell           # Legacy shell mode

Philosophy: Sovereign Intelligence & Tactical Execution.
"""

from __future__ import annotations

import asyncio
from typing import Optional, List, TypeVar, Coroutine, Any

import typer
from rich.console import Console

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run async code safely, handling existing event loops.

    This prevents "asyncio.run() cannot be called from a running event loop"
    errors that occur when calling asyncio.run() from within an async context.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already have a loop - use run_until_complete or create_task
    if loop.is_running():
        # We're in a running loop (e.g., called from TUI)
        # Create a new loop in a new thread is one option,
        # but simpler is to use nest_asyncio or return a task
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


# Create CLI app
app = typer.Typer(
    name="vertice",
    help="Vértice - Enterprise Multi-LLM Orchestration & Agentic Intelligence",
    add_completion=True,
    invoke_without_command=True,  # Allow running without subcommand
)

console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print("[bold cyan]Vértice[/bold cyan] v1.0.0")
        console.print("[dim]Enterprise Multi-LLM Orchestration & Agentic Intelligence[/dim]")
        console.print("[dim]Operando sob a CONSTITUIÇÃO VÉRTICE v3.0[/dim]")
        console.print("\n[bold]Available Modes:[/bold]")
        console.print("  vertice          → Interactive TUI (Executor Tático)")
        console.print("  vertice -p       → Headless mode (CI/CD / Automation)")
        console.print("  vertice chat     → One-shot interaction")
        console.print("  vertice serve    → MCP Server Mode")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Option(
        None, "-p", "--prompt", help="Run in headless mode with given prompt"
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-o", help="Output format: text, json, stream-json"
    ),
    max_turns: int = typer.Option(
        10, "--max-turns", help="Maximum tool execution turns in headless mode"
    ),
    allowed_tools: Optional[List[str]] = typer.Option(
        None, "--allow-tool", help="Restrict to specific tools (can repeat)"
    ),
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Vértice - Enterprise Multi-LLM Orchestration.

    Operacional como Executor Tático sob a Constituição Vértice v3.0.

    Run without arguments to start the interactive TUI (30 FPS optimized).
    Use -p for headless mode (CI/CD, scripts, automation).

    Examples:
        vertice                           # Start TUI (Default)
        vertice -p "Check security"       # Headless one-shot
        vertice chat "Explain this code"  # Simple one-shot
        vertice status                    # Check system integrity
    """
    # Register providers with vertice_core (Dependency Injection)
    from vertice_cli.core.providers.register import ensure_providers_registered

    ensure_providers_registered()

    # If a subcommand is being invoked, skip default behavior
    if ctx.invoked_subcommand is not None:
        return

    # Headless mode
    if prompt:
        run_async(
            _run_headless(
                prompt=prompt,
                output_format=output_format,
                max_turns=max_turns,
                allowed_tools=allowed_tools,
            )
        )
        return

    # Default: Interactive TUI
    _run_tui()


def _run_tui():
    """Run the interactive Textual TUI."""
    try:
        from vertice_cli.ui_launcher import launch_tui

        launch_tui()
    except ImportError as e:
        console.print(f"[red]Error importing TUI:[/red] {e}")
        console.print("[dim]Falling back to shell_main...[/dim]")
        try:
            from vertice_cli.shell_main import main as shell_main

            run_async(shell_main())
        except ImportError:
            console.print("[red]No shell available. Install textual:[/red]")
            console.print("  pip install textual")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


async def _run_headless(
    prompt: str,
    output_format: str = "text",
    max_turns: int = 10,
    allowed_tools: Optional[List[str]] = None,
):
    """
    Run in headless mode for CI/CD and automation.

    No interactive UI - just execute and output.
    """
    import json

    try:
        from vertice_cli.ui_launcher import get_bridge

        bridge = get_bridge()

        if not bridge.is_connected:
            if output_format == "json":
                print(json.dumps({"success": False, "error": "LLM not configured"}))
            else:
                console.print("[red]Error:[/red] LLM not configured. Set GEMINI_API_KEY.")
            raise typer.Exit(1)

        # Collect response
        response_parts = []
        tool_results = []

        async for chunk in bridge.chat(prompt):
            if output_format == "stream-json":
                # Stream JSON events
                print(json.dumps({"type": "chunk", "data": chunk}))
            elif output_format == "text":
                # Print as it streams
                print(chunk, end="", flush=True)

            response_parts.append(chunk)

        full_response = "".join(response_parts)

        if output_format == "json":
            # Final JSON output
            result = {
                "success": True,
                "response": full_response,
                "tool_results": tool_results,
            }
            print(json.dumps(result, indent=2))
        elif output_format == "stream-json":
            # Final event
            print(json.dumps({"type": "complete", "success": True}))
        elif output_format == "text":
            print()  # Final newline

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
):
    """Start as MCP server."""
    console.print(f"[bold cyan]🔌 Starting MCP Server at {host}:{port}...[/bold cyan]")

    try:
        from vertice_cli.cli_mcp import main as mcp_main

        run_async(mcp_main())
    except ImportError as e:
        console.print("[red]Error:[/red] MCP dependencies not installed")
        console.print(f"[dim]Details: {e}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def shell():
    """Start interactive shell."""
    console.print("[bold cyan]🐚 Starting shell...[/bold cyan]")

    try:
        from vertice_cli.shell_main import main as shell_main

        run_async(shell_main())
    except ImportError as e:
        console.print(f"[red]Error:[/red] Shell not available: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send"),
    no_context: bool = typer.Option(False, "--no-context", help="Disable project context"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Send a single message (one-shot mode)."""
    run_async(
        _run_headless(
            prompt=message,
            output_format="json" if json_output else "text",
        )
    )


@app.command()
def status():
    """Show system status."""
    try:
        from vertice_cli.ui_launcher import get_bridge

        bridge = get_bridge()

        console.print("\n[bold cyan]Vértice System Status[/bold cyan]\n")

        # LLM Status
        if bridge.is_connected:
            console.print(f"[green]✅ LLM:[/green] Connected ({bridge.llm.model_name})")
        else:
            console.print("[red]❌ LLM:[/red] Not configured")

        # Agents
        agent_count = len(bridge.agents.available_agents)
        console.print(f"[green]🤖 Agents:[/green] {agent_count} available")

        # Tools
        tool_count = bridge.tools.get_tool_count()
        console.print(f"[green]🔧 Tools:[/green] {tool_count} loaded")

        # Governance
        gov_status = bridge.governance.get_status_emoji()
        console.print(f"[green]👀 Governance:[/green] {gov_status}")

        # Context
        context_count = len(bridge.history.context)
        console.print(f"[green]💬 Context:[/green] {context_count} messages")

        console.print()

    except Exception as e:
        console.print(f"[red]Error getting status:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def agents():
    """List available agents."""
    try:
        from vertice_cli.ui_launcher import get_agent_registry
        from rich.table import Table

        AGENT_REGISTRY = get_agent_registry()

        table = Table(title="Vértice Agent Registry")
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Capabilities", style="dim")

        for name, info in AGENT_REGISTRY.items():
            caps = ", ".join(info.capabilities[:3])
            if len(info.capabilities) > 3:
                caps += "..."
            table.add_row(name, info.role, info.description, caps)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def tools():
    """List available tools."""
    try:
        from vertice_cli.ui_launcher import get_bridge

        bridge = get_bridge()
        console.print(bridge.get_tool_list())

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def cli_main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli_main()
