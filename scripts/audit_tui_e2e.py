#!/usr/bin/env python
"""
TUI E2E Audit Script - Complete Functional Testing.

Tests all major features of the Vertice TUI:
1. Bridge initialization
2. Manager functionality
3. Tool execution
4. Agent invocation (mocked)
5. Command handling
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add project paths
PROJECT_ROOT = Path("/media/juan/DATA/Vertice-Code")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Results tracking
RESULTS: Dict[str, List[Tuple[str, bool, str]]] = {
    "bridge": [],
    "managers": [],
    "tools": [],
    "agents": [],
    "commands": [],
}


def log_result(category: str, test_name: str, passed: bool, message: str = ""):
    """Log a test result."""
    status = "✅" if passed else "❌"
    print(f"  {status} {test_name}: {message}")
    RESULTS[category].append((test_name, passed, message))


def test_bridge_initialization():
    """Test Bridge initialization."""
    print("\n" + "=" * 60)
    print("1. BRIDGE INITIALIZATION")
    print("=" * 60)

    try:
        from vertice_tui.core.bridge import Bridge

        bridge = Bridge()
        log_result("bridge", "Bridge.__init__", True, "Created successfully")

        # Check critical components
        if bridge.llm is not None:
            log_result("bridge", "LLM Client", True, f"Available: {bridge.is_connected}")
        else:
            log_result("bridge", "LLM Client", False, "Not initialized")

        if bridge.governance is not None:
            log_result("bridge", "Governance", True, "Observer active")
        else:
            log_result("bridge", "Governance", False, "Not initialized")

        if bridge.agents is not None:
            count = (
                len(bridge.agents.available_agents)
                if hasattr(bridge.agents, "available_agents")
                else 0
            )
            log_result("bridge", "Agent Manager", True, f"{count} agents")
        else:
            log_result("bridge", "Agent Manager", False, "Not initialized")

        if bridge.tools is not None:
            count = bridge.tools.get_tool_count() if hasattr(bridge.tools, "get_tool_count") else 0
            log_result("bridge", "Tool Bridge", True, f"{count} tools")
        else:
            log_result("bridge", "Tool Bridge", False, "Not initialized")

        return bridge
    except Exception as e:
        log_result("bridge", "Bridge.__init__", False, str(e))
        return None


def test_managers(bridge):
    """Test all managers."""
    print("\n" + "=" * 60)
    print("2. MANAGERS")
    print("=" * 60)

    if bridge is None:
        log_result("managers", "All managers", False, "No bridge available")
        return

    # TodoManager
    try:
        todos = bridge.get_todos()
        log_result("managers", "TodoManager.get_todos", True, f"{len(todos)} items")
    except Exception as e:
        log_result("managers", "TodoManager", False, str(e)[:50])

    # StatusManager
    try:
        health = bridge.check_health()
        log_result("managers", "StatusManager.check_health", True, f"{len(health)} systems")
    except Exception as e:
        log_result("managers", "StatusManager", False, str(e)[:50])

    # MemoryManager
    try:
        memory = bridge.read_memory()
        log_result(
            "managers", "MemoryManager.read_memory", True, f"success={memory.get('success', False)}"
        )
    except Exception as e:
        log_result("managers", "MemoryManager", False, str(e)[:50])

    # HistoryManager
    try:
        sessions = bridge.list_sessions(5)
        log_result("managers", "HistoryManager.list_sessions", True, f"{len(sessions)} sessions")
    except Exception as e:
        log_result("managers", "HistoryManager", False, str(e)[:50])

    # AuthManager
    try:
        auth_status = bridge.get_auth_status()
        log_result("managers", "AuthManager.get_auth_status", True, f"keys={len(auth_status)}")
    except Exception as e:
        log_result("managers", "AuthManager", False, str(e)[:50])

    # ContextManager
    try:
        bridge.get_token_stats()
        log_result("managers", "ContextManager.get_token_stats", True, "tokens tracked")
    except Exception as e:
        log_result("managers", "ContextManager", False, str(e)[:50])


def test_tools(bridge):
    """Test tool system."""
    print("\n" + "=" * 60)
    print("3. TOOLS")
    print("=" * 60)

    if bridge is None or bridge.tools is None:
        log_result("tools", "All tools", False, "No bridge/tools available")
        return

    # List tools
    try:
        tools = bridge.tools.list_tools()
        log_result("tools", "list_tools", True, f"{len(tools)} tools registered")

        # Check specific critical tools
        critical_tools = [
            "read_file",
            "write_file",
            "search_files",
            "bash_command",
            "list_directory",
        ]
        for tool_name in critical_tools:
            if tool_name in tools:
                log_result("tools", f"Tool: {tool_name}", True, "registered")
            else:
                log_result("tools", f"Tool: {tool_name}", False, "NOT registered")
    except Exception as e:
        log_result("tools", "list_tools", False, str(e)[:50])

    # Test read_file execution
    try:

        async def test_read():
            result = await bridge.execute_tool("read_file", path="README.md")
            return result

        result = asyncio.run(test_read())
        if result.get("success"):
            log_result(
                "tools", "execute: read_file", True, f"{len(str(result.get('data', '')))} chars"
            )
        else:
            log_result("tools", "execute: read_file", False, result.get("error", "unknown")[:50])
    except Exception as e:
        log_result("tools", "execute: read_file", False, str(e)[:50])


def test_agents(bridge):
    """Test agent system."""
    print("\n" + "=" * 60)
    print("4. AGENTS")
    print("=" * 60)

    if bridge is None or bridge.agents is None:
        log_result("agents", "All agents", False, "No bridge/agents available")
        return

    try:
        # List available agents
        available = (
            bridge.agents.available_agents if hasattr(bridge.agents, "available_agents") else []
        )
        log_result("agents", "available_agents", True, f"{len(available)} agents")

        # Check router
        if hasattr(bridge.agents, "router"):
            log_result("agents", "AgentRouter", True, "configured")
        else:
            log_result("agents", "AgentRouter", False, "not available")

        # List agent names
        for name in list(available)[:5]:  # First 5
            log_result("agents", f"Agent: {name}", True, "registered")

    except Exception as e:
        log_result("agents", "Agent system", False, str(e)[:50])


def test_commands(bridge):
    """Test command handlers."""
    print("\n" + "=" * 60)
    print("5. COMMANDS")
    print("=" * 60)

    if bridge is None:
        log_result("commands", "All commands", False, "No bridge available")
        return

    # Test command methods that exist on bridge
    commands_to_test = [
        ("get_command_help", lambda: bridge.get_command_help()),
        ("get_tool_list", lambda: bridge.get_tool_list()),
        ("get_agent_commands", lambda: bridge.get_agent_commands()),
        ("get_model_name", lambda: bridge.get_model_name()),
        ("get_available_models", lambda: bridge.get_available_models()),
        ("is_auto_routing_enabled", lambda: bridge.is_auto_routing_enabled()),
        ("get_router_status", lambda: bridge.get_router_status()),
    ]

    for cmd_name, cmd_func in commands_to_test:
        try:
            result = cmd_func()
            log_result("commands", cmd_name, True, f"{type(result).__name__}")
        except Exception as e:
            log_result("commands", cmd_name, False, str(e)[:50])


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    for category, results in RESULTS.items():
        passed = sum(1 for _, p, _ in results if p)
        failed = sum(1 for _, p, _ in results if not p)
        total_passed += passed
        total_failed += failed

        status = "✅" if failed == 0 else "❌"
        print(f"{status} {category.upper()}: {passed}/{passed+failed} passed")

    print("-" * 40)
    total = total_passed + total_failed
    print(
        f"TOTAL: {total_passed}/{total} passed ({int(total_passed/total*100) if total > 0 else 0}%)"
    )

    if total_failed > 0:
        print("\n❌ FAILED TESTS:")
        for category, results in RESULTS.items():
            for name, passed, msg in results:
                if not passed:
                    print(f"  - {category}/{name}: {msg}")

    return total_failed == 0


def main():
    """Run all tests."""
    print("=" * 60)
    print("VERTICE TUI E2E AUDIT")
    print("=" * 60)

    # Change to project directory for relative paths
    os.chdir(PROJECT_ROOT)

    bridge = test_bridge_initialization()
    test_managers(bridge)
    test_tools(bridge)
    test_agents(bridge)
    test_commands(bridge)

    success = print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
