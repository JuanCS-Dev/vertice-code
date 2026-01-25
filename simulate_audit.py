import asyncio
import os
import sys

# Add src to path to emulate TUI environment
sys.path.append(os.path.join(os.getcwd(), "src"))

from vertice_core.agents.devops.agent import create_devops_agent


# Mock MCP Client that actually works (since we don't have the full MCP server running)
class LocalMCPClient:
    async def call_tool(self, name, args):
        # We'll use the fallback logic in the agent, so this mock just needs to exist
        # to trigger the 'hasattr(agent, "mcp_client")' check, but fail so fallback is used?
        # NO, the agent PREFERS mcp_client. If it exists, it calls it.
        # We should let the agent use its internal fallback logic OR implement basic tools here.
        # Given the fix was in _execute_tool_fallback, we want to exercise THAT.
        # So providing None as mcp_client is safer if we want to test the fallback.
        # implementation details of DevOpsAgent show it uses fallback if mcp_client is None/missing
        # OR if we pass mcp_client but it fails.
        raise NotImplementedError("Simulating MCP failure to force fallback")


# We need a real-ish LLM client
# Since I can't easily spin up the real Vertex AI client without auth,
# I rely on the fact that the agent uses `llm_client`.
# Wait, the user wants to see if *THE FIX* works.
# The fix was in the TOOL USE LOOP.
# So I need an LLM that *requests* tools.


class MockToolUsingLLM:
    def __init__(self):
        self.step = 0

    async def generate_with_tools(self, messages, **kwargs):
        # This shouldn't be called if we use the loop in _call_llm_with_tools
        return await self.stream_chat(messages, **kwargs)

    async def generate(self, messages):
        # Join generator
        chunks = []
        async for chunk in self.stream_chat(messages):
            chunks.append(chunk)
        return "".join(chunks)

    async def stream_chat(self, messages, **kwargs):
        prompt = str(messages)

        # Simple state machine to simulate an audit flow
        if "EXECUTE A REAL AUDIT" in prompt and self.step == 0:
            self.step += 1
            yield "I will start by listing the files to understand the structure.\n"
            yield '```python\nlist_directory(".")\n```'
            return

        if "list_directory" in prompt and self.step == 1:
            self.step += 1
            yield "I see a docker-compose.yml and Dockerfiles. I will read them.\n"
            yield '```python\nread_file("docker-compose.yml")\n```'
            return

        if "docker-compose.yml" in prompt and self.step == 2:
            self.step += 1
            yield "I found hardcoded credentials! Now checking Dockerfile.\n"
            yield '```python\nread_file("Dockerfile")\n```'
            return

        if "Dockerfile" in prompt:
            yield "**Audit Report**\n\n1. Found hardcoded secrets in docker-compose.yml\n2. Dockerfile uses root user.\n\nNOT READY for deploy."
            return

        yield "Analysis complete."


async def run_audit():
    print("🚀 Simulating DevOps Audit...")

    # We use a Mock LLM that behaves deterministically to verify the TOOL LOOP works
    # If the tool loop works, the output will contain file contents.
    llm = MockToolUsingLLM()

    # We DO NOT provide mcp_client to force usage of _execute_tool_fallback
    # which is where we applied the directory string fixes.
    agent = create_devops_agent(llm_client=llm, mcp_client=None)

    request = "Faça uma auditoria completa do web-app e me diga se estamos prontos para o deploy"

    output = []
    async for chunk in agent.execute_streaming(request):
        print(chunk, end="", flush=True)
        output.append(chunk)

    # Save to file
    with open("audit_result_simulation.txt", "w") as f:
        f.write("".join(output))


if __name__ == "__main__":
    asyncio.run(run_audit())
