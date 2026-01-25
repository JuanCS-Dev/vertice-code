"""
Skill detection for Executor Agent.

Maps solution patterns to canonical skills from the skill registry.
Prevents hallucination of non-existent skills through validation.
"""

from typing import List, Set

# Import skill registry for validation
try:
    from prometheus.core.skill_registry import validate_skills, is_valid_skill
except ImportError:
    # Fallback if skill_registry not available
    def validate_skills(skills: List[str]) -> List[str]:
        return skills

    def is_valid_skill(skill: str) -> bool:
        return True


# Skill detection patterns - MAPPED TO VALID SKILLS from registry
# Each pattern maps to a canonical skill name from VALID_SKILLS
SKILL_PATTERNS = {
    # Python skills
    "python_basics": ["def ", "class ", "import ", "```python"],
    "python_functions": ["def ", "lambda", "return "],
    "python_classes": ["class ", "self.", "__init__"],
    "python_decorators": ["@", "decorator"],
    "python_comprehensions": ["[", "for", "in", "]"],
    # Async skills
    "async_programming": ["async ", "await ", "asyncio"],
    "async_basics": ["async def", "await"],
    # Testing skills
    "testing": ["test", "assert", "pytest", "unittest"],
    "unit_testing": ["test_", "assert", "assertEqual"],
    "mocking": ["mock", "patch", "MagicMock"],
    # Debugging skills
    "debugging": ["debug", "breakpoint", "pdb"],
    "error_handling": ["try:", "except", "raise"],
    "logging": ["logging", "log.", "logger"],
    # Architecture skills
    "design_patterns": ["factory", "singleton", "observer", "pattern"],
    "architecture": ["module", "component", "layer"],
    "refactoring": ["refactor", "extract", "rename"],
    # Performance skills
    "optimization": ["optimize", "cache", "efficient"],
    "caching": ["cache", "memoize", "@lru_cache"],
    "profiling": ["profile", "timeit", "cProfile"],
    # Data skills
    "data_processing": ["pandas", "numpy", "data"],
    "sql": ["SELECT", "INSERT", "sql", "query"],
    # Documentation
    "documentation": ["docstring", '"""', "'''"],
    "code_comments": ["#", "comment"],
}


class SkillDetector:
    """
    Detects skills demonstrated in solutions.

    Uses pattern matching against SKILL_PATTERNS and validates
    against the skill registry to prevent hallucination.
    """

    def __init__(self):
        """Initialize skill detector."""
        self.patterns = SKILL_PATTERNS

    def identify_skills(self, solution: str, expected_skills: List[str]) -> List[str]:
        """
        Identify skills demonstrated in the solution.

        Args:
            solution: The solution text to analyze
            expected_skills: Skills expected from the task

        Returns:
            List of validated skill names
        """
        demonstrated = self._detect_patterns(solution)
        demonstrated.update(self._validate_expected(expected_skills))
        return validate_skills(list(demonstrated))

    def _detect_patterns(self, solution: str) -> Set[str]:
        """
        Detect skills using pattern matching.

        Args:
            solution: The solution text to analyze

        Returns:
            Set of detected skill names (validated)
        """
        demonstrated = set()
        solution_lower = solution.lower()

        for skill, keywords in self.patterns.items():
            if any(kw in solution_lower or kw in solution for kw in keywords):
                # Only add if it's a valid skill
                if is_valid_skill(skill):
                    demonstrated.add(skill)

        return demonstrated

    def _validate_expected(self, expected_skills: List[str]) -> Set[str]:
        """
        Validate expected skills from task.

        Args:
            expected_skills: Skills expected from the task

        Returns:
            Set of validated expected skills
        """
        validated = set()
        for skill in expected_skills:
            if is_valid_skill(skill):
                validated.add(skill)
        return validated
