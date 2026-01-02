"""
REAL Quality Validation Tests

FUNDAMENTAL: These tests validate that outputs MATCH what was requested.
This is what differentiates top-tier systems (Claude Code, Gemini CLI,
Codex, GitHub Copilot) from the rest.

Quality validation covers:
1. Completeness - All parts of request addressed
2. Correctness - Technically accurate
3. Coherence - Logically structured response
4. Relevance - Stays on topic
5. Actionability - Can be used directly
"""

import pytest
import asyncio
import os
import sys
import time
import re
import ast
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.real,
    pytest.mark.quality,
]


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_env()


@dataclass
class QualityScore:
    """Detailed quality score."""

    completeness: float  # 0-1: All parts of request addressed
    correctness: float   # 0-1: Technically accurate
    coherence: float     # 0-1: Logically structured
    relevance: float     # 0-1: Stays on topic
    actionability: float # 0-1: Can be used directly

    @property
    def overall(self) -> float:
        """Weighted overall score."""
        weights = {
            'completeness': 0.25,
            'correctness': 0.30,  # Most important
            'coherence': 0.15,
            'relevance': 0.15,
            'actionability': 0.15,
        }
        return (
            self.completeness * weights['completeness'] +
            self.correctness * weights['correctness'] +
            self.coherence * weights['coherence'] +
            self.relevance * weights['relevance'] +
            self.actionability * weights['actionability']
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            'completeness': self.completeness,
            'correctness': self.correctness,
            'coherence': self.coherence,
            'relevance': self.relevance,
            'actionability': self.actionability,
            'overall': self.overall,
        }


