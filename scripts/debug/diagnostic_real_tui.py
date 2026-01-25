#!/usr/bin/env python3
"""
TUI E2E CORRECT PIPELINE DIAGNOSTIC

This simulates the EXACT TUI path:
1. Bridge is initialized (calls ensure_providers_registered)
2. GeminiClient is created by Bridge
3. chat() is called

Author: Opus Audit
Date: 2026-01-08
"""
import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())

SYSTEM_PROMPT = """You are a coding assistant with access to tools.
When asked to create files, you MUST use the write_file tool.
DO NOT output code blocks - use the tool instead."""

USER_MESSAGE = "Create a file called test_diagnostic.py with a simple hello world function."


async def trace_real_tui_pipeline():
    """Trace the REAL TUI pipeline using Bridge."""
    print("=" * 70)
    print("🔬 TUI REAL PIPELINE TRACE (Using Bridge)")
    print("=" * 70)
    print()

    # Step 1: Initialize Bridge (like TUI does)
    print("📍 STEP 1: Initialize Bridge")
    print("-" * 70)

    try:
        from vertice_tui.core.bridge import Bridge

        bridge = Bridge()
        print("   ✅ Bridge initialized")
    except Exception as e:
        print(f"   ❌ Bridge failed: {e}")
        import traceback

        traceback.print_exc()
        return

    print()

    # Step 2: Check provider registry after Bridge init
    print("📍 STEP 2: Provider Registry Status")
    print("-" * 70)

    from vertice_core.providers import registry

    print(f"   Registered factories: {list(registry._factories.keys())}")
    print(f"   Available providers: {registry.get_available()}")

    print()

    # Step 3: Check GeminiClient
    print("📍 STEP 3: GeminiClient Status")
    print("-" * 70)

    llm = bridge.llm
    print(f"   Has VerticeClient: {llm._vertice_coreent is not None}")
    if llm._vertice_coreent:
        print(f"   VerticeClient priority: {llm._vertice_coreent.config.priority}")
    print(f"   Current provider: {llm.get_current_provider_name()}")

    print()

    # Step 4: Stream via Bridge's GeminiClient
    print("📍 STEP 4: Stream via LLM (with tools)")
    print("-" * 70)

    tool_schemas = bridge.tools.get_schemas_for_llm()
    print(f"   Tools available: {len(tool_schemas)}")

    print()
    print("   Streaming response...")
    print()

    chunks = []
    function_calls = []
    text_chunks = []

    try:
        async for chunk in llm.stream(
            USER_MESSAGE,
            system_prompt=SYSTEM_PROMPT,
            tools=tool_schemas,
        ):
            chunks.append(chunk)
            if '{"tool_call"' in chunk:
                function_calls.append(chunk)
                print(f"   [FUNC_CALL] {chunk}")
            else:
                text_chunks.append(chunk)
                # Only print first 200 chars of text
                if len("".join(text_chunks)) <= 200:
                    print(chunk, end="", flush=True)

        print()
        print()
        print("-" * 70)
        print()

        print("📊 ANALYSIS:")
        print(f"   Total chunks: {len(chunks)}")
        print(f"   Text chunks: {len(text_chunks)}")
        print(f"   Function call chunks: {len(function_calls)}")
        print()

        if function_calls:
            print("✅ Function calls ARE working!")

            # Test ToolCallParser
            from vertice_tui.core.parsing.tool_call_parser import ToolCallParser

            accumulated = "".join(chunks)
            parsed = ToolCallParser.extract(accumulated)
            print(f"   → ToolCallParser found: {len(parsed)} tool calls")
            for name, args in parsed:
                print(f"      - {name}: {list(args.keys())}")
        else:
            print("❌ Function calls NOT working!")
            print("   Full text output (first 500 chars):")
            print(f"   {''.join(text_chunks)[:500]}")

    except Exception as e:
        print(f"\n   ❌ Stream failed: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 70)
    print("🔬 DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(trace_real_tui_pipeline())
