"""
Unit tests for the skill_registry module.
"""

from prometheus.core.skill_registry import (
    normalize_skill,
    is_valid_skill,
    validate_skills,
    get_invalid_skills,
    suggest_similar_skill,
    get_skill_difficulty,
)


def test_normalize_skill():
    """Test skill normalization."""
    assert normalize_skill("  PyThon-Basics  ") == "python_basics"
    assert normalize_skill("async") == "async_programming"
    assert normalize_skill("e2e") == "e2e_testing"


def test_is_valid_skill():
    """Test skill validation."""
    assert is_valid_skill("python_basics") is True
    assert is_valid_skill("PyTest Fixtures") is True
    assert is_valid_skill("invalid_skill") is False


def test_validate_skills():
    """Test filtering and normalization of a skill list."""
    skills = ["python_basics", "Invalid Skill", "e2e", "python_basics"]
    validated = validate_skills(skills)
    assert "python_basics" in validated
    assert "e2e_testing" in validated
    assert "Invalid Skill" not in validated
    assert len(validated) == 2  # Duplicates should be removed


def test_get_invalid_skills():
    """Test detection of invalid skills."""
    skills = ["python_basics", "Invalid Skill", "another_bad_one"]
    invalid = get_invalid_skills(skills)
    assert "Invalid Skill" in invalid
    assert "another_bad_one" in invalid
    assert "python_basics" not in invalid


def test_suggest_similar_skill():
    """Test suggestion of similar valid skills."""
    assert suggest_similar_skill("python") == "python_basics"
    assert suggest_similar_skill("python-syntax") == "python_syntax"
    assert suggest_similar_skill("testingg") == "testing"
    assert suggest_similar_skill("nonexistent") is None


def test_get_skill_difficulty():
    """Test getting the difficulty of a skill."""
    assert get_skill_difficulty("python_basics") == 1
    assert get_skill_difficulty("async_programming") == 4
    assert get_skill_difficulty("unknown_skill") == 3  # Default value
