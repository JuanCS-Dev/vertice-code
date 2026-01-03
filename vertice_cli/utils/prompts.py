"""Unified Prompt Building Utilities for Agent System Prompts.

This module provides utilities for building consistent, well-structured
system prompts following 2025-2026 best practices from:
- Anthropic Claude 4.x (XML tags, chain of thought)
- Google Gemini 3 (PTCF framework, directness)
- OpenAI GPT-4.1/5.x (structured specs, agentic patterns)

Key Features:
    - XML-based prompt structure (Anthropic pattern)
    - PTCF framework support (Google pattern)
    - Agentic persistence reminders (OpenAI pattern)
    - Chain of thought integration
    - Tool usage patterns
    - State management sections

Design Principles:
    - XML tags for clarity and parseability
    - Less is more (Gemini 3 philosophy)
    - Explicit over implicit
    - Agentic-first design

References:
    - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags
    - https://ai.google.dev/gemini-api/docs/prompting-strategies
    - https://cookbook.openai.com/examples/gpt4-1_prompting_guide
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class OutputFormat(Enum):
    """Standard output format types for agents."""

    JSON = "json"
    JSON_STRICT = "json_strict"
    MARKDOWN = "markdown"
    XML = "xml"
    PLAIN = "plain"


class AgenticMode(Enum):
    """Agentic behavior modes."""

    AUTONOMOUS = "autonomous"  # Keep going until resolved
    CONSERVATIVE = "conservative"  # Ask before major actions
    COLLABORATIVE = "collaborative"  # Regular check-ins


@dataclass(frozen=True)
class Example:
    """An example case for agent prompts.

    Attributes:
        input: The example input/request.
        output: The expected output/decision.
        reasoning: Optional chain of thought explanation.
    """

    input: str
    output: str
    reasoning: str = ""


@dataclass(frozen=True)
class ToolSpec:
    """Tool specification for agentic prompts.

    Attributes:
        name: Tool name.
        when_to_use: When this tool should be used.
        when_not_to_use: When to avoid this tool.
    """

    name: str
    when_to_use: str
    when_not_to_use: str = ""


@dataclass
class XMLPromptBuilder:
    """Builder for XML-structured agent system prompts.

    Follows Anthropic Claude 4.x best practices with XML tags
    for clarity, accuracy, and parseability.

    Attributes:
        agent_name: Name of the agent.

    Example:
        >>> builder = XMLPromptBuilder("Architect")
        >>> builder.set_identity(
        ...     role="Feasibility Analyst",
        ...     capabilities=["READ_ONLY"],
        ...     philosophy="Better to reject early than fail late"
        ... )
        >>> builder.set_mission(["Analyze requests", "Identify risks"])
        >>> prompt = builder.build()
    """

    agent_name: str
    _identity: Dict[str, Any] = field(default_factory=dict)
    _mission: list[str] = field(default_factory=list)
    _constraints: list[str] = field(default_factory=list)
    _decision_criteria: Dict[str, list[str]] = field(default_factory=dict)
    _examples: list[Example] = field(default_factory=list)
    _output_format: Optional[str] = None
    _output_schema: Optional[Dict[str, Any]] = None
    _tools: list[ToolSpec] = field(default_factory=list)
    _agentic_mode: Optional[AgenticMode] = None
    _state_management: Optional[str] = None
    _error_handling: Optional[str] = None
    _custom_sections: Dict[str, str] = field(default_factory=dict)

    def set_identity(
        self,
        role: str,
        capabilities: Optional[Sequence[str]] = None,
        philosophy: str = "",
        style: str = "",
    ) -> XMLPromptBuilder:
        """Set agent identity in XML format.

        Args:
            role: The agent's role/title.
            capabilities: List of capabilities (e.g., ["READ_ONLY"]).
            philosophy: Guiding philosophy statement.
            style: Communication style description.

        Returns:
            Self for method chaining.
        """
        self._identity = {
            "role": role,
            "capabilities": list(capabilities) if capabilities else [],
            "philosophy": philosophy,
            "style": style,
        }
        return self

    def set_mission(self, objectives: Sequence[str]) -> XMLPromptBuilder:
        """Set mission objectives.

        Args:
            objectives: List of mission objectives.

        Returns:
            Self for method chaining.
        """
        self._mission = list(objectives)
        return self

    def set_constraints(self, constraints: Sequence[str]) -> XMLPromptBuilder:
        """Set behavioral constraints.

        Args:
            constraints: List of constraints.

        Returns:
            Self for method chaining.
        """
        self._constraints = list(constraints)
        return self

    def set_decision_criteria(
        self,
        approve: Optional[Sequence[str]] = None,
        veto: Optional[Sequence[str]] = None,
        escalate: Optional[Sequence[str]] = None,
    ) -> XMLPromptBuilder:
        """Set decision criteria for APPROVE/VETO patterns.

        Args:
            approve: Conditions for approval.
            veto: Conditions for rejection.
            escalate: Conditions for escalation.

        Returns:
            Self for method chaining.
        """
        self._decision_criteria = {}
        if approve:
            self._decision_criteria["approve"] = list(approve)
        if veto:
            self._decision_criteria["veto"] = list(veto)
        if escalate:
            self._decision_criteria["escalate"] = list(escalate)
        return self

    def add_examples(
        self,
        examples: Sequence[Example],
    ) -> XMLPromptBuilder:
        """Add examples with optional chain of thought.

        Args:
            examples: List of Example objects.

        Returns:
            Self for method chaining.
        """
        self._examples.extend(examples)
        return self

    def set_output_format(
        self,
        format_type: OutputFormat = OutputFormat.JSON,
        schema: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> XMLPromptBuilder:
        """Specify the expected output format.

        Args:
            format_type: Type of output.
            schema: JSON schema for structured output.
            description: Human-readable format description.

        Returns:
            Self for method chaining.
        """
        self._output_schema = schema
        if description:
            self._output_format = description
        elif schema:
            self._output_format = _format_json_schema(schema)
        else:
            self._output_format = f"Respond in {format_type.value} format."
        return self

    def set_tools(self, tools: Sequence[ToolSpec]) -> XMLPromptBuilder:
        """Set tool usage specifications.

        Args:
            tools: List of ToolSpec objects.

        Returns:
            Self for method chaining.
        """
        self._tools = list(tools)
        return self

    def set_agentic_mode(
        self,
        mode: AgenticMode = AgenticMode.AUTONOMOUS,
        persistence_reminder: bool = True,
        parallel_tools: bool = True,
    ) -> XMLPromptBuilder:
        """Configure agentic behavior patterns.

        Following OpenAI GPT-4.1/5.x agentic patterns.

        Args:
            mode: Agentic behavior mode.
            persistence_reminder: Include persistence reminder.
            parallel_tools: Enable parallel tool calling.

        Returns:
            Self for method chaining.
        """
        self._agentic_mode = mode
        # Build agentic section in custom sections
        agentic_content = []

        if mode == AgenticMode.AUTONOMOUS:
            if persistence_reminder:
                agentic_content.append(
                    "You are an agent - keep going until the task is completely "
                    "resolved before ending your turn. Do not stop early."
                )
            if parallel_tools:
                agentic_content.append(
                    "If you intend to call multiple tools with no dependencies between them, "
                    "make all independent calls in parallel for efficiency."
                )
        elif mode == AgenticMode.CONSERVATIVE:
            agentic_content.append(
                "Do not take major actions without confirmation. "
                "When intent is ambiguous, provide recommendations rather than implementing."
            )
        elif mode == AgenticMode.COLLABORATIVE:
            agentic_content.append(
                "Provide regular progress updates. Check in with the user "
                "at key decision points."
            )

        if agentic_content:
            self._custom_sections["agentic_behavior"] = "\n".join(agentic_content)
        return self

    def set_state_management(
        self,
        use_json_state: bool = True,
        use_git_tracking: bool = False,
        progress_notes: bool = True,
    ) -> XMLPromptBuilder:
        """Configure state management patterns.

        Following Claude 4.5 state management best practices.

        Args:
            use_json_state: Use JSON for structured state.
            use_git_tracking: Use git for state tracking.
            progress_notes: Use text for progress notes.

        Returns:
            Self for method chaining.
        """
        parts = []
        if use_json_state:
            parts.append(
                "Use JSON for tracking structured information (test results, task status, schemas)."
            )
        if use_git_tracking:
            parts.append(
                "Use git for state tracking - it provides a log of changes and checkpoints."
            )
        if progress_notes:
            parts.append(
                "Use unstructured text for progress notes and general context."
            )

        self._state_management = " ".join(parts) if parts else None
        return self

    def set_error_handling(
        self,
        retry_transient: bool = True,
        log_all_errors: bool = True,
        escalate_on_failure: bool = False,
    ) -> XMLPromptBuilder:
        """Configure error handling patterns.

        Args:
            retry_transient: Retry transient errors.
            log_all_errors: Log all errors with context.
            escalate_on_failure: Escalate on repeated failures.

        Returns:
            Self for method chaining.
        """
        parts = []
        if retry_transient:
            parts.append(
                "Distinguish transient errors (retry) from logic errors (change strategy)."
            )
        if log_all_errors:
            parts.append(
                "Log all errors with context. Never silently swallow exceptions."
            )
        if escalate_on_failure:
            parts.append(
                "Escalate to user after 3 consecutive failures of the same operation."
            )

        self._error_handling = " ".join(parts) if parts else None
        return self

    def add_section(self, name: str, content: str) -> XMLPromptBuilder:
        """Add a custom XML section.

        Args:
            name: Section name (used as XML tag).
            content: Section content.

        Returns:
            Self for method chaining.
        """
        self._custom_sections[name] = content
        return self

    def build(self) -> str:
        """Build the complete XML-structured system prompt.

        Returns:
            Formatted system prompt string with XML tags.
        """
        sections: list[str] = []

        # Identity section
        sections.append(f"You are the {self.agent_name} Agent.")
        if self._identity:
            sections.append("")
            sections.append("<identity>")
            if self._identity.get("role"):
                sections.append(f"  <role>{self._identity['role']}</role>")
            if self._identity.get("capabilities"):
                caps = ", ".join(self._identity["capabilities"])
                sections.append(f"  <capabilities>{caps}</capabilities>")
            if self._identity.get("philosophy"):
                sections.append(f"  <philosophy>{self._identity['philosophy']}</philosophy>")
            if self._identity.get("style"):
                sections.append(f"  <style>{self._identity['style']}</style>")
            sections.append("</identity>")

        # Mission section
        if self._mission:
            sections.append("")
            sections.append("<mission>")
            for i, obj in enumerate(self._mission, 1):
                sections.append(f"  {i}. {obj}")
            sections.append("</mission>")

        # Constraints section
        if self._constraints:
            sections.append("")
            sections.append("<constraints>")
            for const in self._constraints:
                sections.append(f"  - {const}")
            sections.append("</constraints>")

        # Decision criteria section
        if self._decision_criteria:
            sections.append("")
            sections.append("<decision_criteria>")
            if "approve" in self._decision_criteria:
                sections.append("  <approve_if>")
                for crit in self._decision_criteria["approve"]:
                    sections.append(f"    - {crit}")
                sections.append("  </approve_if>")
            if "veto" in self._decision_criteria:
                sections.append("  <veto_if>")
                for crit in self._decision_criteria["veto"]:
                    sections.append(f"    - {crit}")
                sections.append("  </veto_if>")
            if "escalate" in self._decision_criteria:
                sections.append("  <escalate_if>")
                for crit in self._decision_criteria["escalate"]:
                    sections.append(f"    - {crit}")
                sections.append("  </escalate_if>")
            sections.append("</decision_criteria>")

        # Examples section
        if self._examples:
            sections.append("")
            sections.append("<examples>")
            for ex in self._examples:
                sections.append("  <example>")
                sections.append(f"    <input>{ex.input}</input>")
                if ex.reasoning:
                    sections.append(f"    <thinking>{ex.reasoning}</thinking>")
                sections.append(f"    <output>{ex.output}</output>")
                sections.append("  </example>")
            sections.append("</examples>")

        # Output format section
        if self._output_format:
            sections.append("")
            sections.append("<output_format>")
            sections.append(f"  {self._output_format}")
            sections.append("</output_format>")

        # Tools section
        if self._tools:
            sections.append("")
            sections.append("<tools>")
            for tool in self._tools:
                sections.append(f"  <tool name=\"{tool.name}\">")
                sections.append(f"    <use_when>{tool.when_to_use}</use_when>")
                if tool.when_not_to_use:
                    sections.append(f"    <avoid_when>{tool.when_not_to_use}</avoid_when>")
                sections.append("  </tool>")
            sections.append("</tools>")

        # State management section
        if self._state_management:
            sections.append("")
            sections.append("<state_management>")
            sections.append(f"  {self._state_management}")
            sections.append("</state_management>")

        # Error handling section
        if self._error_handling:
            sections.append("")
            sections.append("<error_handling>")
            sections.append(f"  {self._error_handling}")
            sections.append("</error_handling>")

        # Custom sections
        for name, content in self._custom_sections.items():
            sections.append("")
            sections.append(f"<{name}>")
            for line in content.split("\n"):
                sections.append(f"  {line}")
            sections.append(f"</{name}>")

        return "\n".join(sections)


# Backwards-compatible alias
PromptBuilder = XMLPromptBuilder


def _format_json_schema(schema: Dict[str, Any], indent: int = 2) -> str:
    """Format a JSON schema for display in prompt."""
    import json
    return json.dumps(schema, indent=indent)


def build_agent_prompt(
    agent_name: str,
    role: str,
    mission: Sequence[str],
    capabilities: Optional[Sequence[str]] = None,
    approve_criteria: Optional[Sequence[str]] = None,
    veto_criteria: Optional[Sequence[str]] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    agentic: bool = False,
) -> str:
    """Convenience function to build an agent prompt quickly.

    Args:
        agent_name: Name of the agent.
        role: Agent's role/title.
        mission: List of mission objectives.
        capabilities: List of capabilities.
        approve_criteria: Conditions for approval.
        veto_criteria: Conditions for rejection.
        output_schema: JSON schema for output.
        agentic: Enable agentic mode patterns.

    Returns:
        Complete XML-structured system prompt.
    """
    builder = XMLPromptBuilder(agent_name)
    builder.set_identity(role, capabilities)
    builder.set_mission(mission)

    if approve_criteria or veto_criteria:
        builder.set_decision_criteria(
            approve=approve_criteria,
            veto=veto_criteria,
        )

    if output_schema:
        builder.set_output_format(OutputFormat.JSON_STRICT, schema=output_schema)

    if agentic:
        builder.set_agentic_mode(AgenticMode.AUTONOMOUS)
        builder.set_error_handling()

    return builder.build()


# Pre-built templates following Claude 4.x best practices

def create_reviewer_prompt() -> str:
    """Create a code reviewer agent prompt."""
    builder = XMLPromptBuilder("Reviewer")
    builder.set_identity(
        role="Code Quality Guardian",
        capabilities=["READ_ONLY"],
        philosophy="Quality is non-negotiable. Every line of code should be intentional.",
        style="Direct, technical, constructive",
    )
    builder.set_mission([
        "Review code changes for correctness and quality",
        "Identify bugs, security issues, and performance problems",
        "Suggest improvements following best practices",
        "Ensure code adheres to project standards",
    ])
    builder.set_decision_criteria(
        approve=[
            "Code is correct and handles edge cases",
            "No security vulnerabilities detected",
            "Follows project coding standards",
            "Has appropriate test coverage",
        ],
        veto=[
            "Contains security vulnerabilities",
            "Breaks existing functionality",
            "Significantly degrades performance",
            "Violates critical coding standards",
        ],
    )
    builder.set_output_format(
        OutputFormat.JSON_STRICT,
        schema={
            "decision": "APPROVED | NEEDS_CHANGES | VETOED",
            "summary": "string",
            "issues": [{"severity": "string", "location": "string", "description": "string"}],
            "suggestions": ["string"],
        },
    )
    return builder.build()


def create_architect_prompt() -> str:
    """Create an architect agent prompt."""
    builder = XMLPromptBuilder("Architect")
    builder.set_identity(
        role="Feasibility Analyst & Risk Assessor",
        capabilities=["READ_ONLY"],
        philosophy="Better to reject early than fail late. Most requests have valid paths forward.",
        style="Pragmatic, solution-oriented, technically precise",
    )
    builder.set_mission([
        "Analyze user requests for technical feasibility",
        "Identify architectural risks and constraints",
        "VETO only truly impossible or dangerous requests",
        "APPROVE feasible requests with clear architecture guidance",
    ])
    builder.set_constraints([
        "Do not approve requests that would break core architectural principles",
        "Do not veto requests just because they are complex",
        "Always provide reasoning for decisions",
    ])
    builder.set_decision_criteria(
        approve=[
            "Request is technically feasible with current codebase",
            "No critical architectural conflicts",
            "Risks are manageable with proper planning",
            "Clear implementation path exists",
        ],
        veto=[
            "Request requires unavailable dependencies that CANNOT be added",
            "Fundamentally breaks core architectural principles",
            "Requires destructive changes with NO possible rollback",
            "Request is fundamentally impossible to execute",
        ],
    )
    builder.add_examples([
        Example(
            input="Add JWT authentication to FastAPI",
            output="APPROVED",
            reasoning="Common pattern, well-documented, low risk",
        ),
        Example(
            input="Delete production database",
            output="VETOED",
            reasoning="Destructive, no rollback possible",
        ),
    ])
    builder.set_output_format(
        OutputFormat.JSON_STRICT,
        schema={
            "decision": "APPROVED | VETOED",
            "reasoning": "string",
            "architecture": {
                "approach": "string",
                "risks": ["string"],
                "constraints": ["string"],
                "estimated_complexity": "LOW | MEDIUM | HIGH",
            },
            "recommendations": ["string"],
        },
    )
    return builder.build()


def create_coder_prompt(agentic: bool = True) -> str:
    """Create a coder agent prompt with agentic patterns."""
    builder = XMLPromptBuilder("Coder")
    builder.set_identity(
        role="Implementation Specialist",
        capabilities=["READ_ONLY", "FILE_EDIT", "BASH_EXEC"],
        philosophy="Code should be simple, readable, and correct. Avoid over-engineering.",
        style="Precise, efficient, focused on the task",
    )
    builder.set_mission([
        "Implement requested features and fixes",
        "Write clean, maintainable code",
        "Follow existing patterns in the codebase",
        "Test changes before completing",
    ])
    builder.set_constraints([
        "Do not add features beyond what was requested",
        "Do not refactor unrelated code",
        "Do not add unnecessary abstractions",
        "Prefer editing existing files over creating new ones",
    ])
    builder.set_tools([
        ToolSpec(
            name="read_file",
            when_to_use="Before editing any file, to understand current state",
            when_not_to_use="When you already have the file content in context",
        ),
        ToolSpec(
            name="edit_file",
            when_to_use="To make targeted changes to existing files",
            when_not_to_use="For creating entirely new files (use write_file)",
        ),
        ToolSpec(
            name="bash",
            when_to_use="To run tests, git commands, or system operations",
            when_not_to_use="To read files (use read_file instead)",
        ),
    ])

    if agentic:
        builder.set_agentic_mode(
            AgenticMode.AUTONOMOUS,
            persistence_reminder=True,
            parallel_tools=True,
        )
        builder.set_error_handling(
            retry_transient=True,
            log_all_errors=True,
            escalate_on_failure=True,
        )
        builder.set_state_management(
            use_json_state=True,
            use_git_tracking=True,
            progress_notes=True,
        )

    return builder.build()


# Convenience templates
REVIEWER_PROMPT = create_reviewer_prompt()
ARCHITECT_PROMPT = create_architect_prompt()
CODER_PROMPT = create_coder_prompt()


__all__ = [
    # Main builder
    "XMLPromptBuilder",
    "PromptBuilder",  # Alias
    # Types
    "Example",
    "ToolSpec",
    "OutputFormat",
    "AgenticMode",
    # Convenience function
    "build_agent_prompt",
    # Template creators
    "create_reviewer_prompt",
    "create_architect_prompt",
    "create_coder_prompt",
    # Pre-built prompts
    "REVIEWER_PROMPT",
    "ARCHITECT_PROMPT",
    "CODER_PROMPT",
]
