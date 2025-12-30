#!/usr/bin/env python3
"""Quick test for streaming fix"""

import asyncio
from vertice_cli.core.llm import LLMClient
from vertice_cli.core.mcp_client import MCPClient
from vertice_cli.agents.executor import NextGenExecutorAgent, ExecutionMode, SecurityLevel
from vertice_cli.agents.base import AgentTask

async def main():
    # Initialize clients
    llm = LLMClient()

    # Initialize MCP with empty registry (test doesn't need real tools)
    from vertice_cli.tools.base import ToolRegistry
    registry = ToolRegistry()
    mcp = MCPClient(registry)

    # Initialize NextGen agent
    agent = NextGenExecutorAgent(
        llm_client=llm,
        mcp_client=mcp,
        execution_mode=ExecutionMode.LOCAL,
        security_level=SecurityLevel.STANDARD
    )

    # Test streaming
    print("🧪 Testing streaming execution...")
    task = AgentTask(request="list running processes")

    events = []
    async for event in agent.execute_streaming(task):
        event_type = event.get("type")
        print(f"  📡 Event: {event_type}")
        events.append(event)

        if event_type == "thinking":
            # Check that we have 'data' key
            assert "data" in event, f"Missing 'data' in thinking event: {event}"
            print(f"     Token: {event['data'][:20]}...")

        elif event_type == "command":
            print(f"     Command: {event['data']}")

        elif event_type == "status":
            print(f"     Status: {event['data']}")

        elif event_type == "result":
            result = event["data"]
            print(f"     Success: {result.get('success', False)}")
            break

    print(f"\n✅ Test passed! Received {len(events)} events")
    print(f"   Event types: {[e['type'] for e in events]}")

if __name__ == "__main__":
    asyncio.run(main())
