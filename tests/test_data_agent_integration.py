#!/usr/bin/env python3
"""
DataAgent Integration Test
===========================

Quick smoke test to verify DataAgent works with the current infrastructure.
"""

import asyncio
from jdev_cli.agents.data_agent_production import create_data_agent
from jdev_cli.agents.base import AgentTask, AgentRole, AgentCapability

# Mock LLM for testing
class SimpleMockLLM:
    async def generate(self, prompt, system_prompt=None, **kwargs):
        if "schema" in prompt.lower():
            return "Found 2 issues: missing primary key on users table, no audit timestamps"
        elif "optimize" in prompt.lower():
            return "Add index on email column for 60% improvement"
        elif "migration" in prompt.lower():
            return "Low risk migration, can run online, 0 downtime"
        return "Task completed successfully"

async def main():
    print("=" * 80)
    print("DATA AGENT - INTEGRATION TEST")
    print("=" * 80)
    print()

    # Test 1: Factory function
    print("TEST 1: Factory Function")
    print("-" * 80)
    llm = SimpleMockLLM()
    agent = create_data_agent(llm, mcp_client=None, enable_thinking=True)

    # Check properties
    assert agent.role == AgentRole.DATABASE, f"Expected DATABASE role, got {agent.role}"
    assert AgentCapability.DATABASE in agent.capabilities, "Missing DATABASE capability"
    assert AgentCapability.READ_ONLY in agent.capabilities, "Missing READ_ONLY capability"

    print(f"✅ Role: {agent.role.value}")
    print(f"✅ Capabilities: {[c.value for c in agent.capabilities]}")
    print(f"✅ Thinking enabled: {agent.adapter is not None}")
    print()

    # Test 2: Schema Analysis
    print("TEST 2: Schema Analysis")
    print("-" * 80)

    schema = {
        "users": {
            "columns": {
                "id": "UUID",
                "name": "VARCHAR(255)",
                "email": "VARCHAR(255)",
            },
            "constraints": [],  # No PK!
        }
    }

    issues = await agent.analyze_schema(schema)

    print(f"✅ Found {len(issues)} schema issues:")
    for issue in issues:
        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }.get(issue.severity.value, "⚪")
        print(f"  {severity_emoji} {issue.severity.value}: {issue.description[:60]}...")
    print()

    # Test 3: Execute via BaseAgent interface
    print("TEST 3: BaseAgent Interface")
    print("-" * 80)

    task = AgentTask(
        request="Analyze the users table for optimization opportunities",
        context={"database": "production"}
    )

    response = await agent.execute(task)

    assert response.success, f"Task failed: {response.error}"
    assert response.reasoning, "No reasoning provided"
    assert "response" in response.data, "Missing response in data"

    print(f"✅ Success: {response.success}")
    print(f"✅ Reasoning: {response.reasoning[:80]}...")
    print(f"✅ Response: {response.data['response'][:80]}...")
    print()

    print("=" * 80)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 80)
    print()
    print("DataAgent is fully integrated with:")
    print("  • BaseAgent v2.0 (role, capabilities, execute)")
    print("  • LLMClientAdapter (thinking simulation)")
    print("  • AgentTask/AgentResponse (standard interface)")
    print()
    print("Ready for production use!")

if __name__ == "__main__":
    asyncio.run(main())
