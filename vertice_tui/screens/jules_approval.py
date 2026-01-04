"""
Jules Plan Approval Screen.

Modal dialog for reviewing and approving Jules execution plans.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown, Static

from vertice_core.types.jules_types import JulesSession


class JulesPlanApprovalScreen(ModalScreen[bool]):
    """
    Modal screen for reviewing and approving Jules plans.

    Features:
    - Plan summary with steps
    - Files to be modified/created
    - Approve/Reject buttons
    - Keyboard shortcuts

    Usage:
        approved = await app.push_screen_wait(JulesPlanApprovalScreen(session))
        if approved:
            await client.approve_plan(session.session_id)
    """

    BINDINGS = [
        Binding("escape", "reject", "Reject"),
        Binding("enter", "approve", "Approve"),
        Binding("y", "approve", "Yes"),
        Binding("n", "reject", "No"),
    ]

    DEFAULT_CSS = """
    JulesPlanApprovalScreen {
        align: center middle;
    }

    JulesPlanApprovalScreen > Vertical {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $warning;
        padding: 1 2;
    }

    JulesPlanApprovalScreen .title {
        text-align: center;
        text-style: bold;
        color: $warning;
        padding: 1 0;
    }

    JulesPlanApprovalScreen .subtitle {
        text-align: center;
        color: $text-muted;
        padding: 0 0 1 0;
    }

    JulesPlanApprovalScreen .plan-content {
        height: auto;
        max-height: 20;
        background: $panel;
        border: solid $border;
        padding: 1;
        margin: 1 0;
    }

    JulesPlanApprovalScreen .files-section {
        height: auto;
        padding: 1 0;
    }

    JulesPlanApprovalScreen .files-header {
        text-style: bold;
        color: $accent;
        padding: 0 0 0 1;
    }

    JulesPlanApprovalScreen .file-list {
        padding-left: 2;
        color: $text;
    }

    JulesPlanApprovalScreen .file-create {
        color: #22C55E;
    }

    JulesPlanApprovalScreen .file-modify {
        color: #F59E0B;
    }

    JulesPlanApprovalScreen .buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    JulesPlanApprovalScreen Button {
        margin: 0 2;
        min-width: 15;
    }

    JulesPlanApprovalScreen Button.approve {
        background: $success;
    }

    JulesPlanApprovalScreen Button.reject {
        background: $error;
    }

    JulesPlanApprovalScreen .warning {
        text-align: center;
        color: $warning;
        padding: 1 0;
    }
    """

    def __init__(self, session: JulesSession) -> None:
        super().__init__()
        self.session = session
        self.plan = session.plan

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(" Jules Plan Approval Required", classes="title")
            yield Label(
                f"Session: {self.session.title or self.session.session_id[:12]}",
                classes="subtitle",
            )

            # Plan content
            with ScrollableContainer(classes="plan-content"):
                if self.plan:
                    yield Markdown(self._format_plan())
                else:
                    yield Static("No plan details available.")

            # Files section
            if self.plan:
                with Vertical(classes="files-section"):
                    # Files to create
                    if self.plan.files_to_create:
                        yield Static("Files to Create:", classes="files-header")
                        for f in self.plan.files_to_create[:8]:
                            yield Static(f"  + {f}", classes="file-list file-create")
                        if len(self.plan.files_to_create) > 8:
                            yield Static(
                                f"  ... and {len(self.plan.files_to_create) - 8} more",
                                classes="file-list",
                            )

                    # Files to modify
                    if self.plan.files_to_modify:
                        yield Static("Files to Modify:", classes="files-header")
                        for f in self.plan.files_to_modify[:8]:
                            yield Static(f"  ~ {f}", classes="file-list file-modify")
                        if len(self.plan.files_to_modify) > 8:
                            yield Static(
                                f"  ... and {len(self.plan.files_to_modify) - 8} more",
                                classes="file-list",
                            )

            # Warning
            yield Static(
                "Review carefully before approving execution.",
                classes="warning",
            )

            # Buttons
            with Horizontal(classes="buttons"):
                yield Button(" Approve (Y)", id="approve", classes="approve")
                yield Button(" Reject (N)", id="reject", classes="reject")

    def _format_plan(self) -> str:
        """Format plan as markdown."""
        if not self.plan:
            return "No plan available."

        lines = ["## Execution Plan\n"]

        if self.plan.estimated_duration:
            lines.append(f"**Estimated Duration:** {self.plan.estimated_duration}\n")

        if self.plan.steps:
            lines.append("### Steps:\n")
            for i, step in enumerate(self.plan.steps, 1):
                desc = step.description or step.action or f"Step {i}"
                lines.append(f"{i}. {desc}")
            lines.append("")

        if self.plan.raw_content:
            # Truncate raw content for display
            content = self.plan.raw_content[:1500]
            if len(self.plan.raw_content) > 1500:
                content += "\n\n*... (content truncated)*"
            lines.append("### Details:\n")
            lines.append(content)

        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.dismiss(event.button.id == "approve")

    def action_approve(self) -> None:
        """Approve the plan."""
        self.dismiss(True)

    def action_reject(self) -> None:
        """Reject the plan."""
        self.dismiss(False)


__all__ = ["JulesPlanApprovalScreen"]
