import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import MagicMock, AsyncMock

from vertice_tui.core.agents.manager import AgentManager
from vertice_cli.agents.base import AgentTask
from vertice_cli.agents.explorer import ExplorerAgent
from vertice_cli.agents.refactorer import RefactorerAgent
from vertice_cli.agents.devops import DevOpsAgent
from vertice_cli.agents.documentation import DocumentationAgent

# MOCK LLM Client for Stress Testing to avoid API costs/latency
class MockLLMClient:
    async def generate_content(self, prompt: str) -> str:
        if "refactoring" in prompt.lower():
            return """
            ```json
            {
                "candidates": [
                    {"file": "main.py", "reason": "Too complex", "priority": "HIGH"}
                ]
            }
            ```
            """
        return "Mock response"

@pytest.fixture
def agent_manager():
    # Patch ensure_providers_registered to avoid CLI dependency issues in test env
    from unittest.mock import patch
    with patch('vertice_cli.core.providers.register.ensure_providers_registered'):
        manager = AgentManager(llm_client=MockLLMClient())
        return manager

@pytest.mark.asyncio
async def test_agent_manager_concurrency(agent_manager):
    """Test AgentManager handling multiple concurrent agent requests."""
    tasks = []
    
    # Simulate 10 parallel requests
    agent = await agent_manager.get_agent("explorer")
    for i in range(10):
        task = AgentTask(
            request=f"Stress test request {i}",
            context={"file": f"test_{i}.py"}
        )
        tasks.append(agent.execute(task))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    assert len(results) == 10
    # Check that no result is an exception
    for r in results:
        assert not isinstance(r, Exception), f"Task failed with {r}"
        
@pytest.mark.asyncio
async def test_explorer_deep_search_performance():
    """Test ExplorerAgent deep search performance and accuracy."""
    agent = ExplorerAgent(llm_client=MockLLMClient(), mcp_client=MagicMock())
    
    # Point to ACTUAL project root for realistic test
    project_root = Path("/media/juan/DATA/Vertice-Code")
    agent._project_root = project_root
    
    task = AgentTask(
        request="deep search for 'BaseAgent'",
        context={"cwd": str(project_root)}
    )
    
    import time
    start = time.time()
    response = await agent.execute(task)
    duration = time.time() - start
    
    assert response.success
    # Should find at least one file (base.py or similar)
    assert len(response.data.get("relevant_files", [])) > 0
    # Should be reasonably fast (< 5 seconds for local grep)
    print(f"Deep search took {duration:.2f}s")
    assert duration < 5.0

@pytest.mark.asyncio
async def test_refactorer_blast_radius_integration():
    """Test RefactorerAgent actually calls Explorer for blast radius."""
    explorer_mock = AsyncMock()
    explorer_mock.execute.return_value.success = True
    explorer_mock.execute.return_value.data = {
        "relevant_files": [{"path": "dependent_module.py"}]
    }
    
    agent = RefactorerAgent(llm_client=MockLLMClient(), mcp_client=MagicMock())
    agent.explorer = explorer_mock
    
    # Test internal method directly
    radius = await agent._analyze_blast_radius("target_module.py")
    
    assert "dependent_module.py" in radius["dependent_files"]
    assert radius["risk_level"] == "MEDIUM" or radius["risk_level"] == "LOW"

@pytest.mark.asyncio
async def test_devops_structured_output():
    """Test DevOpsAgent returns strict structured data."""
    agent = DevOpsAgent(llm_client=MockLLMClient(), mcp_client=MagicMock())
    
    # Mocking internal methods to bypass heavy logic
    # We only care about the return structure of _handle_deployment
    # which we can reach by mocking the LLM to return a plan
    
    task = AgentTask(
        request="deploy to k8s",
        context={"env": "prod"}
    )
    
    
    # We need to mock _generate_k8s_plan or _call_llm to ensure it proceeds
    from unittest.mock import patch
    with patch.object(agent, '_create_deployment_plan', new_callable=AsyncMock) as mock_plan:
        mock_plan.return_value = MagicMock(
            strategy=MagicMock(value="blue-green"),
            health_check_endpoint="/health",
            to_dict=lambda: {}
        )
        
        response = await agent.execute(task)
        
        assert response.success
        data = response.data
        
        assert "infrastructure" in data
        assert "configuration" in data
        assert data["infrastructure"]["orchestration"] == "argocd"
        assert data["configuration"]["replicas"] == 3

@pytest.mark.asyncio
async def test_documentation_fallback_resilience():
    """Test DocumentationAgent fallback when AST fails."""
    agent = DocumentationAgent(llm_client=MockLLMClient(), mcp_client=MagicMock())
    
    # Create a temporary empty file or bad syntax file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as tmp:
        tmp.write("This is not python code !@#$")
        tmp.flush()
        
        task = AgentTask(
            request="generate docs",
            context={"files": [tmp.name]}
        )
        
        response = await agent.execute(task)
        
        # Should succeed via fallback
        assert response.success
        assert "modules" in response.data
        assert "Raw Content Preview" in response.data["modules"][0]["docstring"]
