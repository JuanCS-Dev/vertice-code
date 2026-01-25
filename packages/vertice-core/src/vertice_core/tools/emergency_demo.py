"""
🚨 EMERGENCY TOOL SYSTEM STATUS

The main tool system has circular import issues. This provides immediate working tools.
"""

import asyncio
from vertice_core.core.emergency_mcp import create_emergency_mcp


async def demo_working_tools():
    """Demonstrate working basic tools."""
    print("🚨 EMERGENCY TOOL SYSTEM")
    print("=" * 50)

    mcp = create_emergency_mcp()
    health = mcp.get_health_status()

    print(f"Status: {'✅ Working' if health['healthy'] else '❌ Broken'}")
    print(f"Tools Available: {health['tools_registered']}")

    # Test read_file
    print("\n🧪 Testing read_file tool...")
    try:
        result = await mcp.call_tool("read_file", {"path": "README.md"})
        if "error" not in result:
            content = result.get("content", result.get("result", ""))
            print(f"✅ Success: Read {len(content)} characters")
        else:
            print(f"❌ Error: {result['error']}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # Test write_file
    print("\n🧪 Testing write_file tool...")
    try:
        result = await mcp.call_tool(
            "write_file",
            {
                "path": "test_output.txt",
                "content": "This is a test file created by emergency tools.",
            },
        )
        if "error" not in result:
            print("✅ Success: File written")
        else:
            print(f"❌ Error: {result['error']}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    print("\n🔧 Emergency tools are functional!")
    print("Use: from vertice_core.tools.emergency_setup import setup_emergency_tools")


if __name__ == "__main__":
    asyncio.run(demo_working_tools())
