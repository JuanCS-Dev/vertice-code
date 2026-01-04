"""
Prompt Components - Modular Prompt Building Blocks.

Based on Claude Code 2026 modular prompt architecture.
Each component is activated conditionally based on context.

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# PROMPT CONFIGURATION (Parameter Object Pattern)
# =============================================================================


@dataclass
class PromptConfig:
    """
    Configuration for agent prompt building.

    Parameter Object pattern: groups related boolean flags and options
    that control prompt composition. Reduces function parameter count
    and makes configuration reusable.

    Example:
        config = PromptConfig(
            investigate=True,
            workflow="implement",
            tone="detailed"
        )
        prompt = build_agent_prompt("CodeAgent", ["read", "write"], config=config)

    Attributes:
        investigate: Include code exploration requirement
        minimize_overengineering: Include minimal changes instruction
        output_format: Output format ("json" or "markdown")
        tool_policy: Include tool use policy component
        parallel_tools: Include parallel tool call instruction
        workflow: Workflow type ("implement", "analyze", or None)
        tone: Response tone ("concise" or "detailed")
        custom_instructions: Additional custom text to append
    """

    investigate: bool = True
    minimize_overengineering: bool = True
    output_format: str = "json"
    tool_policy: bool = True
    parallel_tools: bool = True
    workflow: Optional[str] = None
    tone: str = "concise"
    custom_instructions: Optional[str] = None


# =============================================================================
# CODE EXPLORATION COMPONENT
# =============================================================================

INVESTIGATE_COMPONENT = """
<code_exploration>
ALWAYS read and understand relevant code before proposing changes.
Do not speculate about code you have not inspected.
If the user references a specific file, you MUST open it first.
</code_exploration>
"""


# =============================================================================
# MINIMIZE OVERENGINEERING
# =============================================================================

MINIMIZE_OVERENGINEERING = """
<minimize_overengineering>
Avoid over-engineering. Only make changes that are directly requested.
Keep solutions simple and focused. Don't add features beyond what was asked.
A bug fix doesn't need surrounding code cleaned up.
A simple feature doesn't need extra configurability.
Don't add docstrings, comments, or type annotations to code you didn't change.
</minimize_overengineering>
"""


# =============================================================================
# OUTPUT FORMAT
# =============================================================================

OUTPUT_FORMAT_JSON = """
<output_format>
Provide structured JSON output with:
- success: boolean
- data: actual result
- reasoning: step-by-step explanation of how you arrived at the answer

