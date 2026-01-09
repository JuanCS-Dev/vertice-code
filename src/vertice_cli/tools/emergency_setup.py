"""Emergency tool setup for immediate use."""

from vertice_cli.core.emergency_mcp import create_emergency_mcp


def setup_emergency_tools():
    """Setup emergency tools for immediate use."""
    return create_emergency_mcp()


# Quick test
if __name__ == "__main__":
    mcp = setup_emergency_tools()
    print(f"Emergency tools ready: {len(mcp.registry)} tools")
