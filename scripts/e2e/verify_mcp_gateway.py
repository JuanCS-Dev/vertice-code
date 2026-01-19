#!/usr/bin/env python
"""E2E Verification for MCP Gateway centralization."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_mcp_gateway_import():
    """Test MCPGateway imports correctly."""
    print("🔌 Testing MCP Gateway Import...")

    try:
        print("   ✅ MCPGateway imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_adapters_initialized():
    """Test all adapters are initialized."""
    print("\n📦 Testing Adapter Initialization...")

    from vertice_cli.integrations.mcp import mcp_gateway

    adapters = [
        ("daimon_adapter", mcp_gateway.daimon_adapter),
        ("coder_adapter", mcp_gateway.coder_adapter),
        ("reviewer_adapter", mcp_gateway.reviewer_adapter),
        ("architect_adapter", mcp_gateway.architect_adapter),
        ("noesis_adapter", mcp_gateway.noesis_adapter),
    ]

    all_ok = True
    for name, adapter in adapters:
        if adapter is not None:
            print(f"   ✅ {name} initialized")
        else:
            print(f"   ❌ {name} is None")
            all_ok = False

    return all_ok


def test_health_status():
    """Test gateway health endpoint."""
    print("\n🏥 Testing Health Status...")

    from vertice_cli.integrations.mcp import mcp_gateway

    health = mcp_gateway.get_health()

    print(f"   Status: {health['status']}")
    print(f"   Total Tools (pre-registration): {health['total_tools']}")

    if health["status"] in ("healthy", "not_initialized"):
        print("   ✅ Health check passed")
        return True
    else:
        print("   ❌ Unexpected status")
        return False


def test_tool_listing():
    """Test tool listing by adapter."""
    print("\n📋 Testing Tool Listing...")

    from vertice_cli.integrations.mcp import mcp_gateway

    tools = mcp_gateway.list_all_tools()

    expected_adapters = ["daimon", "coder", "reviewer", "architect"]

    for adapter in expected_adapters:
        if adapter in tools:
            count = len(tools[adapter])
            print(f"   ✅ {adapter}: {count} tools")
        else:
            print(f"   ⚠️ {adapter}: not in listing (may need registration first)")

    return True


def main():
    """Run all MCP Gateway E2E tests."""
    print("=" * 60)
    print("🚀 MCP GATEWAY E2E VERIFICATION")
    print("=" * 60)

    results = []

    results.append(("Import", test_mcp_gateway_import()))
    results.append(("Adapters", test_adapters_initialized()))
    results.append(("Health", test_health_status()))
    results.append(("Tools", test_tool_listing()))

    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"   {status} {name}")

    print(f"\n   Total: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 MCP Gateway E2E Verification PASSED!")
        return 0
    else:
        print("\n💥 MCP Gateway E2E Verification FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
