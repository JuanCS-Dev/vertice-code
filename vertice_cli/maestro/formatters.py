"""
Maestro Output Formatters - Beautiful terminal rendering.

Rich-based formatters for plans, code, errors, and success messages.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Global console (singleton)
console = Console()

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Output format options."""

    TABLE = "table"
    JSON = "json"
    MARKDOWN = "markdown"
    PLAIN = "plain"


def render_plan(data: Dict[str, Any], format: OutputFormat = OutputFormat.TABLE) -> None:
    """Render execution plan beautifully."""
    if format == OutputFormat.TABLE:
        table = Table(
            title="Execution Plan",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Stage", style="cyan")
        table.add_column("Steps", style="white")
        table.add_column("Status", style="green")

        for idx, stage in enumerate(data.get("stages", []), 1):
            steps_list = stage.get("steps", [])
            if isinstance(steps_list, list):
                if steps_list and isinstance(steps_list[0], dict):
                    steps = "\n".join(f"- {s.get('action', s)}" for s in steps_list)
                else:
                    steps = "\n".join(f"- {s}" for s in steps_list)
            else:
                steps = str(steps_list)

            table.add_row(str(idx), stage.get("name", "Unknown"), steps, "Ready")

        console.print(table)

    elif format == OutputFormat.JSON:
        import json

        console.print_json(json.dumps(data, indent=2))

    elif format == OutputFormat.MARKDOWN:
        md = f"# {data.get('goal', 'Plan')}\n\n"
        for stage in data.get("stages", []):
            md += f"## {stage.get('name')}\n"
            for step in stage.get("steps", []):
                md += f"- {step}\n"
            md += "\n"
        console.print(Markdown(md))

    else:  # plain
        console.print(data)


def render_code(code: str, language: str = "python") -> None:
    """Render code with syntax highlighting."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"{language.upper()}", border_style="green"))


def render_error(error: str, details: Optional[str] = None) -> None:
    """Render errors beautifully."""
    console.print(f"\n[bold red]Error:[/bold red] {error}")
    if details:
        console.print(f"[dim]{details}[/dim]")
    logger.error(f"{error} | {details}")


def render_success(message: str, duration: Optional[float] = None) -> None:
    """Render success message."""
    if duration:
        console.print(f"\n[bold green]{message}[/bold green] [dim]({duration:.2f}s)[/dim]")
    else:
        console.print(f"\n[bold green]{message}[/bold green]")


def render_review_results(result: Dict[str, Any]) -> None:
    """Render code review results."""
    if "issues" in result:
        table = Table(title="Review Results", border_style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="dim")
        table.add_column("Issue", style="white")

        for issue in result.get("issues", [])[:20]:  # Limit to 20
            table.add_row(
                issue.get("severity", "UNKNOWN"),
                issue.get("file", ""),
                str(issue.get("line", "")),
                issue.get("message", "")[:60],
            )

        console.print(table)
        console.print(f"\n[dim]Score: {result.get('score', 0)}/100[/dim]")


def render_explore_map(result: Dict[str, Any]) -> None:
    """Render repository map results."""
    console.print(
        Panel(
            f"""[bold]Repository Map[/bold]

Total Entities: {result.get('total_entities', 0)}
Files: {result.get('files_analyzed', 0)}
Hotspots: {len(result.get('hotspots', []))}
Dead Code: {result.get('dead_code', 0)} entities""",
            border_style="cyan",
        )
    )

    if result.get("hotspots"):
        console.print("\n[bold yellow]Hotspots (High Coupling):[/bold yellow]")
        for hotspot in result["hotspots"][:5]:
            console.print(f"  - {hotspot}")


def render_blast_radius(result: Dict[str, Any], target: str) -> None:
    """Render blast radius analysis."""
    risk_level = result.get("risk_level", "UNKNOWN")
    border = "red" if risk_level == "HIGH" else "yellow"

    console.print(
        Panel(
            f"""[bold]Blast Radius Analysis[/bold]

Target: {target}
Risk Level: {risk_level}
Impacted Files: {len(result.get('impacted_files', []))}
Dependencies: {len(result.get('transitive_dependencies', []))}""",
            border_style=border,
        )
    )


def render_governance_status(status: Dict[str, Any]) -> None:
    """Render governance system status."""
    table = Table(title="Constitutional Governance Status", border_style="cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    table.add_row(
        "System",
        "Online" if status["initialized"] else "Offline",
        "Governance pipeline active",
    )

    table.add_row(
        "Justica (Governance)",
        "Active" if status["justica_available"] else "Unavailable",
        "Constitutional checks enabled" if status["governance_enabled"] else "Disabled",
    )

    table.add_row(
        "Sofia (Counselor)",
        "Active" if status["sofia_available"] else "Unavailable",
        "Ethical counsel enabled" if status["counsel_enabled"] else "Disabled",
    )

    table.add_row(
        "Observability",
        "Active" if status["observability_enabled"] else "Disabled",
        "OpenTelemetry tracing",
    )

    table.add_row(
        "Risk Detection",
        "Auto" if status["auto_risk_detection"] else "Manual",
        "Automatic risk level detection",
    )

    console.print(table)
