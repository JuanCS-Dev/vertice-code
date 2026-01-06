"""
Test runner for Executor Agent code solutions.

Executes test cases in sandbox and evaluates results.
"""

from typing import List, Optional, Tuple

from ..curriculum_agent import EvolutionTask, TaskDomain
from ..utils.parsers import CodeExtractor, TestCodeGenerator


class TestRunner:
    """Runs test cases for code solutions in sandbox."""

    def __init__(self, sandbox_executor):
        """
        Initialize test runner.

        Args:
            sandbox_executor: Sandbox execution environment
        """
        self.sandbox = sandbox_executor
        self.code_extractor = CodeExtractor()
        self.test_generator = TestCodeGenerator()

    async def run_test_cases(
        self,
        task: EvolutionTask,
        solution: str,
    ) -> Tuple[Optional[float], List[str]]:
        """
        Run test cases for code solutions.

        Args:
            task: The evolution task with test cases
            solution: The solution to test

        Returns:
            Tuple of (score, errors)
            - score: 0-1 pass rate or None if no tests
            - errors: List of error messages
        """
        if not task.test_cases:
            return None, []

        # Extract code from solution
        code = self.code_extractor.extract(solution)
        if not code:
            return 0.0, ["No code found in solution"]

        passed = 0
        errors = []

        for i, test in enumerate(task.test_cases):
            test_input = test.get("input", "")
            expected = test.get("expected_output", test.get("expected", ""))

            # Generate test code
            test_code = self.test_generator.generate(code, test_input, expected, i)

            # Execute in sandbox
            result = await self.sandbox.execute(test_code, timeout=10)

            if result.success and "PASSED: True" in result.stdout:
                passed += 1
            else:
                error_msg = f"Test {i+1} failed"
                if result.stderr:
                    error_msg += f": {result.stderr[:100]}"
                errors.append(error_msg)

        score = passed / len(task.test_cases) if task.test_cases else 0
        return score, errors
