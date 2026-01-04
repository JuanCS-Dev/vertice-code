"""
Output Validator - Validate Agent Output Against Schemas.

Following Claude Code 2026 pattern:
- Extract JSON from LLM responses (handles markdown code blocks)
- Validate against Pydantic schemas
- Provide helpful error messages

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError


# =============================================================================
# EXCEPTIONS
# =============================================================================


class OutputValidationError(Exception):
    """Raised when agent output fails validation."""

    def __init__(self, message: str, raw_output: Optional[str] = None):
        super().__init__(message)
        self.raw_output = raw_output


class JSONExtractionError(OutputValidationError):
    """Raised when JSON cannot be extracted from output."""

    pass


class SchemaValidationError(OutputValidationError):
    """Raised when output doesn't match expected schema."""

    def __init__(
        self,
        message: str,
        raw_output: Optional[str] = None,
        validation_errors: Optional[list] = None,
    ):
        super().__init__(message, raw_output)
        self.validation_errors = validation_errors or []


# =============================================================================
# JSON EXTRACTION
# =============================================================================


def extract_json(text: str) -> str:
    """Extract JSON from text, handling various formats.

    Handles:
    - Markdown code blocks (```json ... ```)
    - Plain JSON objects ({...})
    - JSON arrays ([...])
    - JSON with surrounding text

    Args:
        text: Raw text that may contain JSON

    Returns:
        Extracted JSON string

    Raises:
        JSONExtractionError: If no valid JSON found

    Examples:
        >>> extract_json('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
        >>> extract_json('Here is the result: {"x": 1}')
        '{"x": 1}'
    """
    if not text:
        raise JSONExtractionError("Empty output", text)

    text = text.strip()

    # Pattern 1: JSON in markdown code block
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        # Return the first code block that looks like valid JSON
        for match in matches:
            cleaned = match.strip()
            if cleaned.startswith("{") or cleaned.startswith("["):
                try:
                    json.loads(cleaned)
                    return cleaned
                except json.JSONDecodeError:
                    continue

    # Pattern 2: Find JSON object {...}
    obj_pattern = r"\{(?:[^{}]|\{[^{}]*\})*\}"
    obj_matches = re.findall(obj_pattern, text, re.DOTALL)
    if obj_matches:
        # Try each match, return the first valid one
        for match in obj_matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue

    # Pattern 3: Find JSON array [...]
    arr_pattern = r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]"
    arr_matches = re.findall(arr_pattern, text, re.DOTALL)
    if arr_matches:
        for match in arr_matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue

    # Pattern 4: Maybe the entire text is JSON?
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # Pattern 5: Try to find JSON between common delimiters
    # e.g., "Output: {...}" or "Result: {...}"
    delimited_pattern = r"(?:output|result|response|json)[\s:]*(\{.*\})"
    delimited_matches = re.findall(delimited_pattern, text, re.DOTALL | re.IGNORECASE)
    if delimited_matches:
        for match in delimited_matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue

    raise JSONExtractionError(
        f"No valid JSON found in output. Text starts with: {text[:100]}...", text
    )


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

T = TypeVar("T", bound=BaseModel)


def validate_agent_output(raw_output: str, schema: Type[T], *, strict: bool = True) -> T:
    """Validate and parse agent output against a Pydantic schema.

    Args:
        raw_output: Raw string output from LLM
        schema: Pydantic model class to validate against
        strict: If True, reject extra fields (default True per Claude Code pattern)

    Returns:
        Validated Pydantic model instance

    Raises:
        JSONExtractionError: If JSON cannot be extracted
        SchemaValidationError: If output doesn't match schema

    Examples:
        >>> from vertice_cli.schemas import ReviewOutput
        >>> result = validate_agent_output(
        ...     '{"decision": "APPROVED", "issues": [], "summary": "Good"}',
        ...     ReviewOutput
        ... )
        >>> result.decision
        <ReviewDecision.APPROVED: 'APPROVED'>
    """
    # Step 1: Extract JSON
    json_str = extract_json(raw_output)

    # Step 2: Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise JSONExtractionError(f"Invalid JSON: {e}", raw_output)

    # Step 3: Validate against schema
    try:
        # If strict mode, use model_validate which respects Config.extra
        if strict:
            return schema.model_validate(data)
        else:
            # Allow extra fields
            return schema.model_validate(data, strict=False)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"  - {err['loc']}: {err['msg']}" for err in errors]
        raise SchemaValidationError(
            f"Schema validation failed:\n" + "\n".join(error_messages), raw_output, errors
        )


def safe_validate(
    raw_output: str, schema: Type[T], *, default: Optional[T] = None
) -> Union[T, None]:
    """Validate output without raising exceptions.

    Args:
        raw_output: Raw string output from LLM
        schema: Pydantic model class to validate against
        default: Value to return if validation fails

    Returns:
        Validated model or default value
    """
    try:
        return validate_agent_output(raw_output, schema)
    except (JSONExtractionError, SchemaValidationError):
        return default


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def is_valid_json(text: str) -> bool:
    """Check if text contains valid JSON.

    Args:
        text: Text to check

    Returns:
        True if valid JSON found
    """
    try:
        extract_json(text)
        return True
    except JSONExtractionError:
        return False


def extract_and_parse(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from text to dict.

    Args:
        text: Text containing JSON

    Returns:
        Parsed JSON as dictionary

    Raises:
        JSONExtractionError: If no valid JSON found
    """
    json_str = extract_json(text)
    return json.loads(json_str)


def ensure_grounding(output: BaseModel) -> bool:
    """Check if output has proper grounding (code_analyzed field).

    Following Claude Code anti-hallucination pattern:
    all outputs should reference the code they analyzed.

    Args:
        output: Validated output model

    Returns:
        True if code_analyzed is present and non-empty
    """
    code_analyzed = getattr(output, "code_analyzed", None)
    return bool(code_analyzed and len(str(code_analyzed).strip()) > 0)


def format_validation_error(error: SchemaValidationError) -> str:
    """Format validation error for display.

    Args:
        error: Schema validation error

    Returns:
        User-friendly error message
    """
    lines = ["Output validation failed:"]

    for err in error.validation_errors:
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Unknown error")
        lines.append(f"  - {loc}: {msg}")

    if error.raw_output:
        preview = error.raw_output[:200]
        lines.append(f"\nRaw output preview:\n{preview}...")

    return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Exceptions
    "OutputValidationError",
    "JSONExtractionError",
    "SchemaValidationError",
    # Functions
    "extract_json",
    "validate_agent_output",
    "safe_validate",
    "is_valid_json",
    "extract_and_parse",
    "ensure_grounding",
    "format_validation_error",
]
