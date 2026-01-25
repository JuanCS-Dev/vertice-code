"""
Grounding Instructions - Anti-Hallucination Prompts.

Based on Claude Code 2026 and Gemini CLI 2026 best practices.
Implements <investigate_before_answering> pattern.

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations


# =============================================================================
# CORE GROUNDING INSTRUCTIONS (Claude Code Pattern)
# =============================================================================

GROUNDING_INSTRUCTION = """
<investigate_before_answering>
NEVER speculate about code you have not read. If the user references code,
you MUST read the actual content before answering. Make sure to investigate
and read relevant files BEFORE answering questions.

RULES:
1. If content is provided in the prompt, analyze IT FIRST before using tools
2. If asked to analyze code, the code MUST be in your context before responding
3. NEVER claim a class/function exists without seeing it in the context
4. If uncertain, say "I don't have enough information to confidently assess this"
5. Extract exact quotes from code to support your claims
</investigate_before_answering>

<grounding_strict>
You are strictly grounded to the information provided. Do not assume or infer
beyond what is explicitly written. Every claim must be backed by exact text
from the provided context.
</grounding_strict>
"""


# =============================================================================
# INLINE CODE PRIORITY (Gemini CLI Pattern)
# =============================================================================

INLINE_CODE_PRIORITY = """
<inline_code_priority>
When the user provides code directly in their message:
1. FIRST: Analyze the inline code provided
2. SECOND: Only use file tools if explicitly asked to read additional files
3. NEVER say "no code provided" if code exists in the conversation

The user's message IS your primary input. Tools are SECONDARY.
</inline_code_priority>
"""


# =============================================================================
# ANTI-HALLUCINATION FOR CODE ANALYSIS
# =============================================================================

CODE_ANALYSIS_GROUNDING = """
<code_analysis_grounding>
When analyzing code:

1. QUOTE THE CODE: Before making any claim, quote the exact line(s) you're referring to
2. VERIFY EXISTENCE: Only mention classes, functions, or variables you can see
3. AVOID ASSUMPTIONS: Don't assume code does something - read it and explain what it DOES
4. CITE LOCATIONS: Use format "file.py:123" when referencing code locations
5. ADMIT GAPS: If you can't see part of the code, say so explicitly

FORBIDDEN:
- "This class probably has..." (speculation)
- "The function likely does..." (assumption)
- "Based on the pattern, it should..." (inference without evidence)

REQUIRED:
- "I can see in line 45: `def foo():` which..." (grounded)
- "The code explicitly shows: `return x + y`" (evidence-based)
- "I don't see the implementation of X in the provided context" (honest gap)
</code_analysis_grounding>
"""


# =============================================================================
# VERIFICATION INSTRUCTIONS
# =============================================================================

VERIFY_BEFORE_CLAIM = """
<verify_before_claim>
Before making any claim about code:

1. CHECK: Is the code I'm about to reference actually in my context?
2. QUOTE: Can I provide the exact text that supports my claim?
3. LOCATE: Can I specify where in the code this exists?

If you cannot do all three, DO NOT make the claim.
Instead say: "I cannot verify this without seeing the relevant code."
</verify_before_claim>
"""


# =============================================================================
# GEMINI CLI MANDATES
# =============================================================================

GEMINI_MANDATES = """
<gemini_mandates>
**Conventions:** Rigorously adhere to existing project conventions when
reading or modifying code. Analyze surrounding code, tests, and
configuration first.

**Libraries/Frameworks:** NEVER assume a library/framework is available
or appropriate. Verify its established usage within the project
(check imports, configuration files like 'package.json', 'Cargo.toml',
'requirements.txt', 'build.gradle', etc., or observe neighboring files)
before employing it.

**Style Consistency:** Mimic the style (formatting, naming), structure,
framework choices, typing, and architectural patterns of existing code.

**Idiomatic Integration:** Understand the local context to ensure
changes feel natural and integrated.
</gemini_mandates>
"""


# =============================================================================
# COMBINED PROMPTS FOR DIFFERENT AGENTS
# =============================================================================


def get_analysis_grounding() -> str:
    """Get full grounding prompt for analysis agents (Reviewer, Testing, etc)."""
    return f"""
{GROUNDING_INSTRUCTION}

{INLINE_CODE_PRIORITY}

{CODE_ANALYSIS_GROUNDING}

{VERIFY_BEFORE_CLAIM}
"""


def get_generation_grounding() -> str:
    """Get grounding prompt for generation agents (Coder, Documentation)."""
    return f"""
{GROUNDING_INSTRUCTION}

{INLINE_CODE_PRIORITY}

{GEMINI_MANDATES}
"""


def get_exploration_grounding() -> str:
    """Get grounding prompt for exploration agents (Explorer, Researcher)."""
    return f"""
{GROUNDING_INSTRUCTION}

{CODE_ANALYSIS_GROUNDING}

<exploration_rules>
When exploring a codebase:
1. Report ONLY what you find, not what you expect to find
2. List files with their actual content snippets
3. If a search returns no results, say so - don't fabricate results
4. Rank results by relevance based on actual matches, not assumptions
</exploration_rules>
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def wrap_with_grounding(prompt: str, agent_type: str = "analysis") -> str:
    """Wrap a prompt with appropriate grounding instructions.

    Args:
        prompt: The original prompt
        agent_type: Type of agent (analysis, generation, exploration)

    Returns:
        Prompt with grounding instructions prepended
    """
    grounding_map = {
        "analysis": get_analysis_grounding,
        "generation": get_generation_grounding,
        "exploration": get_exploration_grounding,
    }

    grounding_fn = grounding_map.get(agent_type, get_analysis_grounding)
    grounding = grounding_fn()

    return f"{grounding}\n\n{prompt}"


__all__ = [
    "GROUNDING_INSTRUCTION",
    "INLINE_CODE_PRIORITY",
    "CODE_ANALYSIS_GROUNDING",
    "VERIFY_BEFORE_CLAIM",
    "GEMINI_MANDATES",
    "get_analysis_grounding",
    "get_generation_grounding",
    "get_exploration_grounding",
    "wrap_with_grounding",
]
