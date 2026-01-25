"""
🔧 Quick Fix for Circular Import Issues

This script provides a minimal working setup for basic file tools.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_basic_tools():
    """Test basic tool functionality."""
    print("🔧 Testing basic tools...")

    try:
        # Test ToolRegistry
        from vertice_core.core.tool_registry import ToolRegistry

        registry = ToolRegistry()
        print("✅ ToolRegistry works")

        # Test individual tools
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        print(f"✅ ReadFileTool: {tool.name}")

        # Register tool
        registry.register(tool)
        print(f"✅ Tool registered: {len(registry)} tools")

        # Test MCP client
        from vertice_core.core.mcp import create_mcp_client

        mcp = create_mcp_client()
        print("✅ MCP client created")

        # Test health
        health = mcp.get_health_status()
        print(f"✅ Health check: {health['healthy']}")

        print("\n🎉 All basic tools working!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_basic_tools()
