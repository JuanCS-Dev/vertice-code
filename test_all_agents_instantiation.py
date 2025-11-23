"""
Constitutional Audit: All 12 Agents Instantiation Test
======================================================

Verifica se TODOS os 12 agents podem ser criados sem erros.
"""

from maestro_v10_integrated import Orchestrator

class MockLLM:
    async def generate(self, *args, **kwargs):
        return "mock response"

def test_all_agents_instantiation():
    print("=" * 80)
    print("CONSTITUTIONAL AUDIT: ALL 12 AGENTS INSTANTIATION")
    print("=" * 80)
    print()

    print("Creating Orchestrator with all 12 agents...")
    llm = MockLLM()

    try:
        orchestrator = Orchestrator(llm, None)
        print("✅ Orchestrator created successfully\n")
    except Exception as e:
        print(f"❌ Failed to create Orchestrator: {e}")
        return False

    # Verify all 12 agents are registered
    expected_agents = [
        'executor', 'explorer', 'planner', 'reviewer', 'refactorer',
        'architect', 'security', 'performance', 'testing', 'documentation',
        'data', 'devops'
    ]

    print(f"Expected {len(expected_agents)} agents, checking...")
    print()

    missing = []
    for agent_name in expected_agents:
        if agent_name in orchestrator.agents:
            agent = orchestrator.agents[agent_name]
            print(f"✅ {agent_name:15} → {agent.__class__.__name__}")
        else:
            print(f"❌ {agent_name:15} → MISSING!")
            missing.append(agent_name)

    print()
    print("=" * 80)

    if missing:
        print(f"❌ FAILED: {len(missing)} agents missing: {missing}")
        return False
    else:
        actual_count = len(orchestrator.agents)
        expected_count = len(expected_agents)

        if actual_count == expected_count:
            print(f"✅ SUCCESS: All {actual_count}/12 agents instantiated correctly!")
        else:
            print(f"⚠️  WARNING: Expected {expected_count}, got {actual_count} agents")
            extra = set(orchestrator.agents.keys()) - set(expected_agents)
            if extra:
                print(f"   Extra agents: {extra}")
            return False

    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_all_agents_instantiation()
    exit(0 if success else 1)
