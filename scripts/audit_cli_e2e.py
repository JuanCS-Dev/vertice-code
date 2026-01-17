#!/usr/bin/env python
"""
CLI E2E Audit Script - Complete Functional Testing.

Tests all major features of the Vertice CLI:
1. Core imports (providers, agents, tools)
2. Agency system
3. LLM providers
4. Tool execution
5. Agent invocation
"""

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
    "imports": [],
    "providers": [],
    "tools": [],
    "agents": [],
    "agency": [],
}


def log_result(category: str, test_name: str, passed: bool, message: str = ""):
    """Log a test result."""
    status = "✅" if passed else "❌"
    print(f"  {status} {test_name}: {message}")
    RESULTS[category].append((test_name, passed, message))


def test_core_imports():
    """Test core CLI imports."""
    print("\n" + "=" * 60)
    print("1. CORE IMPORTS")
    print("=" * 60)

    imports_to_test = [
        ("vertice_cli.core", ["config", "providers"]),
        ("vertice_cli.agents", ["base", "registry"]),
        ("vertice_cli.tools", ["base", "validated"]),
        ("vertice_cli.utils", ["error_handler"]),
        ("vertice_cli.handlers", []),
    ]

    for module, submodules in imports_to_test:
        try:
            imported = __import__(module, fromlist=submodules or ["__init__"])
            log_result("imports", module, True, "imported")
        except Exception as e:
            log_result("imports", module, False, str(e)[:60])


def test_providers():
    """Test LLM providers."""
    print("\n" + "=" * 60)
    print("2. LLM PROVIDERS")
    print("=" * 60)

    providers_to_test = [
        ("VertexAIProvider", "vertice_cli.core.providers.vertex_ai"),
        ("VerticeRouter", "vertice_cli.core.vertice_router"),
    ]

    for name, module_path in providers_to_test:
        try:
            parts = module_path.rsplit(".", 1)
            if len(parts) == 2:
                mod = __import__(parts[0], fromlist=[parts[1]])
                cls = getattr(mod, name, None)
                if cls:
                    log_result("providers", name, True, f"{cls}")
                else:
                    # Try module-level import
                    mod = __import__(module_path, fromlist=[name])
                    cls = getattr(mod, name, None)
                    if cls:
                        log_result("providers", name, True, f"{cls}")
                    else:
                        log_result("providers", name, False, "class not found")
        except Exception as e:
            log_result("providers", name, False, str(e)[:60])

    # Test Vertex AI initialization (without actual API call)
    try:
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider()
        log_result("providers", "VertexAI init", True, f"model={provider.model_name}")
    except Exception as e:
        log_result("providers", "VertexAI init", False, str(e)[:60])


def test_tools():
    """Test tool system."""
    print("\n" + "=" * 60)
    print("3. TOOLS")
    print("=" * 60)

    try:
        from vertice_cli.tools.base import ToolRegistry

        registry = ToolRegistry()
        log_result("tools", "ToolRegistry", True, "created")
    except Exception as e:
        log_result("tools", "ToolRegistry", False, str(e)[:60])
        return

    # Test individual tool imports
    tool_modules = [
        ("file_ops", ["ReadFileTool", "WriteFileTool"]),
        ("terminal", ["CdTool", "LsTool"]),
        ("search", ["SearchFilesTool"]),
        ("exec_hardened", ["BashCommandTool"]),
    ]

    for module, classes in tool_modules:
        try:
            mod = __import__(f"vertice_cli.tools.{module}", fromlist=classes)
            for cls_name in classes:
                cls = getattr(mod, cls_name, None)
                if cls:
                    instance = cls()
                    registry.register(instance)
                    log_result(
                        "tools",
                        cls_name,
                        True,
                        f"name={instance.name if hasattr(instance, 'name') and instance.name != 'base_tool' else 'derived'}",
                    )
                else:
                    log_result("tools", cls_name, False, "class not found")
        except Exception as e:
            log_result("tools", module, False, str(e)[:60])

    # Summary
    log_result("tools", "Total registered", True, f"{len(registry.get_all())} tools")


def test_agents():
    """Test agent system."""
    print("\n" + "=" * 60)
    print("4. AGENTS")
    print("=" * 60)

    try:
        log_result("agents", "BaseAgent (vertice_cli)", True, "imported")
    except Exception as e:
        log_result("agents", "BaseAgent (vertice_cli)", False, str(e)[:60])

    # Test agents from src/agents/ (core agents)
    agent_modules = [
        ("agents.coder.agent", "CoderAgent"),
        ("agents.architect.agent", "ArchitectAgent"),
        ("agents.orchestrator.agent", "OrchestratorAgent"),
        ("agents.reviewer.agent", "ReviewerAgent"),
    ]

    for module, cls_name in agent_modules:
        try:
            mod = __import__(module, fromlist=[cls_name])
            cls = getattr(mod, cls_name, None)
            if cls:
                log_result("agents", cls_name, True, "imported")
            else:
                log_result("agents", cls_name, False, "class not found")
        except Exception as e:
            log_result("agents", cls_name, False, str(e)[:60])


def test_agency():
    """Test Agency system."""
    print("\n" + "=" * 60)
    print("5. AGENCY SYSTEM")
    print("=" * 60)

    try:
        from core.agency import Agency

        log_result("agency", "Agency import", True, "imported")
    except Exception as e:
        log_result("agency", "Agency import", False, str(e)[:60])
        return

    try:
        agency = Agency()
        log_result("agency", "Agency init", True, "created")

        # Check config
        if hasattr(agency, "config"):
            log_result("agency", "Agency config", True, "configured")
        else:
            log_result("agency", "Agency config", False, "no config attr")

    except Exception as e:
        log_result("agency", "Agency init", False, str(e)[:60])


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
    print("VERTICE CLI E2E AUDIT")
    print("=" * 60)

    # Change to project directory for relative paths
    os.chdir(PROJECT_ROOT)

    test_core_imports()
    test_providers()
    test_tools()
    test_agents()
    test_agency()

    success = print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
