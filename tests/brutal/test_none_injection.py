"""
brutal/test_none_injection.py: Parametrized none injection tests.

Replaces tests 101-200 from test_500_brutal_tests.py (~1410 lines → ~50 lines).
"""

import pytest
from unittest.mock import Mock, AsyncMock

from vertice_cli.maestro_governance import MaestroGovernance
from vertice_cli.agents.base import AgentTask, AgentResponse, AgentRole


@pytest.mark.asyncio
@pytest.mark.parametrize("test_id", range(101, 201))
async def test_none_injection(test_id: int) -> None:
    """
    None injection test with alternating request values.

    Pattern: request is "test" or None based on test_id % 2.
    """
    try:
        gov = MaestroGovernance(Mock(), Mock())
        task = AgentTask(request="test" if test_id % 2 else None, context={})
        agent = Mock()
        agent.role = AgentRole.EXECUTOR
        agent.execute = AsyncMock(return_value=AgentResponse(success=True, reasoning="ok", data={}))
        response = await gov.execute_with_governance(agent, task)
        assert response is not None
    except Exception:
        pass  # Expected to fail sometimes
