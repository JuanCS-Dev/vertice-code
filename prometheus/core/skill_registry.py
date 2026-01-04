"""
Skill Registry - Valid Skills for Prometheus Agents.

This module defines the canonical set of valid skills that can be
detected, learned, and mastered by Prometheus agents.

Prevents hallucination by validating skills against this registry.

Author: Vertice Framework
Date: 2026-01-01
"""

from __future__ import annotations

from typing import List, Set, Dict, Optional
from enum import Enum


# =============================================================================
# SKILL CATEGORIES
# =============================================================================

class SkillCategory(str, Enum):
    """Categories of skills."""
    PYTHON = "python"
    ASYNC = "async"
    TESTING = "testing"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    DEVOPS = "devops"
    DATA = "data"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"


# =============================================================================
# VALID SKILLS REGISTRY
# =============================================================================

VALID_SKILLS: Set[str] = {
    # Python Basics
    "python_basics",
    "python_syntax",
    "python_data_structures",
    "python_functions",
    "python_classes",
    "python_modules",
    "python_exceptions",
    "python_comprehensions",
    "python_decorators",
    "python_generators",
    "python_context_managers",

    # Async Programming
    "async_programming",
    "async_basics",
    "asyncio_tasks",
    "asyncio_locks",
    "asyncio_queues",
    "async_generators",
    "async_context_managers",
    "concurrent_programming",
    "threading",
    "multiprocessing",

    # Testing
    "testing",
    "unit_testing",
    "integration_testing",
    "e2e_testing",
    "pytest_basics",
    "pytest_fixtures",
    "pytest_parametrize",
    "mocking",
    "test_coverage",
    "mutation_testing",
    "property_based_testing",

    # Debugging
    "debugging",
    "debugging_basics",
    "breakpoints",
    "logging",
    "tracing",
    "profiling",
    "memory_debugging",
    "stack_traces",
    "error_analysis",

    # Error Handling
    "error_handling",
    "exception_handling",
    "custom_exceptions",
    "error_recovery",
    "graceful_degradation",
    "retry_logic",

    # File Operations
    "file_operations",
    "file_reading",
    "file_writing",
    "path_handling",
    "directory_operations",
    "file_streaming",

    # API Design
    "api_design",
    "rest_api",
    "graphql",
    "api_versioning",
    "api_documentation",
    "openapi_spec",
    "request_validation",
    "response_formatting",

    # Architecture
    "architecture",
    "design_patterns",
    "solid_principles",
    "clean_architecture",
    "microservices",
    "monolith",
    "event_driven",
    "cqrs",
    "domain_driven_design",

    # DevOps
    "devops",
    "ci_cd",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "monitoring",
    "alerting",
    "deployment",
    "rollback",

    # Data
    "data_processing",
    "data_validation",
    "data_transformation",
    "pandas",
    "numpy",
    "sql",
    "nosql",
    "data_modeling",
    "etl",

    # Security
    "security",
    "authentication",
    "authorization",
    "encryption",
    "input_validation",
    "sql_injection_prevention",
    "xss_prevention",
    "secure_coding",

    # Documentation
    "documentation",
    "docstrings",
    "readme_writing",
    "api_documentation",
    "code_comments",
    "architecture_docs",

    # Performance
    "performance",
    "optimization",
    "caching",
    "profiling",
    "memory_optimization",
    "algorithm_complexity",
    "database_optimization",

    # Code Quality
    "code_quality",
    "code_review",
    "refactoring",
    "linting",
    "type_hints",
    "static_analysis",

    # Version Control
    "git",
    "git_basics",
    "branching",
    "merging",
    "rebasing",
    "pull_requests",

    # Frameworks
    "fastapi",
    "django",
    "flask",
    "pydantic",
    "sqlalchemy",
    "textual",
    "rich",
}


# =============================================================================
# SKILL ALIASES (Map common variations to canonical names)
# =============================================================================

