#!/usr/bin/env python3
"""
TUI E2E Diagnostic #2: Simulate ToolCallParser on Real Output

This script tests if ToolCallParser.extract() correctly parses
the JSON output from VertexAIProvider.

Author: Opus Audit
Date: 2026-01-08
"""
import sys
import os

sys.path.insert(0, os.getcwd())

# The exact JSON from the diagnostic
TEST_JSON = '{"tool_call": {"name": "write_file", "arguments": {"content": "def hello_world():\\n  print(\\"hello world\\")", "path": "test_diagnostic.py"}}}'


def test_parser():
    """Test ToolCallParser with real LLM output."""
    print("=" * 70)
    print("🔬 TUI E2E DIAGNOSTIC #2: ToolCallParser Test")
    print("=" * 70)

    try:
        from vertice_tui.core.parsing.tool_call_parser import ToolCallParser
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    print(f"\n📥 Input JSON:\n{TEST_JSON}\n")
    print("-" * 70)

    results = ToolCallParser.extract(TEST_JSON)

    print("📊 Extraction Results:")
    print(f"   Tool calls found: {len(results)}")

    if results:
        for name, args in results:
            print(f"   - Tool: {name}")
            print(f"     Args: {args}")
        print("\n✅ ToolCallParser WORKS!")
        return True
    else:
        print("\n❌ ToolCallParser FAILED to extract tool call!")
        print("   → The regex pattern is not matching.")
        return False


if __name__ == "__main__":
    success = test_parser()
    exit(0 if success else 1)
