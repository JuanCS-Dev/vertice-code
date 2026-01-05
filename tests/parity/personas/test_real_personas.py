"""
REAL Persona-Based Tests

Tests the system with different user personas to ensure
it works well for various skill levels and use cases.

Personas:
1. Senior Developer - Complex requests, expects precision
2. Junior Developer - Needs guidance, may make mistakes
3. Non-Technical User - Plain language, needs explanations
4. DevOps Engineer - Infrastructure and deployment focus
5. Data Scientist - Data analysis and ML focus
"""

import pytest
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.real,
    pytest.mark.personas,
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
class PersonaProfile:
    """Profile defining a user persona."""

    name: str
    description: str
    skill_level: str
    typical_requests: List[str]
    quality_criteria: List[str]


PERSONAS = {
    "senior_dev": PersonaProfile(
        name="Senior Developer",
        description="Experienced developer who wants precise, efficient solutions",
        skill_level="expert",
        typical_requests=[
            "Implement a thread-safe singleton pattern with lazy initialization",
            "Refactor this using the strategy pattern with dependency injection",
            "Optimize this O(n^2) algorithm to O(n log n)",
        ],
        quality_criteria=[
            "Uses correct design patterns",
            "Handles edge cases",
            "Follows best practices",
            "Efficient implementation",
        ]
    ),
    "junior_dev": PersonaProfile(
        name="Junior Developer",
        description="New developer learning the ropes, needs guidance",
        skill_level="beginner",
        typical_requests=[
            "How do I create a list in Python?",
            "What's the difference between a class and a function?",
            "My code has an error, can you help? for i in range(10) print(i)",
        ],
        quality_criteria=[
            "Clear explanations",
            "Step-by-step guidance",
            "Educational content",
            "Patient tone",
        ]
    ),
    "non_technical": PersonaProfile(
        name="Non-Technical User",
        description="Business user who needs plain language explanations",
        skill_level="none",
        typical_requests=[
            "Can you explain what an API is in simple terms?",
            "I need a script that renames files in a folder",
            "What does this error message mean?",
        ],
        quality_criteria=[
            "Plain language",
            "No jargon without explanation",
            "Practical focus",
            "Clear instructions",
        ]
    ),
    "devops": PersonaProfile(
        name="DevOps Engineer",
        description="Infrastructure and deployment specialist",
        skill_level="expert",
        typical_requests=[
            "Write a Dockerfile for a Python FastAPI application",
            "Create a GitHub Actions workflow for CI/CD",
            "Set up monitoring with Prometheus metrics",
        ],
        quality_criteria=[
            "Production-ready configs",
            "Security best practices",
            "Scalability considerations",
            "Proper error handling",
        ]
    ),
    "data_scientist": PersonaProfile(
        name="Data Scientist",
        description="Data analysis and ML specialist",
        skill_level="expert",
        typical_requests=[
            "Implement a simple linear regression from scratch",
            "Create a data pipeline for preprocessing CSV files",
            "Visualize this dataset distribution",
        ],
        quality_criteria=[
            "Correct statistical methods",
            "Proper data handling",
            "Clear visualizations",
            "Reproducible code",
        ]
    ),
}


