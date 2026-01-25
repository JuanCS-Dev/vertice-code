#!/usr/bin/env python3
"""
TUI E2E Diagnostic: Capture Raw LLM Output for Tool Call Analysis

This script isolates the exact point of failure by:
1. Sending a "create file" request directly to the LLM.
2. Capturing the RAW output (text + function_calls).
3. Analyzing if the LLM uses tools or just outputs text.

Author: Opus Audit
Date: 2026-01-08
"""
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())

# Simulated tool schema (same as TUI would send)
WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": "Write content to a file. Creates the file if it doesn't exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
}

SYSTEM_PROMPT = """You are a coding assistant with access to tools.
When asked to create files, you MUST use the write_file tool.
DO NOT output code blocks - use the tool instead."""

USER_MESSAGE = "Create a file called test_diagnostic.py with a simple hello world function."


async def run_diagnostic():
    """Run diagnostic test against VertexAIProvider."""
    print("=" * 70)
    print("🔬 TUI E2E DIAGNOSTIC: Raw LLM Output Analysis")
    print("=" * 70)

    # Import provider
    try:
        from vertice_core.core.providers.vertex_ai import VertexAIProvider
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return

    # Initialize provider
    provider = VertexAIProvider(
        location="us-central1",
        model_name="pro",  # gemini-2.5-pro
    )

    print(f"📋 Model: {provider.model_name}")
    print(f"📍 Location: {provider.location}")
    print(f"🏗️ Project: {provider.project}")
    print()

    # Build messages
    messages = [{"role": "user", "content": USER_MESSAGE}]

    # Create a mock tool object with get_schema method
    class MockTool:
        name = "write_file"

        def get_schema(self):
            return WRITE_FILE_SCHEMA

    tools = [MockTool()]

    print("📤 Sending request with tools...")
    print(f"   System Prompt: {SYSTEM_PROMPT[:80]}...")
    print(f"   User Message: {USER_MESSAGE}")
    print(f"   Tools: {[t.name for t in tools]}")
    print()
    print("-" * 70)
    print("📥 RAW LLM OUTPUT:")
    print("-" * 70)

    raw_chunks = []
    function_calls_found = []
    text_found = []

    try:
        async for chunk in provider.stream_chat(
            messages,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            tool_config="AUTO",  # Current setting
        ):
            raw_chunks.append(chunk)

            # Analyze chunk type
            if chunk.startswith('{"tool_call"'):
                function_calls_found.append(chunk)
                print(f"[FUNC_CALL] {chunk}")
            else:
                text_found.append(chunk)
                print(chunk, end="", flush=True)

        print()
        print("-" * 70)
        print()

        # Analysis
        print("📊 ANALYSIS:")
        print(f"   Total chunks: {len(raw_chunks)}")
        print(f"   Text chunks: {len(text_found)}")
        print(f"   Function call chunks: {len(function_calls_found)}")
        print()

        if function_calls_found:
            print("✅ LLM IS using function calls!")
            print("   → Issue is likely in ToolCallParser pattern matching.")
            print()
            print("   Function calls received:")
            for fc in function_calls_found:
                print(f"   {fc}")
        else:
            print("❌ LLM is NOT using function calls!")
            print("   → LLM outputs text instead of calling write_file tool.")
            print("   → FIX: Change tool_config from 'AUTO' to 'ANY'")
            print()
            print("   Text output sample (first 500 chars):")
            full_text = "".join(text_found)
            print(f"   {full_text[:500]}")

        print()
        print("=" * 70)
        print("🔬 DIAGNOSTIC COMPLETE")
        print("=" * 70)

        return len(function_calls_found) > 0

    except Exception as e:
        print(f"\n❌ Error during diagnostic: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(run_diagnostic())
    exit(0 if result else 1)
