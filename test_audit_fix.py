import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from vertice_cli.agents.devops.agent import DevOpsAgent


# Mock LLM Client
class MockLLM:
    async def generate_with_tools(self, prompt, **kwargs):
        print(f"   [LLM] Called with prompt len: {len(prompt)}")
        if "read_file" in prompt or "EXECUTE A REAL AUDIT" in prompt:
            return '```python\nread_file("docker-compose.yml")\n```'
        return "Audit complete. System is robust."

    async def stream_chat(self, messages, **kwargs):
        yield "Thinking..."
        yield " Done."

    async def generate(self, messages, **kwargs):
        return '```python\nlist_directory(".")\n```'


async def test_audit_streaming():
    print("🚀 Starting DevOps Audit Test")

    # Initialize Agent
    agent = DevOpsAgent(llm_client=MockLLM())

    # Inject fake MCP client to test fallback path logic (or integration)
    # Actually, let's test the FALLBACK path since that was broken
    agent.mcp_client = None

    task_req = "faça uma auditoria completa do web-app e me diga se estamos prontos para o deploy"

    print(f"📋 Request: {task_req}")
    print("-" * 50)

    if hasattr(agent, "execute_streaming"):
        print("✅ execute_streaming method found")

        async for chunk in agent.execute_streaming(task_req):
            print(f"🌊 Stream chunk: {chunk.strip()}")

            # If we see the tool output in the stream, it's working
            if "docker-compose" in chunk:
                print("   ✅ Found docker-compose content in stream!")
    else:
        print("❌ execute_streaming NOT found")


if __name__ == "__main__":
    # Ensure we are in project root
    print(f"CWD: {os.getcwd()}")
    asyncio.run(test_audit_streaming())
