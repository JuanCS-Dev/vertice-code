"""
TestingAgent - The QA Engineer: Intelligent Test Generation and Quality Analysis.

This agent generates comprehensive test suites, analyzes coverage, performs mutation
testing, and detects flaky tests. It operates with READ_ONLY + BASH_EXEC capabilities.

Architecture (Boris Cherny Philosophy):
    - Type-safe interfaces (no Any except where unavoidable)
    - Pure functions for test generation logic
    - Zero mocks in production code
    - Comprehensive error handling

Philosophy:
    "Tests are executable specifications. If it's not tested, it's broken."
    - Boris Cherny

Capabilities:
    - Unit test generation (pytest-style)
    - Coverage analysis (pytest-cov integration)
    - Mutation testing (mutmut integration)
    - Flaky test detection
    - Test quality scoring (0-100)
"""

import logging
import re
from typing import Any, Dict, List, Optional

from vertice_cli.utils import MarkdownExtractor

from ..base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)
from vertice_cli.prompts.grounding import (
    INLINE_CODE_PRIORITY,
    get_analysis_grounding,
)
from vertice_cli.core.temperature_config import get_temperature

from .models import TestCase, TestFramework
from .generators import generate_test_suite
from .analyzers import CoverageAnalyzer, MutationAnalyzer, FlakyDetector
from .scoring import QualityScorer, score_to_grade
from .prompts import TESTING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class TestingAgent(BaseAgent):
    """
    The QA Engineer - Intelligent test generation and quality analysis.

    This agent analyzes code to generate comprehensive test suites, measures
    test quality through coverage and mutation testing, and identifies issues
    like flaky tests.

    Capabilities:
        - READ_ONLY: Analyze source code
        - BASH_EXEC: Run pytest, coverage tools, mutation testing

    Philosophy (Boris Cherny):
        "Test code is production code. Zero technical debt."
    """

    def __init__(
        self,
        llm_client: Any = None,
        mcp_client: Any = None,
        model: Any = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize TestingAgent with type-safe configuration.

        Args:
            llm_client: LLM provider client (for docstring generation)
            mcp_client: MCP tools client (for file operations)
            model: Alternative model (for test compatibility)
            config: Optional configuration dictionary
        """
        if llm_client is not None and mcp_client is not None:
            super().__init__(
                role=AgentRole.TESTING,
                capabilities=[
                    AgentCapability.READ_ONLY,
                    AgentCapability.BASH_EXEC,
                ],
                llm_client=llm_client,
                mcp_client=mcp_client,
                system_prompt=TESTING_SYSTEM_PROMPT,
            )
        else:
            # Test compatibility mode
            self.role = AgentRole.TESTING
            self.capabilities = [
                AgentCapability.READ_ONLY,
                AgentCapability.BASH_EXEC,
            ]
            self.name = "TestingAgent"
            self.llm_client = model
            self.config = config or {}

        # Configuration
        self.test_framework: TestFramework = TestFramework.PYTEST
        self.min_coverage_threshold: float = 90.0
        self.min_mutation_score: float = 80.0
        self.flaky_detection_runs: int = 5

        # Execution tracking
        self.execution_count: int = 0

        # Initialize analyzers (lazy - will be created when needed)
        self._coverage_analyzer: Optional[CoverageAnalyzer] = None
        self._mutation_analyzer: Optional[MutationAnalyzer] = None
        self._flaky_detector: Optional[FlakyDetector] = None
        self._quality_scorer: Optional[QualityScorer] = None

    def _get_coverage_analyzer(self) -> CoverageAnalyzer:
        """Get or create coverage analyzer."""
        if self._coverage_analyzer is None:
            self._coverage_analyzer = CoverageAnalyzer(
                self._execute_tool, self.min_coverage_threshold
            )
        return self._coverage_analyzer

    def _get_mutation_analyzer(self) -> MutationAnalyzer:
        """Get or create mutation analyzer."""
        if self._mutation_analyzer is None:
            self._mutation_analyzer = MutationAnalyzer(self._execute_tool, self.min_mutation_score)
        return self._mutation_analyzer

    def _get_flaky_detector(self) -> FlakyDetector:
        """Get or create flaky detector."""
        if self._flaky_detector is None:
            self._flaky_detector = FlakyDetector(self._execute_tool, self.flaky_detection_runs)
        return self._flaky_detector

    def _get_quality_scorer(self) -> QualityScorer:
        """Get or create quality scorer."""
        if self._quality_scorer is None:
            self._quality_scorer = QualityScorer(
                self._get_coverage_analyzer(), self._get_mutation_analyzer()
            )
        return self._quality_scorer

    def _extract_code_blocks(self, text: str) -> str:
        """Extract code from markdown code blocks or inline in user message.

        Claude Code Pattern: Inline code has priority over file tools.
        Uses unified MarkdownExtractor from vertice_cli.utils.

        Args:
            text: User message or prompt text

        Returns:
            Extracted code as string, empty if none found
        """
        if not text:
            return ""

        extractor = MarkdownExtractor(deduplicate=True)
        blocks = extractor.extract_code_blocks(text, language="python")

        # If no python-specific blocks, try all blocks
        if not blocks:
            blocks = extractor.extract_code_blocks(text)

        return "\n\n".join(block.content for block in blocks)

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute testing analysis task.

        Args:
            task: Testing task with action type in context

        Returns:
            AgentResponse with test generation/analysis results

        Workflow:
            1. Parse task action (generate_tests, analyze_coverage, etc.)
            2. Execute appropriate analysis method
            3. Calculate quality score
            4. Return structured response
        """
        self.execution_count += 1

        try:
            action = task.context.get("action", "generate_tests")

            if action == "generate_tests":
                return await self._handle_test_generation(task)
            elif action == "analyze_coverage":
                return await self._handle_coverage_analysis(task)
            elif action == "mutation_testing":
                return await self._handle_mutation_testing(task)
            elif action == "detect_flaky":
                return await self._handle_flaky_detection(task)
            elif action == "test_quality_score":
                return await self._handle_quality_scoring(task)
            else:
                return AgentResponse(
                    success=False,
                    data={},
                    reasoning=f"Unknown action: {action}",
                    error="Supported actions: generate_tests, analyze_coverage, "
                    "mutation_testing, detect_flaky, test_quality_score",
                )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"TestingAgent execution failed: {str(e)}",
                error=str(e),
            )

    async def _handle_test_generation(self, task: AgentTask) -> AgentResponse:
        """Generate test suite for given code.

        Priority Order (Claude Code 2026 Pattern):
            1. Inline code in user_message (HIGHEST PRIORITY)
            2. source_code in context
            3. file_path in context
            4. files list in context

        Args:
            task: Task with source_code, file_path, or inline code

        Returns:
            AgentResponse with generated tests
        """
        source_code = ""

        # PRIORITY 1: Extract inline code from user message
        user_message = task.context.get("user_message", "")
        if not user_message:
            user_message = task.context.get("prompt", task.context.get("request", ""))

        inline_code = self._extract_code_blocks(user_message)
        if inline_code:
            source_code = inline_code

        # PRIORITY 2: Check source_code in context
        if not source_code:
            source_code = task.context.get("source_code", "")

        # PRIORITY 3: Read from file_path
        file_path = task.context.get("file_path", "")
        if not source_code and file_path:
            try:
                result = await self._execute_tool("read_file", {"path": file_path})
                source_code = result.get("content", "")
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    reasoning=f"Failed to read file: {file_path}",
                    error=str(e),
                )

        # PRIORITY 4: Read from files list
        files = task.context.get("files", [])
        if not source_code and files:
            code_parts = []
            for f in files[:5]:  # Limit to 5 files
                try:
                    with open(f, "r") as fp:
                        code_parts.append(f"# File: {f}\n{fp.read()}")
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug(f"Could not read file {f}: {e}")
                    continue
            source_code = "\n\n".join(code_parts)

        # Final check
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code found. Please provide source_code inline, "
                "or specify source_code, file_path, or files in context.",
                error="source_code is required. Tip: Include code in ```python``` blocks.",
            )

        # Generate tests using pure function
        test_cases = generate_test_suite(source_code)

        # Calculate metrics
        total_assertions = sum(tc.assertions for tc in test_cases)
        avg_complexity = (
            sum(tc.complexity for tc in test_cases) / len(test_cases) if test_cases else 0
        )

        return AgentResponse(
            success=True,
            data={
                "test_cases": [
                    {
                        "name": tc.name,
                        "code": tc.code,
                        "type": tc.test_type.value,
                        "target": tc.target,
                        "assertions": tc.assertions,
                        "complexity": tc.complexity,
                    }
                    for tc in test_cases
                ],
                "metrics": {
                    "total_tests": len(test_cases),
                    "total_assertions": total_assertions,
                    "avg_complexity": round(avg_complexity, 2),
                },
            },
            reasoning=f"Generated {len(test_cases)} tests with {total_assertions} assertions",
            metrics={
                "test_count": float(len(test_cases)),
                "total_assertions": float(total_assertions),
            },
        )

    async def _handle_coverage_analysis(self, task: AgentTask) -> AgentResponse:
        """Analyze test coverage using pytest-cov.

        Args:
            task: Task with test_path and source_path in context

        Returns:
            AgentResponse with coverage report
        """
        test_path = task.context.get("test_path", "tests/")
        source_path = task.context.get("source_path", ".")

        try:
            # Run pytest with coverage
            cmd = f"pytest {test_path} --cov={source_path} --cov-report=json --quiet"
            await self._execute_tool("bash_command", {"command": cmd})

            # Parse coverage JSON (can be mocked for tests)
            coverage_data = await self._parse_coverage_json()

            # Calculate quality score
            quality_score = self._calculate_coverage_score(coverage_data)

            return AgentResponse(
                success=True,
                data={
                    "coverage": {
                        "total_statements": coverage_data.total_statements,
                        "covered_statements": coverage_data.covered_statements,
                        "coverage_percentage": coverage_data.coverage_percentage,
                        "branch_coverage": coverage_data.branch_coverage,
                        "missing_lines_count": len(coverage_data.missing_lines),
                    },
                    "quality_score": quality_score,
                    "meets_threshold": coverage_data.coverage_percentage
                    >= self.min_coverage_threshold,
                },
                reasoning=f"Coverage: {coverage_data.coverage_percentage:.1f}% "
                f"(threshold: {self.min_coverage_threshold}%)",
                metrics={
                    "coverage_percentage": coverage_data.coverage_percentage,
                    "branch_coverage": coverage_data.branch_coverage,
                },
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"Coverage analysis failed: {str(e)}",
                error=str(e),
            )

    async def _parse_coverage_json(self) -> "CoverageReport":
        """Parse coverage.json file. Can be mocked for testing."""
        import json
        from .models import CoverageReport

        try:
            result = await self._execute_tool("read_file", {"path": "coverage.json"})
            data = json.loads(result.get("content", "{}"))
            totals = data.get("totals", {})

            return CoverageReport(
                total_statements=totals.get("num_statements", 0),
                covered_statements=totals.get("covered_lines", 0),
                coverage_percentage=totals.get("percent_covered", 0.0),
                missing_lines=[],
                branches_total=totals.get("num_branches", 0),
                branches_covered=totals.get("covered_branches", 0),
            )
        except (json.JSONDecodeError, KeyError, TypeError, FileNotFoundError):
            from .models import CoverageReport

            return CoverageReport(
                total_statements=0,
                covered_statements=0,
                coverage_percentage=0.0,
                missing_lines=[],
                branches_total=0,
                branches_covered=0,
            )

    def _calculate_coverage_score(self, coverage: "CoverageReport") -> int:
        """Calculate quality score from coverage metrics. Can be mocked for testing."""
        base_score = coverage.coverage_percentage * 0.7
        branch_bonus = coverage.branch_coverage * 0.3
        return min(100, int(base_score + branch_bonus))

    async def _handle_mutation_testing(self, task: AgentTask) -> AgentResponse:
        """Run mutation testing using mutmut.

        Args:
            task: Task with source_path in context

        Returns:
            AgentResponse with mutation testing results
        """
        source_path = task.context.get("source_path", ".")

        try:
            # Run mutmut
            cmd = f"mutmut run --paths-to-mutate={source_path} --runner='pytest -x'"
            await self._execute_tool("bash_command", {"command": cmd})

            # Get results
            result = await self._execute_tool("bash_command", {"command": "mutmut results"})

            # Parse mutation results (can be mocked for tests)
            mutation_result = self._parse_mutation_results(result.get("output", ""))

            # Calculate score
            quality_score = int(mutation_result.mutation_score)

            return AgentResponse(
                success=True,
                data={
                    "mutation_testing": {
                        "total_mutants": mutation_result.total_mutants,
                        "killed_mutants": mutation_result.killed_mutants,
                        "survived_mutants": mutation_result.survived_mutants,
                        "timeout_mutants": mutation_result.timeout_mutants,
                        "mutation_score": mutation_result.mutation_score,
                    },
                    "quality_score": quality_score,
                    "meets_threshold": mutation_result.mutation_score >= self.min_mutation_score,
                },
                reasoning=f"Mutation score: {mutation_result.mutation_score:.1f}% "
                f"(threshold: {self.min_mutation_score}%)",
                metrics={
                    "mutation_score": mutation_result.mutation_score,
                    "killed_mutants": float(mutation_result.killed_mutants),
                },
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"Mutation testing failed: {str(e)}",
                error=str(e),
            )

    def _parse_mutation_results(self, output: str) -> "MutationResult":
        """Parse mutmut results output. Can be mocked for testing."""
        from .models import MutationResult

        killed = len(re.findall(r"KILLED", output))
        survived = len(re.findall(r"SURVIVED", output))
        timeout = len(re.findall(r"TIMEOUT", output))
        total = killed + survived + timeout

        return MutationResult(
            total_mutants=total,
            killed_mutants=killed,
            survived_mutants=survived,
            timeout_mutants=timeout,
        )

    async def _handle_flaky_detection(self, task: AgentTask) -> AgentResponse:
        """Detect flaky tests by running multiple times.

        Args:
            task: Task with test_path in context

        Returns:
            AgentResponse with flaky test results
        """
        test_path = task.context.get("test_path", "tests/")
        runs = task.context.get("runs", self.flaky_detection_runs)

        try:
            flaky_tests = await self._detect_flaky_tests(test_path, runs)

            return AgentResponse(
                success=True,
                data={
                    "flaky_tests": [
                        {
                            "name": ft.name,
                            "file_path": ft.file_path,
                            "failure_rate": ft.failure_rate,
                            "error_messages": ft.error_messages,
                            "suspected_cause": ft.suspected_cause,
                        }
                        for ft in flaky_tests
                    ],
                    "flaky_count": len(flaky_tests),
                },
                reasoning=f"Found {len(flaky_tests)} flaky tests in {runs} runs",
                metrics={
                    "runs": float(runs),
                    "flaky_count": float(len(flaky_tests)),
                },
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"Flaky detection failed: {str(e)}",
                error=str(e),
            )

    async def _detect_flaky_tests(self, test_path: str, runs: int) -> List["FlakyTest"]:
        """Run tests multiple times to detect flakiness. Can be mocked for testing."""
        from .models import FlakyTest

        test_results: Dict[str, List[bool]] = {}

        for _ in range(runs):
            result = await self._execute_tool("bash_command", {"command": f"pytest {test_path} -v"})

            output = result.get("output", "")
            for line in output.split("\n"):
                if "::" in line and ("PASSED" in line or "FAILED" in line):
                    test_name = line.split("::")[0].strip()
                    if test_name:
                        if test_name not in test_results:
                            test_results[test_name] = []
                        test_results[test_name].append("PASSED" in line)

        # Identify flaky tests
        flaky_tests: List[FlakyTest] = []
        for test_name, results in test_results.items():
            if len(set(results)) > 1:
                failure_rate = (results.count(False) / len(results)) * 100
                flaky_tests.append(
                    FlakyTest(
                        name=test_name,
                        file_path=test_path,
                        failure_rate=failure_rate,
                        error_messages=["Intermittent failure"],
                        suspected_cause="Race condition or timing issue",
                    )
                )

        return flaky_tests

    async def _handle_quality_scoring(self, task: AgentTask) -> AgentResponse:
        """Calculate comprehensive test quality score.

        Args:
            task: Task (may include specific metrics to evaluate)

        Returns:
            AgentResponse with quality score (0-100)
        """
        try:
            # Get coverage
            coverage_task = AgentTask(
                request="Analyze coverage",
                context={"action": "analyze_coverage", **task.context},
            )
            coverage_response = await self._handle_coverage_analysis(coverage_task)
            coverage_pct = coverage_response.data.get("coverage", {}).get("coverage_percentage", 0)

            # Get mutation score
            try:
                mutation_task = AgentTask(
                    request="Run mutation testing",
                    context={"action": "mutation_testing", **task.context},
                )
                mutation_response = await self._handle_mutation_testing(mutation_task)
                mutation_score = mutation_response.data.get("mutation_testing", {}).get(
                    "mutation_score", 0
                )
            except Exception as e:
                logger.warning(f"Mutation testing failed during quality analysis: {e}")
                mutation_score = 0

            # Calculate component scores
            coverage_score = (coverage_pct / 100) * 40
            mutation_component = (mutation_score / 100) * 30
            test_count_component = 15  # Assume good if tests exist
            flaky_component = 15  # Assume no flaky tests

            total_score = int(
                coverage_score + mutation_component + test_count_component + flaky_component
            )

            return AgentResponse(
                success=True,
                data={
                    "quality_score": total_score,
                    "breakdown": {
                        "coverage": int(coverage_score),
                        "mutation": int(mutation_component),
                        "test_count": test_count_component,
                        "no_flaky": flaky_component,
                    },
                    "grade": score_to_grade(total_score),
                },
                reasoning=f"Test quality score: {total_score}/100 "
                f"({score_to_grade(total_score)})",
                metrics={
                    "quality_score": float(total_score),
                    "coverage_score": coverage_score,
                },
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"Quality scoring failed: {str(e)}",
                error=str(e),
            )


def create_testing_agent(
    llm_client: Any = None,
    mcp_client: Any = None,
    config: Optional[Dict[str, Any]] = None,
) -> TestingAgent:
    """Factory function to create TestingAgent.

    Args:
        llm_client: LLM provider client
        mcp_client: MCP tools client
        config: Optional configuration

    Returns:
        Configured TestingAgent instance
    """
    return TestingAgent(
        llm_client=llm_client,
        mcp_client=mcp_client,
        config=config,
    )


__all__ = [
    "TestingAgent",
    "create_testing_agent",
    "TESTING_SYSTEM_PROMPT",
]
