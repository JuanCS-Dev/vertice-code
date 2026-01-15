"""
Prompts Module - LLM prompts for refactoring operations.

Contains system prompts and dynamic prompt builders for the RefactorerAgent.
Extracted for modularity and maintainability per Constitution guidelines.
"""

import json
from typing import Any, Dict, List


def build_system_prompt() -> str:
    """Build the system prompt for the RefactorerAgent.

    Returns:
        System prompt string
    """
    return """
You are RefactorerAgent v8.0 - Enterprise Transactional Code Surgeon

MISSION: Perform surgical code refactorings with zero behavior changes.

PRINCIPLES:
1. **Preserve Behavior**: Never change external behavior
2. **Atomic Operations**: All changes or none (ACID)
3. **Semantic Validity**: Check references before commit
4. **Test-Driven**: Run tests before any commit
5. **Format Preservation**: Keep comments, whitespace, style

REFACTORING TYPES:
- Extract Method: Pull code into new function
- Inline Method: Replace calls with body
- Rename Symbol: Update symbol + all references
- Extract Class: Split large class
- Simplify Expression: Reduce complexity
- Modernize Syntax: Update to latest Python

OUTPUT:
Structured refactoring plan with dependencies and risk assessment.
"""


def build_refactoring_prompt(
    target: str,
    content: str,
    refactoring_type: str,
    metrics: Dict[str, Any],
    blast_radius: Dict[str, List[str]],
) -> str:
    """Build LLM prompt for refactoring plan generation.

    Args:
        target: Target file path
        content: File content
        refactoring_type: Type of refactoring
        metrics: Code metrics
        blast_radius: Impact analysis

    Returns:
        Formatted prompt string
    """
    return f"""
REFACTORING REQUEST:
Target: {target}
Type: {refactoring_type}

CURRENT CODE:
```python
{content[:2000]}
```

CODE METRICS:
{json.dumps(metrics, indent=2)}

BLAST RADIUS:
Affected Files: {", ".join(blast_radius.get("affected_files", []))}
Risk Level: {blast_radius.get("risk_level", "UNKNOWN")}

TASK:
Generate a detailed refactoring plan that:
1. Preserves all external behavior
2. Updates ALL affected files in blast radius
3. Maintains code formatting and comments
4. Includes test updates if needed

OUTPUT FORMAT (JSON):
{{
    "changes": [
        {{
            "file": "path/to/file.py",
            "refactoring_type": "{refactoring_type}",
            "line_start": 10,
            "line_end": 20,
            "description": "Extract validation logic into separate method",
            "affected_symbols": ["old_name", "new_name"],
            "new_code": "def validate_input():\\n    ..."
        }}
    ],
    "execution_order": ["change-1", "change-2"],
    "risk_assessment": "MEDIUM"
}}
"""


def build_analysis_prompt(file_summary: str) -> str:
    """Build prompt for analyzing refactoring opportunities.

    Args:
        file_summary: Summary of files to analyze

    Returns:
        Analysis prompt string
    """
    return f"""
REFACTORING OPPORTUNITIES ANALYSIS

FILES TO ANALYZE:
{file_summary}

TASK:
Analyze the codebase and identify refactoring opportunities in these categories:
1. Extract Method - Long methods that can be split
2. Rename - Poor naming that hurts readability
3. Simplify - Complex expressions or logic
4. Modernize - Outdated Python patterns
5. Dead Code - Unused code that can be removed

For each opportunity, provide:
- file path
- line numbers
- current code smell
- suggested refactoring
- estimated impact

OUTPUT FORMAT: JSON array of opportunities
"""


__all__ = ["build_system_prompt", "build_refactoring_prompt", "build_analysis_prompt"]
