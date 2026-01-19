import asyncio
import sys
import logging
from pathlib import Path

# Fix Path for Imports
PROJECT_ROOT = Path("/media/juan/DATA/Vertice-Code")
sys.path.insert(0, str(PROJECT_ROOT))

from agents.coder.agent import CoderAgent
from providers.vertex_ai import VertexAIProvider
from agents.coder.types import CodeGenerationRequest

# Configure Logging to Stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def trace_coder_check():
    print("🚀 STARTING LIVE TRACE: CoderAgent -> VertexAI")

    # 1. Instantiate Agent
    try:
        agent = CoderAgent()
        print("✅ CoderAgent instantiated")
    except Exception as e:
        print(f"❌ Failed to instantiate CoderAgent: {e}")
        import traceback

        traceback.print_exc()
        return

    # 2. Force Provider (Bypass Router for isolation)
    # We want to test the Vertex integration specifically
    # Use 'vertex-ai' as provider name if needed, but we instantiate class directly
    try:
        provider = VertexAIProvider(model_name="gemini-1.0-pro", location="us-central1")
    except Exception as e:
        print(f"❌ Failed to init VertexAIProvider: {e}")
        return

    if not provider.is_available():
        print("❌ Vertex AI Provider is not available (Check Auth/Region)")
        return
    print("✅ Vertex AI Provider is online")

    # Inject provider manually if possible or via mock router
    # CoderAgent uses `_get_llm` which calls `get_router`.
    # We will MonkeyPatch `_get_llm` to return our direct provider for this test.
    async def mock_get_llm():
        return provider

    agent._get_llm = mock_get_llm
    print("🔧 Monkey-patched CoderAgent to use direct VertexAIProvider")

    # 3. Validation Scenario
    # We use a request that explicitly demands a file write to test tool usage.
    request_desc = "Create a file named 'trace_output.py' that prints 'Hello World'"
    print(f"📝 Request: {request_desc}")

    req = CodeGenerationRequest(description=request_desc, language="python")

    # 4. Execute and Trace
    print("\n--- STREAM START ---\n")
    raw_chunks = []

    try:
        async for chunk in agent.generate(req):
            sys.stdout.write(chunk)
            raw_chunks.append(chunk)
    except Exception as e:
        print(f"\n❌ Stream Crashed: {e}")
        import traceback

        traceback.print_exc()

    print("\n\n--- STREAM END ---\n")

    # 5. Analysis
    full_output = "".join(raw_chunks)

    # Check for JSON Tool Call (Vertex Style)
    # It might come as a separate chunk with 'tool_call' key if we parsed it in provider,
    # OR as raw text if provider yielded text.
    # Our VertexAIProvider implementation yields json.dumps({"tool_call": ...})

    has_tool_call_json = '"tool_call":' in full_output

    # Check for Markdown/Text fallback
    # CoderAgent has regex: r"write_file\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(?:'''|\"\"\")(.*?)(?:'''|\"\"\")\s*\)"

    has_simulated_call = "write_file" in full_output

    print("🔍 DIAGNOSTIC RESULTS:")
    print(f"1. Raw JSON Tool Call detected? {'✅ YES' if has_tool_call_json else '❌ NO'}")
    print(
        f"2. 'write_file' text detected? {'⚠️ YES (Maybe Fallback)' if has_simulated_call else '❌ NO'}"
    )

    if not has_tool_call_json and not has_simulated_call:
        print("\n🚨 CRITICAL FAILURE: The model chatted but did NOT attempt to write the file.")
        print("Possible Code Issues:")
        print("- System Prompt didn't enforce tools?")
        print("- VertexAI SDK didn't send tool definitions?")
        print("- Model decided to ignore instructions.")

    if has_simulated_call and "Executing Tool" not in full_output:
        print(
            "\n🚨 REGEX FAILURE: Text-based tool call was present but Regex logic didn't catch it."
        )
        print("The Regex expects triple quotes. If model used single quotes, it fails.")


if __name__ == "__main__":
    asyncio.run(trace_coder_check())
