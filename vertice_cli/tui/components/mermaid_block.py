"""
Mermaid Block - ASCII rendering for Mermaid diagrams.

Converts Mermaid syntax to ASCII art for terminal display.

Supported diagram types:
- flowchart/graph (TD, LR, BT, RL)
- sequence
- classDiagram
- stateDiagram
- pie
- gantt (basic)

Phase 11: Visual Upgrade - Polish & Delight.
"""

from __future__ import annotations

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

from rich.panel import Panel
from rich.text import Text
from rich import box


class DiagramType(Enum):
    """Mermaid diagram types."""

    FLOWCHART = auto()
    SEQUENCE = auto()
    CLASS = auto()
    STATE = auto()
    PIE = auto()
    GANTT = auto()
    UNKNOWN = auto()


@dataclass
class FlowNode:
    """Node in a flowchart."""

    id: str
    label: str
    shape: str = "rect"  # rect, rounded, diamond, circle


@dataclass
class FlowEdge:
    """Edge in a flowchart."""

    from_node: str
    to_node: str
    label: str = ""
    style: str = "-->"  # -->, ---, -.->


class MermaidParser:
    """Parse Mermaid diagram syntax."""

    # Pattern to detect diagram type
    TYPE_PATTERNS = {
        DiagramType.FLOWCHART: re.compile(r"^(flowchart|graph)\s+(TD|TB|LR|RL|BT)", re.MULTILINE),
        DiagramType.SEQUENCE: re.compile(r"^sequenceDiagram", re.MULTILINE),
        DiagramType.CLASS: re.compile(r"^classDiagram", re.MULTILINE),
        DiagramType.STATE: re.compile(r"^stateDiagram", re.MULTILINE),
        DiagramType.PIE: re.compile(r"^pie", re.MULTILINE),
        DiagramType.GANTT: re.compile(r"^gantt", re.MULTILINE),
    }

    # Flowchart node shapes
    NODE_PATTERNS = [
        (r"\[([^\]]+)\]", "rect"),  # [label]
        (r"\(([^\)]+)\)", "rounded"),  # (label)
        (r"\{([^\}]+)\}", "diamond"),  # {label}
        (r"\(\(([^\)]+)\)\)", "circle"),  # ((label))
    ]

    # Edge patterns
    EDGE_PATTERN = re.compile(
        r"(\w+)\s*"  # from node
        r"(-->|---|-\.->|==>)"  # edge type
        r"\s*(\|[^|]+\|)?\s*"  # optional label
        r"(\w+)"  # to node
    )

    @classmethod
    def detect_type(cls, diagram: str) -> DiagramType:
        """Detect diagram type from content."""
        for dtype, pattern in cls.TYPE_PATTERNS.items():
            if pattern.search(diagram):
                return dtype
        return DiagramType.UNKNOWN

    @classmethod
    def parse_flowchart(cls, diagram: str) -> Tuple[List[FlowNode], List[FlowEdge], str]:
        """Parse flowchart diagram."""
        nodes: dict[str, FlowNode] = {}
        edges: List[FlowEdge] = []
        direction = "TD"

        lines = diagram.strip().split("\n")

        # Get direction from first line
        first_line = lines[0].strip()
        match = re.search(r"(TD|TB|LR|RL|BT)", first_line)
        if match:
            direction = match.group(1)

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("%%"):
                continue

            # Parse edges
            edge_match = cls.EDGE_PATTERN.search(line)
            if edge_match:
                from_id = edge_match.group(1)
                edge_style = edge_match.group(2)
                label = (edge_match.group(3) or "").strip("|")
                to_id = edge_match.group(4)

                edges.append(FlowEdge(from_id, to_id, label, edge_style))

                # Create nodes if not exist
                if from_id not in nodes:
                    nodes[from_id] = FlowNode(from_id, from_id)
                if to_id not in nodes:
                    nodes[to_id] = FlowNode(to_id, to_id)

            # Parse node definitions
            for pattern, shape in cls.NODE_PATTERNS:
                node_match = re.search(r"^(\w+)" + pattern, line)
                if node_match:
                    node_id = node_match.group(1)
                    label = node_match.group(2)
                    nodes[node_id] = FlowNode(node_id, label, shape)
                    break

        return list(nodes.values()), edges, direction


