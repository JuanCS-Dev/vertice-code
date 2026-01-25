"""
Testing Module - Intelligent Test Generation and Quality Analysis.

This module provides comprehensive testing capabilities:
- Unit test generation (pytest-style)
- Coverage analysis (pytest-cov integration)
- Mutation testing (mutmut integration)
- Flaky test detection
- Test quality scoring (0-100)

Architecture:
    - models.py: Type-safe data structures (enums, dataclasses)
    - generators.py: Pure functions for test generation
    - analyzers.py: Coverage, mutation, flaky detection
    - scoring.py: Quality scoring system
    - prompts.py: LLM system prompts
    - agent.py: TestRunnerAgent orchestrator

Usage:
    from vertice_core.agents.testing import TestRunnerAgent, create_testing_agent

    agent = create_testing_agent(llm_client, mcp_client)
    response = await agent.execute(task)

Philosophy (Boris Cherny):
    "Tests are executable specifications. If it's not tested, it's broken."
"""

# Models
from .models import (
    TestingFramework,
)

# Generators
from .generators import (
    generate_test_suite,
    generate_function_tests,
    generate_class_tests,
    generate_tui_tests,
)

# Analyzers
from .analyzers import (
    CoverageAnalyzer,
    MutationAnalyzer,
    FlakyDetector,
)

# Scoring
from .scoring import (
    QualityScorer,
    score_to_grade,
)

# Prompts
from .prompts import TESTING_SYSTEM_PROMPT

# Agent
from .agent import (
    TestRunnerAgent,
    create_testing_agent,
)

__all__ = [
    # Models
    "TestingFramework",
    "TestType",
    "TestCase",
    "TestCoverageReport",
    "TestMutationResult",
    "TestFlakyTest",
    # Generators
    "generate_test_suite",
    "generate_function_tests",
    "generate_class_tests",
    "generate_tui_tests",
    # Analyzers
    "CoverageAnalyzer",
    "MutationAnalyzer",
    "FlakyDetector",
    # Scoring
    "QualityScorer",
    "score_to_grade",
    # Prompts
    "TESTING_SYSTEM_PROMPT",
    # Agent
    "TestRunnerAgent",
    "create_testing_agent",
]
