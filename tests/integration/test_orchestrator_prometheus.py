"""
Integration Test: Orchestrator -> Prometheus Handoff.

Verifies Phase 3 (Meta-Orchestrator Elevation):
1. Router selects Prometheus for COMPLEX tasks.
2. Orchestrator delegates to Prometheus agent.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.types import Task, TaskComplexity, AgentRole
from vertice_cli.agents.base import AgentResponse, TaskResult, TaskStatus

@pytest.mark.asyncio
async def test_router_selects_prometheus_for_complex_tasks():
    """Test that TaskRouter selects Prometheus for COMPLEX/CRITICAL tasks."""
    orchestrator = OrchestratorAgent()
    
    # Test COMPLEX
    task_complex = Task(
        id="t1",
        description="Build a full autonomous system",
        complexity=TaskComplexity.COMPLEX
    )
    role = await orchestrator.route(task_complex)
    assert role == AgentRole.PROMETHEUS
    
    # Test CRITICAL
    task_critical = Task(
        id="t2",
        description="Fix production security vulnerability",
        complexity=TaskComplexity.CRITICAL
    )
    role = await orchestrator.route(task_critical)
    assert role == AgentRole.PROMETHEUS
    
    # Test Keyword
    task_keyword = Task(
        id="t3",
        description="Please plan the evolution of the system",
        complexity=TaskComplexity.MODERATE
    )
    role = await orchestrator.route(task_keyword)
    assert role == AgentRole.PROMETHEUS

@pytest.mark.asyncio
async def test_orchestrator_delegates_to_prometheus():
    """Test full delegation flow."""
    
    # Mock Prometheus Agent
    mock_prometheus = AsyncMock()
    mock_result = TaskResult(
        task_id="t1",
        status=TaskStatus.COMPLETED,
        output={"output": "Prometheus Plan Executed"}
    )
    mock_response = AgentResponse(
        success=True,
        data={
            "task_id": "t1",
            "result": mock_result
        },
        reasoning="Simulated"
    )
    mock_prometheus.execute.return_value = mock_response
    
    # Patch get_agent to return our mock
    with patch("vertice_agents.registry.get_agent", return_value=mock_prometheus):
        orchestrator = OrchestratorAgent()
        
        # Manually ensure agents are loaded (since we patched get_agent)
        orchestrator._ensure_agents()
        assert AgentRole.PROMETHEUS in orchestrator.agents
        
        # Execute task directly via _delegate_to_agent to test the adaptation logic
        task = Task(
            id="t1",
            description="Complex task",
            complexity=TaskComplexity.COMPLEX
        )
        
        chunks = []
        async for chunk in orchestrator._delegate_to_agent(
            mock_prometheus, 
            AgentRole.PROMETHEUS, 
            task, 
            stream=True
        ):
            chunks.append(chunk)
            
        assert "".join(chunks) == "Prometheus Plan Executed"