class MermaidAsciiRenderer:
    """Render Mermaid diagrams as ASCII art."""

    # Box drawing characters
    HORIZONTAL = "─"
    VERTICAL = "│"
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"
    ARROW_LEFT = "←"
    ARROW_UP = "↑"

    @classmethod
    def render(cls, diagram: str) -> str:
        """Render any Mermaid diagram to ASCII."""
        dtype = MermaidParser.detect_type(diagram)

        if dtype == DiagramType.FLOWCHART:
            return cls._render_flowchart(diagram)
        elif dtype == DiagramType.SEQUENCE:
            return cls._render_sequence(diagram)
        elif dtype == DiagramType.CLASS:
            return cls._render_class(diagram)
        elif dtype == DiagramType.PIE:
            return cls._render_pie(diagram)
        elif dtype == DiagramType.STATE:
            return cls._render_state(diagram)
        else:
            return cls._render_fallback(diagram)

    @classmethod
    def _render_flowchart(cls, diagram: str) -> str:
        """Render flowchart as ASCII."""
        nodes, edges, direction = MermaidParser.parse_flowchart(diagram)

        if not nodes:
            return cls._render_fallback(diagram)

        lines = ["[Flowchart]", ""]

        # Simple vertical rendering for TD/TB
        if direction in ("TD", "TB"):
            for edge in edges:
                from_node = next((n for n in nodes if n.id == edge.from_node), None)
                to_node = next((n for n in nodes if n.id == edge.to_node), None)

                if from_node and to_node:
                    # Draw from node
                    lines.append(cls._box(from_node.label, from_node.shape))
                    lines.append("    │")
                    if edge.label:
                        lines.append(f"    │ {edge.label}")
                    lines.append("    ↓")

            # Draw last node
            if edges:
                last_edge = edges[-1]
                to_node = next((n for n in nodes if n.id == last_edge.to_node), None)
                if to_node:
                    lines.append(cls._box(to_node.label, to_node.shape))

        # Horizontal rendering for LR
        elif direction == "LR":
            row = []
            for edge in edges:
                from_node = next((n for n in nodes if n.id == edge.from_node), None)
                if from_node:
                    row.append(f"[{from_node.label}]")
                    if edge.label:
                        row.append(f"--{edge.label}-->")
                    else:
                        row.append("-->")

            if edges:
                to_node = next((n for n in nodes if n.id == edges[-1].to_node), None)
                if to_node:
                    row.append(f"[{to_node.label}]")

            lines.append(" ".join(row))

        return "\n".join(lines)

    @classmethod
    def _box(cls, label: str, shape: str = "rect") -> str:
        """Draw a box around label."""
        width = len(label) + 4

        if shape == "diamond":
            return f"   ◇ {label} ◇"
        elif shape == "circle":
            return f"   ○ {label} ○"
        elif shape == "rounded":
            return f"   ({label})"
        else:  # rect
            top = cls.TOP_LEFT + cls.HORIZONTAL * (width - 2) + cls.TOP_RIGHT
            mid = cls.VERTICAL + f" {label} " + cls.VERTICAL
            bot = cls.BOTTOM_LEFT + cls.HORIZONTAL * (width - 2) + cls.BOTTOM_RIGHT
            return f"  {top}\n  {mid}\n  {bot}"

    @classmethod
    def _render_sequence(cls, diagram: str) -> str:
        """Render sequence diagram as ASCII."""
        lines = ["[Sequence Diagram]", ""]

        participants = []
        messages = []

        for line in diagram.strip().split("\n")[1:]:
            line = line.strip()
            if not line or line.startswith("%%"):
                continue

            # participant
            if line.startswith("participant"):
                name = line.replace("participant", "").strip()
                participants.append(name)

            # message arrow
            match = re.search(r"(\w+)\s*(->>|-->>|->|-->)\s*(\w+)\s*:\s*(.+)", line)
            if match:
                from_p, arrow, to_p, msg = match.groups()
                messages.append((from_p, to_p, msg, "--" in arrow))

        # Draw participants
        if participants:
            lines.append("  " + "    ".join(f"[{p}]" for p in participants))
            lines.append("  " + "    ".join("  │  " for _ in participants))

        # Draw messages
        for from_p, to_p, msg, dashed in messages:
            arrow = "- - ->" if dashed else "─────>"
            lines.append(f"  {from_p} {arrow} {to_p}: {msg}")

        return "\n".join(lines)

    @classmethod
    def _render_class(cls, diagram: str) -> str:
        """Render class diagram as ASCII."""
        lines = ["[Class Diagram]", ""]

        classes = []
        for line in diagram.strip().split("\n")[1:]:
            line = line.strip()
            if line.startswith("class "):
                class_name = line.replace("class ", "").split("{")[0].strip()
                classes.append(class_name)

        for class_name in classes:
            lines.append(f"  ┌{'─' * (len(class_name) + 2)}┐")
            lines.append(f"  │ {class_name} │")
            lines.append(f"  └{'─' * (len(class_name) + 2)}┘")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _render_pie(cls, diagram: str) -> str:
        """Render pie chart as ASCII."""
        lines = ["[Pie Chart]", ""]

        title = ""
        slices = []

        for line in diagram.strip().split("\n")[1:]:
            line = line.strip()
            if line.startswith("title"):
                title = line.replace("title", "").strip()
            elif ":" in line:
                match = re.search(r'"([^"]+)"\s*:\s*(\d+)', line)
                if match:
                    slices.append((match.group(1), int(match.group(2))))

        if title:
            lines.append(f"  {title}")
            lines.append("")

        total = sum(v for _, v in slices)
        for label, value in slices:
            pct = (value / total * 100) if total > 0 else 0
            bar_len = int(pct / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {label}: {bar} {pct:.1f}%")

        return "\n".join(lines)

    @classmethod
    def _render_state(cls, diagram: str) -> str:
        """Render state diagram as ASCII."""
        lines = ["[State Diagram]", ""]

        states = []
        transitions = []

        for line in diagram.strip().split("\n")[1:]:
            line = line.strip()
            if not line or line.startswith("%%"):
                continue

            match = re.search(r"(\w+|\[\*\])\s*-->\s*(\w+|\[\*\])\s*:?\s*(.*)", line)
            if match:
                from_s, to_s, label = match.groups()
                transitions.append((from_s, to_s, label.strip()))

                if from_s not in states and from_s != "[*]":
                    states.append(from_s)
                if to_s not in states and to_s != "[*]":
                    states.append(to_s)

        for from_s, to_s, label in transitions:
            from_display = "●" if from_s == "[*]" else f"({from_s})"
            to_display = "●" if to_s == "[*]" else f"({to_s})"
            if label:
                lines.append(f"  {from_display} ──{label}──→ {to_display}")
            else:
                lines.append(f"  {from_display} ────────→ {to_display}")

        return "\n".join(lines)

    @classmethod
    def _render_fallback(cls, diagram: str) -> str:
        """Fallback for unsupported diagrams."""
        lines = ["[Mermaid Diagram]", ""]
        for line in diagram.strip().split("\n"):
            lines.append(f"  {line}")
        return "\n".join(lines)


class MermaidBlock(Widget):
    """
    Widget for displaying Mermaid diagrams as ASCII.

    Features:
    - Auto-detect diagram type
    - ASCII rendering
    - Collapsible source view
    """

    DEFAULT_CSS = """
    MermaidBlock {
        width: 100%;
        height: auto;
        margin: 1 0;
    }

    MermaidBlock .mermaid-content {
        padding: 1;
        background: $surface;
        border: solid $border;
    }

    MermaidBlock .mermaid-header {
        background: $panel;
        padding: 0 1;
        height: 1;
    }
    """

    show_source: reactive[bool] = reactive(False)

    def __init__(
        self,
        diagram: str,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._diagram = diagram
        self._ascii = MermaidAsciiRenderer.render(diagram)

    def compose(self):
        yield Static("📊 Mermaid Diagram", classes="mermaid-header")
        yield Static(self._ascii, classes="mermaid-content")

    def toggle_source(self) -> None:
        """Toggle between ASCII and source view."""
        self.show_source = not self.show_source
        content = self.query_one(".mermaid-content", Static)
        if self.show_source:
            content.update(self._diagram)
        else:
            content.update(self._ascii)


def render_mermaid(diagram: str) -> str:
    """Convenience function to render Mermaid as ASCII."""
    return MermaidAsciiRenderer.render(diagram)


def create_mermaid_panel(diagram: str, title: str = "Diagram") -> Panel:
    """Create a Rich Panel with rendered Mermaid."""
    ascii_art = MermaidAsciiRenderer.render(diagram)
    return Panel(
        Text(ascii_art),
        title=f"[bold cyan]📊 {title}[/]",
        border_style="cyan",
        box=box.ROUNDED,
    )
