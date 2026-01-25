#!/usr/bin/env python3
"""
TUI E2E FULL PIPELINE DIAGNOSTIC

Traces the EXACT path that the E2E test takes and identifies where tool calls are lost.

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


async def trace_full_pipeline():
    """Trace the full TUI pipeline to identify where tool calls are lost."""
    print("=" * 70)
    print("🔬 TUI FULL PIPELINE TRACE")
    print("=" * 70)
    print()

    # Step 1: Check which provider VerticeClient uses
    print("📍 STEP 1: VerticeClient Provider Selection")
    print("-" * 70)

    try:
        from vertice_core.clients.vertice_coreent import VerticeClient

        client = VerticeClient()
        print(f"   Priority order: {client.config.priority}")
        print(
            f"   Available providers: {list(client._providers.keys()) if hasattr(client, '_providers') else 'N/A'}"
        )
    except Exception as e:
        print(f"   ❌ VerticeClient failed: {e}")
        client = None

    print()

    # Step 2: Check what GeminiClient does
    print("📍 STEP 2: GeminiClient._stream_via_client path")
    print("-" * 70)

    try:
        from vertice_tui.core.llm_client import GeminiClient

        gemini = GeminiClient()
        print(f"   VerticeClient available: {gemini._vertice_coreent is not None}")
        print(f"   Current provider: {gemini.get_current_provider_name()}")
    except Exception as e:
        print(f"   ❌ GeminiClient failed: {e}")
        gemini = None

    print()

    # Step 3: Actually stream and capture output
    print("📍 STEP 3: Stream via TUI GeminiClient")
    print("-" * 70)

    if gemini:
        # Get tool schemas like TUI would
        try:
            from vertice_tui.core.tools_bridge import ToolBridge

            tools_bridge = ToolBridge()
            tool_schemas = tools_bridge.get_schemas_for_llm()
            print(f"   Tool schemas available: {len(tool_schemas)}")

            # Find write_file
            write_file_present = any(t.get("name") == "write_file" for t in tool_schemas)
            print(f"   write_file in schemas: {write_file_present}")
        except Exception as e:
            print(f"   ❌ ToolBridge failed: {e}")
            tool_schemas = None

        print()
        print("   Streaming response...")
        print()

        chunks = []
        function_calls = []
        text_chunks = []

        try:
            async for chunk in gemini.stream(
                USER_MESSAGE,
                system_prompt=SYSTEM_PROMPT,
                tools=tool_schemas,
            ):
                chunks.append(chunk)
                if chunk.startswith('{"tool_call"'):
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
                print("✅ Function calls ARE reaching GeminiClient.stream()!")
                print("   → Issue is in ChatController or ToolCallParser (less likely).")

                # Test ToolCallParser
                from vertice_tui.core.parsing.tool_call_parser import ToolCallParser

                accumulated = "".join(chunks)
                parsed = ToolCallParser.extract(accumulated)
                print(f"   → ToolCallParser found: {len(parsed)} tool calls")
                if parsed:
                    print("   ✅ ToolCallParser works!")
                else:
                    print("   ❌ ToolCallParser FAILED despite function_call in output!")

            else:
                print("❌ Function calls are NOT reaching GeminiClient.stream()!")
                print("   → The provider being used does NOT emit tool_call JSON.")
                print()
                print("   Full text output (first 500 chars):")
                print(f"   {''.join(text_chunks)[:500]}")
                print()
                print("   🔴 ROOT CAUSE: TUI is using a provider that doesn't support tool calls")
                print(
                    "      (probably falling back to legacy GeminiProvider instead of VertexAIProvider)"
                )

        except Exception as e:
            print(f"\n   ❌ Stream failed: {e}")
            import traceback

            traceback.print_exc()

    print()
    print("=" * 70)
    print("🔬 DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(trace_full_pipeline())
