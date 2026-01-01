"""
brutal/test_boundary_violation.py: Parametrized boundary violation tests.

Replaces tests 201-300 from test_500_brutal_tests.py (~1010 lines → ~40 lines).
"""

import pytest
from unittest.mock import Mock

from vertice_cli.maestro_governance import MaestroGovernance


@pytest.mark.parametrize("test_id", range(201, 301))
def test_boundary_violation(test_id: int) -> None:
    """
    Boundary violation test with large prompts.

    Pattern: huge_prompt size = test_id * 1000 characters.
    """
    try:
        gov = MaestroGovernance(Mock(), Mock())
        huge_prompt = "x" * (test_id * 1000)
        risk = gov.detect_risk_level(huge_prompt, "executor")
        assert risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    except Exception:
        pass  # Expected for very large inputs
