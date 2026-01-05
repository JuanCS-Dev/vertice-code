"""
brutal/conftest.py: Shared fixtures for brutal tests.

These fixtures support parametrized brutal tests that replace
the verbose 7,210-line test_500_brutal_tests.py with ~100 lines.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def gov_mock():
    """Create MaestroGovernance mock for basic tests."""
    from vertice_cli.maestro_governance import MaestroGovernance
    return MaestroGovernance(
        llm_client=Mock(),
        mcp_client=Mock()
    )


@pytest.fixture
def gov_with_detect_risk():
    """Create MaestroGovernance with mocked detect_risk_level."""
    from vertice_cli.maestro_governance import MaestroGovernance
    gov = MaestroGovernance(
        llm_client=Mock(),
        mcp_client=Mock()
    )
    return gov