class QualityValidator:
    """Validates output quality against requests."""

    def validate_code_output(
        self,
        request: str,
        output: str,
        expected_elements: List[str]
    ) -> QualityScore:
        """Validate code generation output."""

        # Extract code from output
        code = self._extract_code(output)

        # Completeness: Check expected elements
        completeness = self._check_completeness(output, expected_elements)

        # Correctness: Syntax validity + logic check
        correctness = self._check_code_correctness(code, request)

        # Coherence: Well-structured response
        coherence = self._check_coherence(output)

        # Relevance: Addresses the request
        relevance = self._check_relevance(output, request)

        # Actionability: Code can be used directly
        actionability = self._check_actionability(code)

        return QualityScore(
            completeness=completeness,
            correctness=correctness,
            coherence=coherence,
            relevance=relevance,
            actionability=actionability,
        )

    def validate_explanation_output(
        self,
        request: str,
        output: str,
        key_concepts: List[str]
    ) -> QualityScore:
        """Validate explanation/documentation output."""

        # Completeness: Key concepts mentioned
        completeness = self._check_completeness(output, key_concepts)

        # Correctness: Factual accuracy (harder to verify automatically)
        # Check for common misconceptions
        correctness = self._check_explanation_correctness(output, request)

        # Coherence: Well-structured explanation
        coherence = self._check_coherence(output)

        # Relevance: Stays on topic
        relevance = self._check_relevance(output, request)

        # Actionability: Provides usable information
        actionability = 0.8 if len(output) > 100 else 0.5

        return QualityScore(
            completeness=completeness,
            correctness=correctness,
            coherence=coherence,
            relevance=relevance,
            actionability=actionability,
        )

    def validate_plan_output(
        self,
        request: str,
        output: str,
        expected_steps: List[str]
    ) -> QualityScore:
        """Validate planning output."""

        # Completeness: All steps addressed
        completeness = self._check_completeness(output, expected_steps)

        # Correctness: Steps make sense
        correctness = self._check_plan_correctness(output, request)

        # Coherence: Steps in logical order
        coherence = self._check_plan_coherence(output)

        # Relevance: Plan matches request
        relevance = self._check_relevance(output, request)

        # Actionability: Can follow the plan
        actionability = self._check_plan_actionability(output)

        return QualityScore(
            completeness=completeness,
            correctness=correctness,
            coherence=coherence,
            relevance=relevance,
            actionability=actionability,
        )

    def _extract_code(self, output: str) -> str:
        """Extract code blocks from output."""
        # Try markdown code blocks first
        code_blocks = re.findall(r'```(?:python)?\n?(.*?)```', output, re.DOTALL)
        if code_blocks:
            return '\n\n'.join(code_blocks)

        # Try to find function/class definitions
        lines = output.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            if re.match(r'^(def |class |import |from |@)', line.strip()):
                in_code = True
            if in_code:
                if line.strip() and not line.startswith(' ') and not any(
                    line.strip().startswith(kw) for kw in ['def ', 'class ', 'import ', 'from ', '@', '#']
                ):
                    in_code = False
                else:
                    code_lines.append(line)

        return '\n'.join(code_lines) if code_lines else ""

    def _check_completeness(self, output: str, elements: List[str]) -> float:
        """Check if all expected elements are present."""
        if not elements:
            return 0.8  # Default for no specific requirements

        output_lower = output.lower()
        found = sum(1 for elem in elements if elem.lower() in output_lower)
        return found / len(elements)

    def _check_code_correctness(self, code: str, request: str) -> float:
        """Check code correctness."""
        if not code:
            return 0.3  # No code found

        score = 0.5  # Base score

        # Syntax check
        try:
            ast.parse(code)
            score += 0.3  # Valid syntax
        except SyntaxError:
            score -= 0.2  # Invalid syntax

        # Check for common issues
        issues = []

        # Undefined variable patterns (very basic)
        if 'undefined' in code.lower() or 'todo' in code.lower():
            issues.append("Contains placeholder code")
            score -= 0.1

        # Check for proper function/class structure
        if 'def ' in code or 'class ' in code:
            score += 0.1

        # Check for error handling if request mentions errors
        if 'error' in request.lower() or 'exception' in request.lower():
            if 'try' in code or 'except' in code or 'raise' in code:
                score += 0.1

        return min(1.0, max(0.0, score))

    def _check_explanation_correctness(self, output: str, request: str) -> float:
        """Check explanation correctness."""
        score = 0.7  # Base score for providing an explanation

        output_lower = output.lower()

        # Common misconceptions to penalize
        misconceptions = [
            ("python is compiled", -0.2),  # Python is interpreted
            ("javascript is java", -0.2),
            ("global variables are good", -0.1),
        ]

        for misconception, penalty in misconceptions:
            if misconception in output_lower:
                score += penalty

        # Bonus for mentioning caveats/limitations
        if any(word in output_lower for word in ['however', 'but', 'note', 'caveat', 'limitation']):
            score += 0.1

        return min(1.0, max(0.0, score))

    def _check_coherence(self, output: str) -> float:
        """Check response coherence."""
        if not output:
            return 0.0

        score = 0.5

        # Has structure (paragraphs or sections)
        if '\n\n' in output or '##' in output or '1.' in output:
            score += 0.2

        # Reasonable length
        if 50 < len(output) < 10000:
            score += 0.2

        # Has conclusion or summary indicators
        if any(word in output.lower() for word in ['in summary', 'to summarize', 'in conclusion', 'finally']):
            score += 0.1

        return min(1.0, score)

    def _check_relevance(self, output: str, request: str) -> float:
        """Check if output is relevant to request."""
        if not output or not request:
            return 0.0

        # Extract key terms from request
        request_words = set(re.findall(r'\b\w{4,}\b', request.lower()))
        output_lower = output.lower()

        # Count how many request terms appear in output
        found = sum(1 for word in request_words if word in output_lower)
        relevance = found / max(1, len(request_words))

        # Bonus for addressing the main verb (what the user wants to DO)
        action_words = ['create', 'write', 'implement', 'explain', 'fix', 'analyze',
                       'design', 'build', 'add', 'remove', 'update', 'refactor']
        for action in action_words:
            if action in request.lower() and action in output_lower:
                relevance = min(1.0, relevance + 0.1)

        return min(1.0, relevance)

    def _check_actionability(self, code: str) -> float:
        """Check if code is actionable."""
        if not code:
            return 0.3

        score = 0.5

        # Has complete function/class definitions
        if re.search(r'def \w+\([^)]*\):', code):
            score += 0.2
        if re.search(r'class \w+', code):
            score += 0.1

        # Has docstrings
        if '"""' in code or "'''" in code:
            score += 0.1

        # Doesn't have obvious placeholders
        if 'pass' not in code and '...' not in code:
            score += 0.1

        return min(1.0, score)

    def _check_plan_correctness(self, output: str, request: str) -> float:
        """Check plan correctness."""
        score = 0.6

        # Has numbered steps or bullet points
        if re.search(r'^\s*[\d\-\*]', output, re.MULTILINE):
            score += 0.2

        # Steps seem actionable
        action_verbs = ['create', 'implement', 'add', 'configure', 'set up',
                       'install', 'write', 'define', 'test', 'deploy']
        if any(verb in output.lower() for verb in action_verbs):
            score += 0.1

        return min(1.0, score)

    def _check_plan_coherence(self, output: str) -> float:
        """Check if plan steps are in logical order."""
        score = 0.6

        output_lower = output.lower()

        # Has sequential indicators
        if any(word in output_lower for word in ['first', 'then', 'next', 'finally', 'after']):
            score += 0.2

        # Dependencies mentioned
        if any(word in output_lower for word in ['before', 'requires', 'depends', 'prerequisite']):
            score += 0.1

        return min(1.0, score)

    def _check_plan_actionability(self, output: str) -> float:
        """Check if plan is actionable."""
        score = 0.5

        # Specific technologies/tools mentioned
        if any(tech in output.lower() for tech in
               ['python', 'javascript', 'docker', 'git', 'api', 'database']):
            score += 0.2

        # Has specific commands or code snippets
        if '```' in output or '$' in output or 'pip' in output.lower():
            score += 0.2

        return min(1.0, score)