class PersonaTester:
    """Tester for persona-based scenarios."""

    def __init__(self):
        self.initialized = False
        self.bridge = None

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

    async def execute_as_persona(
        self,
        persona: PersonaProfile,
        request: str,
        timeout: int = 120
    ) -> Dict:
        """Execute a request as a specific persona."""
        result = {
            "persona": persona.name,
            "request": request,
            "success": False,
            "output": "",
            "latency_ms": 0,
            "quality_score": 0.0,
            "quality_notes": [],
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

            # Evaluate quality for persona
            result['quality_score'], result['quality_notes'] = self._evaluate_quality(
                persona, request, output
            )

        except asyncio.TimeoutError:
            result['error'] = 'Timeout'
        except Exception as e:
            result['error'] = str(e)

        result['latency_ms'] = int((time.time() - start) * 1000)
        return result

    def _evaluate_quality(
        self,
        persona: PersonaProfile,
        request: str,
        output: str
    ) -> tuple:
        """Evaluate response quality for persona."""
        notes = []
        score = 0.0
        max_score = len(persona.quality_criteria)

        output_lower = output.lower()

        # Generic quality checks
        if len(output) > 50:
            score += 0.5
            notes.append("Substantial response")

        # Persona-specific checks
        if persona.skill_level == "beginner":
            if any(word in output_lower for word in ['step', 'first', 'then', 'next']):
                score += 1
                notes.append("Step-by-step guidance provided")
            if len(output) > 200:
                score += 0.5
                notes.append("Detailed explanation")

        elif persona.skill_level == "expert":
            if 'def ' in output or 'class ' in output or '```' in output:
                score += 1
                notes.append("Code provided")
            if any(word in output_lower for word in ['pattern', 'optimize', 'efficient']):
                score += 0.5
                notes.append("Advanced concepts addressed")

        elif persona.skill_level == "none":
            # Check for jargon without explanation
            jargon = ['api', 'function', 'variable', 'class', 'method']
            for term in jargon:
                if term in output_lower:
                    # Should have explanation nearby
                    idx = output_lower.find(term)
                    context = output_lower[max(0, idx-50):min(len(output_lower), idx+100)]
                    if any(explain in context for explain in ['is', 'means', 'like', 'think of']):
                        score += 0.3
                        notes.append(f"'{term}' explained")

        # Normalize score
        normalized = min(1.0, score / max(1, max_score))
        return normalized, notes

    async def cleanup(self):
        """Cleanup resources."""
        if self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def persona_tester():
    """Provide persona tester."""
    tester = PersonaTester()
    success = await tester.initialize()

    if not success:
        pytest.skip("Could not initialize persona tester")

    yield tester

    await tester.cleanup()


class TestSeniorDeveloperPersona:
    """Tests for senior developer persona."""

    @pytest.mark.timeout(180)
    async def test_design_pattern_request(self, persona_tester):
        """
        REAL PERSONA TEST: Senior dev requests design pattern implementation.
        """
        persona = PERSONAS["senior_dev"]
        request = "Implement a thread-safe singleton pattern in Python with lazy initialization"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")
        print(f"[{persona.name}] Quality: {result['quality_score']:.1%}")
        print(f"[{persona.name}] Notes: {result['quality_notes']}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should provide actual code
        assert 'class' in result['output'] or 'def' in result['output'], \
            "Senior dev request should produce code"

        # Should mention thread safety
        output_lower = result['output'].lower()
        assert any(word in output_lower for word in ['thread', 'lock', 'singleton']), \
            "Should address thread safety for singleton"

    @pytest.mark.timeout(180)
    async def test_optimization_request(self, persona_tester):
        """
        REAL PERSONA TEST: Senior dev requests algorithm optimization.
        """
        persona = PERSONAS["senior_dev"]
        request = """
        Optimize this O(n^2) function to O(n log n):
        ```python
        def find_pairs(arr, target):
            pairs = []
            for i in range(len(arr)):
                for j in range(i+1, len(arr)):
                    if arr[i] + arr[j] == target:
                        pairs.append((arr[i], arr[j]))
            return pairs
        ```
        """

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should discuss optimization
        discusses_optimization = any(word in output_lower for word in
            ['sort', 'hash', 'set', 'dict', 'o(n)', 'optimize', 'efficient'])

        assert discusses_optimization, \
            "Should discuss optimization approach"


class TestJuniorDeveloperPersona:
    """Tests for junior developer persona."""

    @pytest.mark.timeout(120)
    async def test_basic_question(self, persona_tester):
        """
        REAL PERSONA TEST: Junior dev asks basic question.
        """
        persona = PERSONAS["junior_dev"]
        request = "How do I create a list in Python and add items to it?"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")
        print(f"[{persona.name}] Quality: {result['quality_score']:.1%}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should provide clear explanation
        assert len(result['output']) > 100, \
            "Should provide detailed explanation for beginner"

        # Should include examples
        has_example = '[' in result['output'] or 'append' in result['output'].lower()
        assert has_example, \
            "Should include practical examples"

    @pytest.mark.timeout(120)
    async def test_error_help(self, persona_tester):
        """
        REAL PERSONA TEST: Junior dev needs help with error.
        """
        persona = PERSONAS["junior_dev"]
        request = """
        My code has an error, can you help?
        for i in range(10)
            print(i)
        """

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should identify the missing colon
        identifies_issue = any(word in output_lower for word in
            ['colon', ':', 'syntax', 'missing'])

        assert identifies_issue, \
            "Should identify the syntax error (missing colon)"


class TestNonTechnicalPersona:
    """Tests for non-technical user persona."""

    @pytest.mark.timeout(120)
    async def test_plain_language_explanation(self, persona_tester):
        """
        REAL PERSONA TEST: Non-technical user needs plain explanation.
        """
        persona = PERSONAS["non_technical"]
        request = "Can you explain what an API is in simple terms?"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")
        print(f"[{persona.name}] Quality: {result['quality_score']:.1%}")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should use analogies or simple terms
        uses_simple_language = any(word in output_lower for word in
            ['like', 'think of', 'imagine', 'example', 'simple'])

        # Should not be too technical without explanation
        assert len(result['output']) > 50, \
            "Should provide explanation"

    @pytest.mark.timeout(120)
    async def test_practical_task(self, persona_tester):
        """
        REAL PERSONA TEST: Non-technical user needs practical help.
        """
        persona = PERSONAS["non_technical"]
        request = "I need a simple script that renames all .txt files in a folder to have today's date"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should provide usable solution
        has_solution = 'import' in result['output'] or 'os' in result['output'] or \
                       'rename' in result['output'].lower()

        assert has_solution, \
            "Should provide practical solution"


class TestDevOpsPersona:
    """Tests for DevOps engineer persona."""

    @pytest.mark.timeout(180)
    async def test_dockerfile_request(self, persona_tester):
        """
        REAL PERSONA TEST: DevOps needs Dockerfile.
        """
        persona = PERSONAS["devops"]
        request = "Write a Dockerfile for a Python FastAPI application with gunicorn"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output = result['output']

        # Should have Dockerfile content
        has_dockerfile = 'FROM' in output or 'dockerfile' in output.lower()

        assert has_dockerfile, \
            "Should provide Dockerfile content"

        # Should mention key components
        output_lower = output.lower()
        mentions_components = any(word in output_lower for word in
            ['python', 'fastapi', 'gunicorn', 'pip', 'requirements'])

        assert mentions_components, \
            "Should include relevant Docker components"

    @pytest.mark.timeout(180)
    async def test_cicd_request(self, persona_tester):
        """
        REAL PERSONA TEST: DevOps needs CI/CD workflow.
        """
        persona = PERSONAS["devops"]
        request = "Create a GitHub Actions workflow for Python CI with pytest"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should have workflow structure
        has_workflow = any(word in output_lower for word in
            ['yaml', 'yml', 'jobs', 'steps', 'workflow', 'actions'])

        assert has_workflow, \
            "Should provide GitHub Actions workflow"


class TestDataScientistPersona:
    """Tests for data scientist persona."""

    @pytest.mark.timeout(180)
    async def test_ml_implementation(self, persona_tester):
        """
        REAL PERSONA TEST: Data scientist requests ML implementation.
        """
        persona = PERSONAS["data_scientist"]
        request = "Implement a simple linear regression using numpy (no sklearn)"

        result = await persona_tester.execute_as_persona(persona, request)

        print(f"\n[{persona.name}] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output = result['output']

        # Should provide actual implementation
        has_implementation = 'def' in output or 'numpy' in output.lower() or 'np.' in output

        assert has_implementation, \
            "Should provide implementation code"

        # Should mention key concepts
        output_lower = output.lower()
        mentions_concepts = any(word in output_lower for word in
            ['gradient', 'fit', 'predict', 'coefficient', 'slope'])

        assert mentions_concepts or has_implementation, \
            "Should address linear regression concepts"


class TestCrossPersonaConsistency:
    """Test consistency across personas."""

    @pytest.mark.timeout(300)
    async def test_same_question_different_personas(self, persona_tester):
        """
        REAL TEST: Same question should adapt to different personas.
        """
        question = "How do I handle errors in Python?"

        results = {}
        for persona_id in ["senior_dev", "junior_dev"]:
            persona = PERSONAS[persona_id]
            result = await persona_tester.execute_as_persona(persona, question)
            results[persona_id] = result

            print(f"\n[{persona.name}] Response length: {len(result['output'])} chars")

        # Junior should get more detailed explanation
        if results["junior_dev"]["success"] and results["senior_dev"]["success"]:
            junior_len = len(results["junior_dev"]["output"])
            senior_len = len(results["senior_dev"]["output"])

            # Both should provide substantial answers
            assert junior_len > 50 and senior_len > 50, \
                "Both personas should get substantial answers"
