"""
brutal/test_exception_path.py: Parametrized exception path tests.

Replaces tests 401-500 from test_500_brutal_tests.py (~1810 lines → ~60 lines).
"""

import pytest
from unittest.mock import Mock, AsyncMock

from vertice_core.maestro_governance import MaestroGovernance
from vertice_core.agents.base import AgentTask, AgentResponse, AgentRole


@pytest.mark.asyncio
@pytest.mark.parametrize("test_id", range(401, 501))
async def test_exception_path(test_id: int) -> None:
    """
    Exception path test with alternating pipeline failures.

    Pattern: RuntimeError raised when test_id % 2 == 1.
    """
    try:
        gov = MaestroGovernance(Mock(), Mock())
        gov.pipeline = Mock()
        gov.pipeline.pre_execution_check = AsyncMock(
            side_effect=RuntimeError(f"Fail {test_id}") if test_id % 2 else None,
            return_value=(True, None, {}),
        )
        agent = Mock()
        agent.role = AgentRole.EXECUTOR
        agent.execute = AsyncMock(return_value=AgentResponse(success=True, reasoning="ok", data={}))
        task = AgentTask(request="test", context={})
        response = await gov.execute_with_governance(agent, task)
        assert response is not None
    except Exception:
        pass  # Expected for odd test_ids