Every claim must reference specific code you have seen.
</output_format>
"""

OUTPUT_FORMAT_MARKDOWN = """
<output_format>
Provide clear, structured output in Markdown format:
- Use headers (##) for sections
- Use code blocks (```) for code
- Use bullet points for lists
- Be concise but complete
</output_format>
"""


# =============================================================================
# TOOL USE POLICY
# =============================================================================

TOOL_USE_POLICY = """
<tool_use_policy>
Use tools ONLY when necessary:
- If information is in context, use it directly
- If you need to verify something, use read tools
- Parallel tool calls for independent operations
- Never guess file contents - read first

TOOL PRIORITY:
1. Use context already provided
2. Read files only when needed
3. Execute commands only when required
4. Never write without reading first
</tool_use_policy>
"""


# =============================================================================
# PARALLEL TOOL CALLS
# =============================================================================

PARALLEL_TOOL_CALLS = """
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between
the tool calls, make all independent calls in parallel.

EXAMPLE - DO THIS:
[read_file("a.py"), read_file("b.py"), read_file("c.py")]  # Parallel

EXAMPLE - DON'T DO THIS:
read_file("a.py")  # Wait
read_file("b.py")  # Wait
read_file("c.py")  # Wait - Sequential is slower

Only make sequential calls when one depends on another's result.
</use_parallel_tool_calls>
"""


# =============================================================================
# DEFAULT TO ACTION
# =============================================================================

DEFAULT_TO_ACTION = """
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's
intent is unclear, infer the most useful likely action and proceed, using
tools to discover any missing details instead of guessing.

PREFER:
- Implementing a fix over describing it
- Running a command over explaining it
- Writing code over outlining it

AVOID:
- "You could try..." (just do it)
- "One approach would be..." (implement it)
- "I suggest..." (execute the suggestion)
</default_to_action>
"""


# =============================================================================
# CONSERVATIVE ACTION MODE
# =============================================================================

CONSERVATIVE_ACTION = """
<conservative_action>
Do not jump into implementation unless clearly instructed. When the user's
intent is ambiguous, default to providing information and recommendations
rather than taking action.

PREFER:
- Explaining options before choosing
- Asking clarifying questions
- Showing what would change before changing

AVOID:
- Making assumptions about intent
- Modifying files without confirmation
- Running destructive commands
</conservative_action>
"""


# =============================================================================
# WORKFLOW COMPONENTS
# =============================================================================

WORKFLOW_UNDERSTAND_PLAN_IMPLEMENT = """
<workflow>
Follow this workflow for implementation tasks:

1. UNDERSTAND: Read and comprehend the request fully
2. INVESTIGATE: Explore relevant code and context
3. PLAN: Outline approach before implementing
4. IMPLEMENT: Make focused, minimal changes
5. VERIFY: Check that changes work as intended
6. RESPOND: Summarize what was done
</workflow>
"""

WORKFLOW_ANALYZE_REPORT = """
<workflow>
Follow this workflow for analysis tasks:

1. GATHER: Collect all relevant information
2. ANALYZE: Process and understand the data
3. SYNTHESIZE: Form conclusions based on evidence
4. REPORT: Present findings with citations
</workflow>
"""


# =============================================================================
# TONE AND STYLE
# =============================================================================

TONE_CONCISE = """
<tone>
Concise, direct, professional.
- Fewer than 3 lines output excluding tool use
- No chitchat or preambles
- Balance conciseness with clarity on safety matters
</tone>
"""

TONE_DETAILED = """
<tone>
Thorough and educational.
- Explain reasoning step by step
- Provide context for decisions
- Include relevant examples
</tone>
"""


# =============================================================================
# COMPONENT BUILDER
# =============================================================================


class PromptBuilder:
    """Build prompts from modular components."""

    def __init__(self):
        self._components: List[str] = []

    def add(self, component: str) -> "PromptBuilder":
        """Add a component to the prompt."""
        self._components.append(component.strip())
        return self

    def add_if(self, condition: bool, component: str) -> "PromptBuilder":
        """Conditionally add a component."""
        if condition:
            self._components.append(component.strip())
        return self

    def build(self) -> str:
        """Build the final prompt."""
        return "\n\n".join(self._components)

    def clear(self) -> "PromptBuilder":
        """Clear all components."""
        self._components = []
        return self


def build_agent_prompt(
    role: str,
    capabilities: List[str],
    config: Optional[PromptConfig] = None,
    *,
    # Legacy params for backward compatibility (deprecated)
    investigate: Optional[bool] = None,
    minimize_overengineering: Optional[bool] = None,
    output_format: Optional[str] = None,
    tool_policy: Optional[bool] = None,
    parallel_tools: Optional[bool] = None,
    workflow: Optional[str] = None,
    tone: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    """
    Build a complete agent prompt from modular components.

    Supports two calling patterns:
    1. New pattern (recommended): Pass a PromptConfig object
    2. Legacy pattern: Pass individual keyword arguments

    Args:
        role: Agent role description (e.g., "ReviewerAgent")
        capabilities: List of agent capabilities (e.g., ["read", "analyze"])
        config: PromptConfig object with all options (recommended)

    Legacy Args (deprecated - use config instead):
        investigate: Include investigation requirement
        minimize_overengineering: Include minimization instruction
        output_format: "json" or "markdown"
        tool_policy: Include tool use policy
        parallel_tools: Include parallel tool instruction
        workflow: "implement", "analyze", or None
        tone: "concise" or "detailed"
        custom_instructions: Additional custom instructions

    Returns:
        Complete prompt string ready for LLM

    Example:
        # New pattern (recommended)
        config = PromptConfig(workflow="implement", tone="detailed")
        prompt = build_agent_prompt("ArchitectAgent", ["design"], config=config)

        # Legacy pattern (still works)
        prompt = build_agent_prompt("ArchitectAgent", ["design"], workflow="implement")
    """
    # Use config or build from legacy params
    if config is None:
        config = PromptConfig(
            investigate=investigate if investigate is not None else True,
            minimize_overengineering=(
                minimize_overengineering if minimize_overengineering is not None else True
            ),
            output_format=output_format if output_format is not None else "json",
            tool_policy=tool_policy if tool_policy is not None else True,
            parallel_tools=parallel_tools if parallel_tools is not None else True,
            workflow=workflow,
            tone=tone if tone is not None else "concise",
            custom_instructions=custom_instructions,
        )

    builder = PromptBuilder()

    # Role header
    builder.add(f"You are {role}.")
    builder.add(f"CAPABILITIES: {', '.join(capabilities)}")

    # Core components
    builder.add_if(config.investigate, INVESTIGATE_COMPONENT)
    builder.add_if(config.minimize_overengineering, MINIMIZE_OVERENGINEERING)

    # Output format
    if config.output_format == "json":
        builder.add(OUTPUT_FORMAT_JSON)
    else:
        builder.add(OUTPUT_FORMAT_MARKDOWN)

    # Tool policy
    builder.add_if(config.tool_policy, TOOL_USE_POLICY)
    builder.add_if(config.parallel_tools, PARALLEL_TOOL_CALLS)

    # Workflow
    if config.workflow == "implement":
        builder.add(WORKFLOW_UNDERSTAND_PLAN_IMPLEMENT)
    elif config.workflow == "analyze":
        builder.add(WORKFLOW_ANALYZE_REPORT)

    # Tone
    if config.tone == "concise":
        builder.add(TONE_CONCISE)
    else:
        builder.add(TONE_DETAILED)

    # Custom
    if config.custom_instructions:
        builder.add(config.custom_instructions)

    return builder.build()


__all__ = [
    # Components
    "INVESTIGATE_COMPONENT",
    "MINIMIZE_OVERENGINEERING",
    "OUTPUT_FORMAT_JSON",
    "OUTPUT_FORMAT_MARKDOWN",
    "TOOL_USE_POLICY",
    "PARALLEL_TOOL_CALLS",
    "DEFAULT_TO_ACTION",
    "CONSERVATIVE_ACTION",
    "WORKFLOW_UNDERSTAND_PLAN_IMPLEMENT",
    "WORKFLOW_ANALYZE_REPORT",
    "TONE_CONCISE",
    "TONE_DETAILED",
    # Configuration
    "PromptConfig",
    # Builder
    "PromptBuilder",
    "build_agent_prompt",
]