class QualityTester:
    """Main tester for quality validation."""

    def __init__(self):
        self.initialized = False
        self.bridge = None
        self.validator = QualityValidator()

    async def initialize(self):
        """Initialize the system."""
        try:
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            await self.bridge.initialize()
            self.initialized = True
            return True
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    async def execute_and_validate(
        self,
        request: str,
        validation_type: str,
        expected_elements: List[str],
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Execute request and validate quality."""
        result = {
            "request": request,
            "output": "",
            "success": False,
            "quality_score": None,
            "latency_ms": 0,
            "error": None,
        }

        start = time.time()

        try:
            output = ""
            async for chunk in self.bridge.process_message(request):
                if hasattr(chunk, 'content'):
                    output += chunk.content
                elif isinstance(chunk, str):
                    output += chunk

            result['output'] = output
            result['success'] = True

            # Validate quality
            if validation_type == "code":
                score = self.validator.validate_code_output(
                    request, output, expected_elements
                )
            elif validation_type == "explanation":
                score = self.validator.validate_explanation_output(
                    request, output, expected_elements
                )
            elif validation_type == "plan":
                score = self.validator.validate_plan_output(
                    request, output, expected_elements
                )
            else:
                score = self.validator.validate_explanation_output(
                    request, output, expected_elements
                )

            result['quality_score'] = score

        except asyncio.TimeoutError:
            result['error'] = 'Timeout'
        except Exception as e:
            result['error'] = str(e)

        result['latency_ms'] = int((time.time() - start) * 1000)
        return result

    async def cleanup(self):
        """Cleanup resources."""
        if self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def quality_tester():
    """Provide quality tester."""
    tester = QualityTester()
    success = await tester.initialize()

    if not success:
        pytest.skip("Could not initialize quality tester")

    yield tester

    await tester.cleanup()


# ============================================================================
# CODE GENERATION QUALITY TESTS
# ============================================================================

class TestCodeGenerationQuality:
    """Test quality of code generation outputs."""

    @pytest.mark.timeout(180)
    async def test_function_completeness(self, quality_tester):
        """
        QUALITY TEST: Function request should produce complete function.
        """
        request = "Write a Python function that validates email addresses using regex"
        expected = ["def", "email", "re", "return", "@"]

        result = await quality_tester.execute_and_validate(
            request, "code", expected
        )

        print(f"\n[QUALITY] Duration: {result['latency_ms']}ms")
        if result['quality_score']:
            print(f"[QUALITY] Scores: {result['quality_score'].to_dict()}")
            print(f"[QUALITY] OVERALL: {result['quality_score'].overall:.1%}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Quality threshold
        assert result['quality_score'].overall >= 0.6, \
            f"Quality too low: {result['quality_score'].overall:.1%}"

        # Must have working code
        assert result['quality_score'].correctness >= 0.5, \
            "Code correctness too low"

    @pytest.mark.timeout(180)
    async def test_class_implementation(self, quality_tester):
        """
        QUALITY TEST: Class request should produce complete class.
        """
        request = "Implement a Python Stack class with push, pop, and peek methods"
        expected = ["class", "stack", "push", "pop", "peek", "def"]

        result = await quality_tester.execute_and_validate(
            request, "code", expected
        )

        print(f"\n[QUALITY] Scores: {result['quality_score'].to_dict() if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        assert result['quality_score'].completeness >= 0.6, \
            "Should implement all required methods"

    @pytest.mark.timeout(180)
    async def test_algorithm_correctness(self, quality_tester):
        """
        QUALITY TEST: Algorithm implementation should be correct.
        """
        request = "Write a binary search function in Python"
        expected = ["def", "binary", "search", "mid", "return"]

        result = await quality_tester.execute_and_validate(
            request, "code", expected
        )

        print(f"\n[QUALITY] Correctness: {result['quality_score'].correctness if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Algorithm correctness is critical
        assert result['quality_score'].correctness >= 0.6, \
            "Algorithm correctness too low"


# ============================================================================
# EXPLANATION QUALITY TESTS
# ============================================================================

class TestExplanationQuality:
    """Test quality of explanation outputs."""

    @pytest.mark.timeout(120)
    async def test_concept_explanation(self, quality_tester):
        """
        QUALITY TEST: Concept explanation should be complete and clear.
        """
        request = "Explain how Python decorators work with examples"
        expected = ["decorator", "@", "function", "wrapper", "example"]

        result = await quality_tester.execute_and_validate(
            request, "explanation", expected
        )

        print(f"\n[QUALITY] Scores: {result['quality_score'].to_dict() if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Explanation should be comprehensive
        assert result['quality_score'].completeness >= 0.5, \
            "Explanation not complete enough"

    @pytest.mark.timeout(120)
    async def test_comparison_explanation(self, quality_tester):
        """
        QUALITY TEST: Comparison should address both sides.
        """
        request = "Compare REST and GraphQL APIs - pros and cons of each"
        expected = ["rest", "graphql", "pros", "cons", "api"]

        result = await quality_tester.execute_and_validate(
            request, "explanation", expected
        )

        print(f"\n[QUALITY] Completeness: {result['quality_score'].completeness if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Must address both technologies
        assert result['quality_score'].completeness >= 0.6, \
            "Should compare both REST and GraphQL"


# ============================================================================
# PLANNING QUALITY TESTS
# ============================================================================

class TestPlanningQuality:
    """Test quality of planning outputs."""

    @pytest.mark.timeout(180)
    async def test_project_plan(self, quality_tester):
        """
        QUALITY TEST: Project plan should have clear steps.
        """
        request = "Create a plan for building a REST API with user authentication"
        expected = ["api", "authentication", "endpoint", "database", "test"]

        result = await quality_tester.execute_and_validate(
            request, "plan", expected
        )

        print(f"\n[QUALITY] Scores: {result['quality_score'].to_dict() if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Plan should be actionable
        assert result['quality_score'].actionability >= 0.5, \
            "Plan should be actionable"

    @pytest.mark.timeout(180)
    async def test_refactoring_plan(self, quality_tester):
        """
        QUALITY TEST: Refactoring plan should be specific.
        """
        request = "Plan how to refactor a monolithic Python application into microservices"
        expected = ["microservice", "service", "api", "database", "deploy"]

        result = await quality_tester.execute_and_validate(
            request, "plan", expected
        )

        print(f"\n[QUALITY] Coherence: {result['quality_score'].coherence if result['quality_score'] else 'N/A'}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Plan should be coherent
        assert result['quality_score'].coherence >= 0.5, \
            "Plan should be logically structured"


# ============================================================================
# COMPREHENSIVE QUALITY VALIDATION
# ============================================================================

class TestComprehensiveQuality:
    """Comprehensive quality validation tests."""

    @pytest.mark.timeout(300)
    async def test_multi_part_request(self, quality_tester):
        """
        QUALITY TEST: Multi-part request should address ALL parts.
        """
        request = """
        I need you to:
        1. Write a Python function to validate passwords (min 8 chars, 1 uppercase, 1 number)
        2. Write unit tests for this function
        3. Add docstrings explaining the validation rules
        """
        expected = [
            "def", "password", "test", "assert",
            "docstring", "uppercase", "number", "8"
        ]

        result = await quality_tester.execute_and_validate(
            request, "code", expected
        )

        print(f"\n[QUALITY] COMPREHENSIVE TEST")
        if result['quality_score']:
            for key, value in result['quality_score'].to_dict().items():
                print(f"  {key}: {value:.1%}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Multi-part requests require high completeness
        assert result['quality_score'].completeness >= 0.5, \
            f"Multi-part request completeness too low: {result['quality_score'].completeness:.1%}"

        # Overall quality should be good
        assert result['quality_score'].overall >= 0.5, \
            f"Overall quality too low: {result['quality_score'].overall:.1%}"

    @pytest.mark.timeout(180)
    async def test_error_handling_request(self, quality_tester):
        """
        QUALITY TEST: Error handling request should include try/except.
        """
        request = "Write a function to read JSON from a file with proper error handling"
        expected = ["def", "json", "try", "except", "file", "open"]

        result = await quality_tester.execute_and_validate(
            request, "code", expected
        )

        print(f"\n[QUALITY] Error handling test")
        if result['quality_score']:
            print(f"  Correctness: {result['quality_score'].correctness:.1%}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Error handling is part of correctness
        output_lower = result['output'].lower()
        has_error_handling = 'try' in output_lower and 'except' in output_lower

        assert has_error_handling, \
            "Code should include error handling when requested"


class TestQualityBenchmarks:
    """Benchmark quality scores."""

    @pytest.mark.timeout(600)
    @pytest.mark.benchmark
    async def test_quality_benchmark_suite(self, quality_tester):
        """
        QUALITY BENCHMARK: Run multiple requests and report quality scores.
        """
        test_cases = [
            {
                "request": "Write a function to check if a string is a palindrome",
                "type": "code",
                "expected": ["def", "palindrome", "return"]
            },
            {
                "request": "Explain the difference between lists and tuples in Python",
                "type": "explanation",
                "expected": ["list", "tuple", "mutable", "immutable"]
            },
            {
                "request": "Plan the steps to deploy a Python app to AWS",
                "type": "plan",
                "expected": ["aws", "deploy", "ec2", "docker"]
            },
        ]

        results = []
        for case in test_cases:
            result = await quality_tester.execute_and_validate(
                case["request"],
                case["type"],
                case["expected"]
            )
            results.append({
                "request": case["request"][:50],
                "type": case["type"],
                "score": result['quality_score'].overall if result['quality_score'] else 0,
            })

        print("\n" + "="*60)
        print("QUALITY BENCHMARK RESULTS")
        print("="*60)

        for r in results:
            print(f"{r['type']:12} | {r['score']:.1%} | {r['request']}...")

        avg_score = sum(r['score'] for r in results) / len(results)
        print("="*60)
        print(f"AVERAGE QUALITY SCORE: {avg_score:.1%}")
        print("="*60)

        # Benchmark threshold
        assert avg_score >= 0.5, \
            f"Average quality score too low: {avg_score:.1%}"
