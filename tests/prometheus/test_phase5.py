"""
Test Prometheus Phase 5: Observability & Governance - Real LLM.

Uses real LLM connectivity to validate the entire pipeline with
personality, governance, and observability.
"""

import pytest
from unittest.mock import AsyncMock

from prometheus.core.orchestrator import PrometheusOrchestrator
from prometheus.core.governance import GovernanceVerdict
from prometheus.core.llm_adapter import PrometheusLLMAdapter
from vertice_cli.core.providers.vertex_ai import VertexAIProvider


@pytest.mark.asyncio
async def test_full_pipeline_with_real_llm():
    """Verify that the agent works end-to-end with real LLM and personality."""

    # Initialize real LLM (Vertex AI / Gemini 2.5 Pro)
    vertex_provider = VertexAIProvider(model_name="pro")
    llm_adapter = PrometheusLLMAdapter(vertex_provider=vertex_provider, enable_thinking=True)

    orchestrator = PrometheusOrchestrator(llm_client=llm_adapter, agent_name="SymbiosisAgent")
    orchestrator._persistence_initialized = True  # Skip DB init for this test

    # Mock Governance to APPROVE (we want to see the LLM output)
    orchestrator.governance.review_task = AsyncMock(
        return_value=GovernanceVerdict(
            approved=True, reasoning="Safe task for testing", risk_level="LOW", governor="JUSTICA"
        )
    )

    # Execute a simple task
    task = "Explain the importance of symbiosis in 10 words."
    chunks = []
    async for chunk in orchestrator.execute(task, fast_mode=True):
        chunks.append(chunk)

    full_output = "".join(chunks)

    # Verify Personality
    assert "🔥 **PROMETHEUS** executing..." in full_output
    assert "✅ Done in" in full_output

    # Verify Content (LLM should have generated something)
    assert len(full_output) > 50

    # Verify Observability Stats
    stats = orchestrator.get_observability_stats()
    assert stats["initialized"] is True
    assert "traces" in stats

    print(f"\n[REAL LLM OUTPUT]\n{full_output}")


@pytest.mark.asyncio
async def test_governance_veto_personality():
    """Verify that VETO still works and keeps its personality with real components."""
    orchestrator = PrometheusOrchestrator(agent_name="VetoAgent")
    orchestrator._persistence_initialized = True

    # Mock Governance to VETO
    orchestrator.governance.review_task = AsyncMock(
        return_value=GovernanceVerdict(
            approved=False, reasoning="Harmful intent", risk_level="CRITICAL", governor="JUSTICA"
        )
    )

    chunks = []
    async for chunk in orchestrator.execute("Dangerous Task", fast_mode=True):
        chunks.append(chunk)

    full_output = "".join(chunks)
    assert "🛑 **VETO** by JUSTICA" in full_output
    assert "Harmful intent" in full_output
