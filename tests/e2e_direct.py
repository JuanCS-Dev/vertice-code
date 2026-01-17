#!/usr/bin/env python3
"""
Direct E2E Test - BYPASS AGENT ROUTING

Forces request directly to LLM without agent routing to test tool execution.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())


async def test_direct_llm_tools():
    """Test tool execution directly through LLM without agent routing."""
    print("=" * 60)
    print("🔬 DIRECT E2E TEST - LLM + Tools (NO AGENT ROUTING)")
    print("=" * 60)
    print()

    # Setup test file
    test_file = "test_e2e_direct.txt"
    if os.path.exists(test_file):
        os.unlink(test_file)

    # Initialize Bridge
    from vertice_tui.core.bridge import Bridge

    bridge = Bridge()

    print("✓ Bridge initialized")
    print(f"✓ Tools: {len(bridge.tools.get_schemas_for_llm())} available")

    # Disable auto-routing
    print("✓ Disabling agent auto-routing")
    print()

    # Create the prompt
    prompt = f"Create a file called {test_file} with content 'Vértice Sovereign Mode Active'. Use the write_file tool."
    print(f"📝 Prompt: {prompt}")
    print()
    print("⏳ Streaming via Bridge.chat(auto_route=False)...")
    print("-" * 60)

    # Stream with auto_route=False
    full_response = []
    try:
        async for chunk in bridge.chat(prompt, auto_route=False):
            full_response.append(chunk)
            # Print first 500 chars
            if len("".join(full_response)) <= 500:
                print(chunk, end="", flush=True)
    except Exception as e:
        print(f"\n❌ Stream error: {e}")
        import traceback

        traceback.print_exc()
        return False

    print()
    print("-" * 60)
    print()

    # Check results
    print("📊 RESULTS:")
    print(f"   Response length: {len(''.join(full_response))} chars")
    print(f"   File exists: {os.path.exists(test_file)}")

    if os.path.exists(test_file):
        content = open(test_file).read()
        print(f"   File content: {content[:100]}")
        success = "Vértice" in content or "Sovereign" in content
        print(f"   Content match: {success}")

        # Cleanup
        os.unlink(test_file)

        if success:
            print()
            print("✅ E2E TEST PASSED!")
            return True

    print()
    print("❌ E2E TEST FAILED!")
    return False


if __name__ == "__main__":
    result = asyncio.run(test_direct_llm_tools())
    exit(0 if result else 1)
