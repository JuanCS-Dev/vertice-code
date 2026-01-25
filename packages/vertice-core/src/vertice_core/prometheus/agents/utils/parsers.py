"""
Parsing utilities for Executor Agent.

Handles code extraction from LLM responses and JSON parsing.
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CodeExtractor:
    """Extracts code from solution text."""

    @staticmethod
    def extract(text: str) -> str:
        """
        Extract code from solution text.

        Tries multiple strategies:
        1. Code blocks (```python...```)
        2. Function definitions (def ...)
        3. Raw text as fallback

        Args:
            text: Solution text containing code

        Returns:
            Extracted code string
        """
        # Try to find code block
        code_match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Look for function definitions
        func_match = re.search(r"(def \w+.*?)(?=\n\n|\Z)", text, re.DOTALL)
        if func_match:
            return func_match.group(1).strip()

        return text


class JSONResponseParser:
    """Parses JSON from LLM responses."""

    @staticmethod
    def parse(text: str, default: Optional[dict] = None) -> dict:
        """
        Parse JSON from LLM response.

        Uses regex to find JSON-like structures even in mixed text.

        Args:
            text: LLM response text
            default: Default dict if parsing fails (defaults to {})

        Returns:
            Parsed dictionary or default
        """
        if default is None:
            default = {}

        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON from LLM response: {e}")

        return default


class TestCodeGenerator:
    """Generates test code for solution validation."""

    @staticmethod
    def generate(code: str, test_input: str, expected_output: str, test_index: int) -> str:
        """
        Generate test code for a solution.

        Creates executable test code that validates a solution against
        expected output. Includes fallback logic to find main function.

        Args:
            code: Solution code to test
            test_input: Input for the test
            expected_output: Expected output
            test_index: Test case number (for logging)

        Returns:
            Complete test code as string
        """
        return f"""
{code}

# Test case {test_index + 1}
try:
    result = main({repr(test_input)}) if 'main' in dir() else None
    if result is None:
        # Try to find the main function (silent continue is intentional)
        import sys
        for name, obj in list(globals().items()):
            if callable(obj) and not name.startswith('_'):
                try:
                    result = obj({repr(test_input)})
                    break
                except Exception as e:
                    continue  # Expected - try next callable

    expected = {repr(expected_output)}
    passed = result == expected
    print(f"RESULT: {{result}}")
    print(f"EXPECTED: {{expected}}")
    print(f"PASSED: {{passed}}")
except Exception as e:
    print(f"ERROR: {{e}}")
    print("PASSED: False")
"""
