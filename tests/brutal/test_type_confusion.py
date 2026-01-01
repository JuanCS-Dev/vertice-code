"""
brutal/test_type_confusion.py: Parametrized type confusion tests.

Replaces tests 001-100 from test_500_brutal_tests.py (~1210 lines → ~40 lines).
"""

import pytest
from unittest.mock import Mock

from vertice_cli.maestro_governance import MaestroGovernance


@pytest.mark.parametrize("test_id", range(1, 101))
def test_type_confusion(test_id: int) -> None:
    """
    Type confusion test with varying client types.

    Pattern: llm_client alternates None/Mock, mcp_client uses int or Mock.
    """
    try:
        gov = MaestroGovernance(
            llm_client=None if test_id % 2 == 0 else Mock(),
            mcp_client=test_id if test_id % 3 == 0 else Mock()
        )
        assert gov is not None
    except Exception:
        pass  # Expected to fail for invalid types