SKILL_ALIASES: Dict[str, str] = {
    # Python variations
    "python": "python_basics",
    "py": "python_basics",
    "python3": "python_basics",

    # Async variations
    "async": "async_programming",
    "asyncio": "async_programming",
    "asynchronous": "async_programming",

    # Testing variations
    "test": "testing",
    "tests": "testing",
    "unittest": "unit_testing",
    "unit_test": "unit_testing",
    "e2e": "e2e_testing",
    "end_to_end": "e2e_testing",

    # Debug variations
    "debug": "debugging",

    # Error variations
    "errors": "error_handling",
    "exceptions": "exception_handling",

    # File variations
    "files": "file_operations",
    "io": "file_operations",

    # API variations
    "api": "api_design",
    "rest": "rest_api",

    # Architecture variations
    "arch": "architecture",
    "patterns": "design_patterns",
    "solid": "solid_principles",
    "ddd": "domain_driven_design",

    # DevOps variations
    "ci": "ci_cd",
    "cd": "ci_cd",
    "k8s": "kubernetes",
    "deploy": "deployment",

    # Data variations
    "data": "data_processing",
    "db": "sql",
    "database": "sql",

    # Security variations
    "auth": "authentication",
    "authz": "authorization",
    "authn": "authentication",

    # Docs variations
    "docs": "documentation",
    "doc": "documentation",

    # Perf variations
    "perf": "performance",
    "optimize": "optimization",
    "cache": "caching",
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical form.

    Args:
        skill: Raw skill name (may be alias)

    Returns:
        Canonical skill name
    """
    # Lowercase and replace spaces/hyphens with underscores
    normalized = skill.lower().strip().replace("-", "_").replace(" ", "_")

    # Check aliases
    if normalized in SKILL_ALIASES:
        return SKILL_ALIASES[normalized]

    return normalized


def is_valid_skill(skill: str) -> bool:
    """Check if a skill is valid.

    Args:
        skill: Skill name to validate

    Returns:
        True if skill is valid
    """
    normalized = normalize_skill(skill)
    return normalized in VALID_SKILLS


def validate_skills(detected_skills: List[str]) -> List[str]:
    """Filter and normalize a list of detected skills.

    Only returns skills that exist in the registry.
    This prevents hallucination of non-existent skills.

    Args:
        detected_skills: Raw list of detected skill names

    Returns:
        List of valid, normalized skill names
    """
    valid = []
    for skill in detected_skills:
        normalized = normalize_skill(skill)
        if normalized in VALID_SKILLS:
            valid.append(normalized)
    return list(set(valid))  # Remove duplicates


def get_invalid_skills(detected_skills: List[str]) -> List[str]:
    """Get skills that are not in the registry.

    Useful for logging/debugging hallucinated skills.

    Args:
        detected_skills: Raw list of detected skill names

    Returns:
        List of invalid skill names
    """
    invalid = []
    for skill in detected_skills:
        normalized = normalize_skill(skill)
        if normalized not in VALID_SKILLS:
            invalid.append(skill)
    return invalid


def get_skills_by_category(category: SkillCategory) -> List[str]:
    """Get all skills in a category.

    Args:
        category: Skill category

    Returns:
        List of skills in that category
    """
    category_prefix = category.value
    return [s for s in VALID_SKILLS if s.startswith(category_prefix)]


def suggest_similar_skill(invalid_skill: str) -> Optional[str]:
    """Suggest a similar valid skill for an invalid one.

    Args:
        invalid_skill: Invalid skill name

    Returns:
        Similar valid skill or None
    """
    normalized = normalize_skill(invalid_skill)

    # Check if any valid skill contains this as substring
    for valid in VALID_SKILLS:
        if normalized in valid or valid in normalized:
            return valid

    # Check prefix match
    for valid in VALID_SKILLS:
        if valid.startswith(normalized[:4]):
            return valid

    return None


# =============================================================================
# SKILL DIFFICULTY LEVELS
# =============================================================================

SKILL_DIFFICULTY: Dict[str, int] = {
    # Level 1 - Beginner
    "python_basics": 1,
    "python_syntax": 1,
    "file_reading": 1,
    "file_writing": 1,
    "logging": 1,
    "git_basics": 1,

    # Level 2 - Elementary
    "python_functions": 2,
    "python_classes": 2,
    "error_handling": 2,
    "unit_testing": 2,
    "debugging_basics": 2,

    # Level 3 - Intermediate
    "python_decorators": 3,
    "async_basics": 3,
    "pytest_fixtures": 3,
    "api_design": 3,
    "design_patterns": 3,

    # Level 4 - Advanced
    "python_generators": 4,
    "async_programming": 4,
    "mocking": 4,
    "caching": 4,
    "clean_architecture": 4,

    # Level 5 - Expert
    "asyncio_locks": 5,
    "mutation_testing": 5,
    "microservices": 5,
    "domain_driven_design": 5,
    "kubernetes": 5,
}


def get_skill_difficulty(skill: str) -> int:
    """Get difficulty level of a skill (1-5).

    Args:
        skill: Skill name

    Returns:
        Difficulty level (1=beginner, 5=expert), default 3
    """
    normalized = normalize_skill(skill)
    return SKILL_DIFFICULTY.get(normalized, 3)


__all__ = [
    "SkillCategory",
    "VALID_SKILLS",
    "SKILL_ALIASES",
    "normalize_skill",
    "is_valid_skill",
    "validate_skills",
    "get_invalid_skills",
    "get_skills_by_category",
    "suggest_similar_skill",
    "SKILL_DIFFICULTY",
    "get_skill_difficulty",
]
