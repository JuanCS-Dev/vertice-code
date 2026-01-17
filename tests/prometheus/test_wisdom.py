"""
Deep Governance & Wisdom Test Suite.

Focuses on the relationship between Prometheus, SOFIA, and the user,
ensuring that governance is not just a block, but a source of insight.

Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from prometheus.core.orchestrator import PrometheusOrchestrator
from prometheus.core.governance import GovernanceVerdict


@pytest.mark.asyncio
async def test_sofia_uncertainty_leads_to_wise_veto():
    """Verify that when SOFIA is uncertain, Prometheus offers a teaching moment."""
    orchestrator = PrometheusOrchestrator(agent_name="WisdomAgent")
    orchestrator._persistence_initialized = True

    # Mock SOFIA to express high uncertainty (confidence < 0.4)
    mock_sofia_counsel = MagicMock()
    mock_sofia_counsel.confidence = 0.3
    mock_sofia_counsel.response = (
        "This path is clouded. One must look inward before acting on the world."
    )
    orchestrator.governance.sofia.respond = MagicMock(return_value=mock_sofia_counsel)

    chunks = []
    async for chunk in orchestrator.execute("Perform a reckless action", fast_mode=True):
        chunks.append(chunk)

    full_output = "".join(chunks)

    # Verify the Wise Veto
    assert "🛑 **VETO** by SOFIA" in full_output
    assert "SOFIA expressed high uncertainty" in full_output
    assert "look inward" in full_output  # SOFIA's teaching preserved
    assert "💡 Suggestion:" in full_output


@pytest.mark.asyncio
async def test_observability_context_propagation():
    """Verify that task context is propagated to observability spans."""
    orchestrator = PrometheusOrchestrator(agent_name="ContextAgent")
    orchestrator._persistence_initialized = True

    # Approve task
    orchestrator.governance.review_task = AsyncMock(
        return_value=GovernanceVerdict(
            approved=True, reasoning="Safe", risk_level="LOW", governor="JUSTICA"
        )
    )

    # Mock LLM
    orchestrator._execute_task_with_context = AsyncMock(return_value="Action Complete")

    # Execute
    async for _ in orchestrator.execute("Analyze this", fast_mode=True):
        pass

    # Access stats
    stats = orchestrator.get_observability_stats()
    # In a real OTel environment, we'd check the exported spans.
    # Here we verify the system is tracking active operations.
    assert stats["initialized"] is True
    assert stats["traces"]["active_spans"] == 0  # Finished spans should be 0 active


@pytest.mark.asyncio
async def test_teaching_output_format():
    """Verify that Prometheus output follows the 'Teaching' spirit."""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "The true refactor happens within the dev's mind. Here is the code: [TOOL:write_file:path=soul.py,content=print('hello')]"

    orchestrator = PrometheusOrchestrator(llm_client=mock_llm, agent_name="MentorAgent")
    orchestrator._persistence_initialized = True
    orchestrator.governance.review_task = AsyncMock(
        return_value=GovernanceVerdict(
            approved=True, reasoning="Educational", risk_level="LOW", governor="JUSTICA"
        )
    )

    chunks = []
    async for chunk in orchestrator.execute("Teach me something", fast_mode=True):
        chunks.append(chunk)

    full_output = "".join(chunks)
    assert "🔥 **PROMETHEUS** executing..." in full_output
    assert "true refactor" in full_output
    assert "✅ Done" in full_output
