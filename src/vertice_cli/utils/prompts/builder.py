"XML Prompt Builder implementation."

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence
from .types import Example, ToolSpec, AgenticMode, OutputFormat


@dataclass
class XMLPromptBuilder:
    """Builder for XML-structured agent system prompts."""

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
        self._identity = {
            "role": role,
            "capabilities": list(capabilities) if capabilities else [],
            "philosophy": philosophy,
            "style": style,
        }
        return self

    def set_mission(self, objectives: Sequence[str]) -> XMLPromptBuilder:
        self._mission = list(objectives)
        return self

    def set_constraints(self, constraints: Sequence[str]) -> XMLPromptBuilder:
        self._constraints = list(constraints)
        return self

    def set_decision_criteria(
        self,
        approve: Optional[Sequence[str]] = None,
        veto: Optional[Sequence[str]] = None,
        escalate: Optional[Sequence[str]] = None,
    ) -> XMLPromptBuilder:
        self._decision_criteria = {}
        if approve:
            self._decision_criteria["approve"] = list(approve)
        if veto:
            self._decision_criteria["veto"] = list(veto)
        if escalate:
            self._decision_criteria["escalate"] = list(escalate)
        return self

    def add_examples(self, examples: Sequence[Example]) -> XMLPromptBuilder:
        self._examples.extend(examples)
        return self

    def set_output_format(
        self,
        format_type: OutputFormat = OutputFormat.JSON,
        schema: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> XMLPromptBuilder:
        self._output_schema = schema
        if description:
            self._output_format = description
        elif schema:
            self._output_format = _format_json_schema(schema)
        else:
            self._output_format = f"Respond in {format_type.value} format."
        return self

    def set_tools(self, tools: Sequence[ToolSpec]) -> XMLPromptBuilder:
        self._tools = list(tools)
        return self

    def set_agentic_mode(
        self,
        mode: AgenticMode = AgenticMode.AUTONOMOUS,
        persistence_reminder: bool = True,
        parallel_tools: bool = True,
    ) -> XMLPromptBuilder:
        self._agentic_mode = mode
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
            parts.append("Use unstructured text for progress notes and general context.")
        self._state_management = " ".join(parts) if parts else None
        return self

    def set_error_handling(
        self,
        retry_transient: bool = True,
        log_all_errors: bool = True,
        escalate_on_failure: bool = False,
    ) -> XMLPromptBuilder:
        parts = []
        if retry_transient:
            parts.append(
                "Distinguish transient errors (retry) from logic errors (change strategy)."
            )
        if log_all_errors:
            parts.append("Log all errors with context. Never silently swallow exceptions.")
        if escalate_on_failure:
            parts.append("Escalate to user after 3 consecutive failures of the same operation.")
        self._error_handling = " ".join(parts) if parts else None
        return self

    def add_section(self, name: str, content: str) -> XMLPromptBuilder:
        self._custom_sections[name] = content
        return self

    def build(self) -> str:
        sections: list[str] = []
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
        if self._mission:
            sections.append("")
            sections.append("<mission>")
            for i, obj in enumerate(self._mission, 1):
                sections.append(f"  {i}. {obj}")
            sections.append("</mission>")
        if self._constraints:
            sections.append("")
            sections.append("<constraints>")
            for const in self._constraints:
                sections.append(f"  - {const}")
            sections.append("</constraints>")
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
        if self._output_format:
            sections.append("")
            sections.append("<output_format>")
            sections.append(f"  {self._output_format}")
            sections.append("</output_format>")
        if self._tools:
            sections.append("")
            sections.append("<tools>")
            for tool in self._tools:
                sections.append(f'  <tool name="{tool.name}">')
                sections.append(f"    <use_when>{tool.when_to_use}</use_when>")
                if tool.when_not_to_use:
                    sections.append(f"    <avoid_when>{tool.when_not_to_use}</avoid_when>")
                sections.append("  </tool>")
            sections.append("</tools>")
        if self._state_management:
            sections.append("")
            sections.append("<state_management>")
            sections.append(f"  {self._state_management}")
            sections.append("</state_management>")
        if self._error_handling:
            sections.append("")
            sections.append("<error_handling>")
            sections.append(f"  {self._error_handling}")
            sections.append("</error_handling>")
        for name, content in self._custom_sections.items():
            sections.append("")
            sections.append(f"<{name}>")
            for line in content.split("\n"):
                sections.append(f"  {line}")
            sections.append(f"</{name}>")
        return "\n".join(sections)


def _format_json_schema(schema: Dict[str, Any], indent: int = 2) -> str:
    import json

    return json.dumps(schema, indent=indent)
