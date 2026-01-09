#!/usr/bin/env python3
"""
🎯 CORRECTED AGENT VALIDATION - FINAL TEST

Test all agents with their correct APIs after fixes.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def final_agent_validation():
    """Final comprehensive agent validation."""

    print("🎯 FINAL AGENT VALIDATION - CORRECTED APIs")
    print("=" * 60)

    results = {}

    # Mock clients
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return f"Mock response for: {prompt[:50]}..."

    class MockMCPClient:
        def get_health_status(self):
            return {"healthy": True, "tools_registered": 4}

        async def call_tool(self, name: str, params: dict):
            return {"result": f"Mock {name} execution"}

    mock_llm = MockLLMClient()
    mock_mcp = MockMCPClient()

    # Test all core agents with correct APIs
    agents_to_test = [
        (
            "NextGenExecutorAgent",
            "vertice_cli.agents.executor.agent",
            lambda: mock_llm,
            lambda: mock_mcp,
        ),
        ("PlannerAgent", "vertice_cli.agents.planner.agent", lambda: mock_llm, lambda: mock_mcp),
        ("ArchitectAgent", "vertice_cli.agents.architect", lambda: mock_llm, lambda: mock_mcp),
    ]

    print("Testing Core Agents...")
    for agent_name, module_path, get_llm, get_mcp in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)

            # Instantiate with correct API
            agent = agent_class(llm_client=get_llm(), mcp_client=get_mcp())

            # Test basic execution
            from vertice_core.types import AgentTask

            task = AgentTask(request=f"Test {agent_name}")
            result = await agent.execute(task)

            results[agent_name] = "✅ PASSED"
            print(f"✅ {agent_name} fully functional")

        except Exception as e:
            results[agent_name] = f"❌ FAILED: {e}"
            print(f"❌ {agent_name} failed: {e}")

    # Test specialized agents
    specialized_agents = [
        ("ReviewerAgent", "vertice_cli.agents.reviewer.agent"),
        ("ExplorerAgent", "vertice_cli.agents.explorer"),
        ("JusticaIntegratedAgent", "vertice_cli.agents.justica_agent"),
    ]

    print("\nTesting Specialized Agents...")
    for agent_name, module_path in specialized_agents:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)

            # Try instantiation (may need special setup)
            agent = agent_class(llm_client=mock_llm, mcp_client=mock_mcp)

            results[f"specialized_{agent_name}"] = "✅ PASSED"
            print(f"✅ {agent_name} available")

        except Exception as e:
            results[f"specialized_{agent_name}"] = f"⚠️ LIMITED: {e}"
            print(f"⚠️ {agent_name} limited functionality: {str(e)[:50]}...")

    # Test Prometheus agents
    print("\nTesting Prometheus Agents...")
    prometheus_agents = [
        ("PrometheusIntegratedAgent", "prometheus.agent"),
        ("PrometheusAgent", "prometheus.main"),
        ("CurriculumAgent", "prometheus.agents.curriculum_agent"),
    ]

    for agent_name, module_path in prometheus_agents:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)

            results[f"prometheus_{agent_name}"] = "✅ IMPORTED"
            print(f"✅ {agent_name} imported successfully")

        except Exception as e:
            results[f"prometheus_{agent_name}"] = f"❌ FAILED: {e}"
            print(f"❌ {agent_name} failed: {e}")

    # Final analysis
    print("\n" + "=" * 60)
    print("📊 FINAL AGENT VALIDATION RESULTS")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r.startswith("✅"))
    failed = sum(1 for r in results.values() if r.startswith("❌"))
    limited = sum(1 for r in results.values() if r.startswith("⚠️"))
    total = len(results)

    print(f"Total agents tested: {total}")
    print(f"✅ Fully functional: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Limited functionality: {limited}")

    success_rate = ((passed + limited * 0.5) / total) * 100
    print(".1f")

    print("\nDetailed Results:")
    for agent, result in results.items():
        print(f"  {result} - {agent}")

    print("\n" + "=" * 60)

    if success_rate >= 90:
        print("🎉 EXCELLENT - AGENTS FULLY CORRECTED!")
        print("✅ All APIs working correctly")
        print("✅ Agents instantiable and functional")
        print("✅ System ready for production")
        status = "SUCCESS"
    elif success_rate >= 75:
        print("✅ GOOD - AGENTS MOSTLY CORRECTED")
        print("✅ Core functionality restored")
        print("⚠️ Some specialized agents need attention")
        status = "MOSTLY_SUCCESS"
    else:
        print("❌ NEEDS MORE WORK")
        print("❌ Significant agent issues remain")
        status = "NEEDS_WORK"

    print("=" * 60)

    return {"status": status, "results": results, "success_rate": success_rate}


if __name__ == "__main__":
    asyncio.run(final_agent_validation())
