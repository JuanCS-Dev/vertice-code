#!/usr/bin/env python3
"""
E2E Test Runner for Vertice-Code
Simple comprehensive E2E testing
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path


async def run_e2e_tests():
    """Run comprehensive E2E tests."""
    print("🚀 Starting E2E Tests...")
    print("=" * 50)

    results = {}
    errors = []

    # Test 1: Component Imports
    print("📦 Testing Component Imports...")
    for component in ["vertice_core", "vertice_tui", "vertice_core", "prometheus"]:
        try:
            __import__(component)
            results[f"{component}_import"] = "PASS"
            print(f"  ✅ {component}")
        except Exception as e:
            results[f"{component}_import"] = "FAIL"
            errors.append(f"{component} import: {e}")
            print(f"  ❌ {component}: {e}")

    # Test 2: Dependency Validation
    print("🔍 Testing Dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "tools/validate_dependencies.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            results["dependencies"] = "PASS"
            print("  ✅ Dependencies validated")
        else:
            results["dependencies"] = "FAIL"
            errors.append("Dependency validation failed")
            print("  ❌ Dependencies failed")
    except Exception as e:
        results["dependencies"] = "FAIL"
        errors.append(f"Dependency test error: {e}")
        print(f"  ❌ Dependencies error: {e}")

    # Test 3: CLI Integration
    print("💻 Testing CLI...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "vertice_core.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "Usage:" in result.stdout:
            results["cli"] = "PASS"
            print("  ✅ CLI working")
        else:
            results["cli"] = "FAIL"
            errors.append("CLI test failed")
            print("  ❌ CLI failed")
    except Exception as e:
        results["cli"] = "FAIL"
        errors.append(f"CLI error: {e}")
        print(f"  ❌ CLI error: {e}")

    # Test 4: Backend Health
    print("🌐 Testing Backend...")
    try:
        # Start backend briefly
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "vertice-chat-webapp.backend.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8002",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        await asyncio.sleep(3)  # Wait for startup

        # Test health endpoint
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:8002/health")
            if response.status_code == 200:
                results["backend"] = "PASS"
                print("  ✅ Backend healthy")
            else:
                results["backend"] = "FAIL"
                errors.append("Backend health check failed")
                print("  ❌ Backend unhealthy")

        backend.terminate()
        backend.wait()

    except Exception as e:
        results["backend"] = "FAIL"
        errors.append(f"Backend error: {e}")
        print(f"  ❌ Backend error: {e}")

    # Test 5: MCP Connection
    print("🔗 Testing MCP Server...")
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://vertice-mcp-server-452089804714.us-central1.run.app/health"
            )
            if response.status_code == 200:
                results["mcp"] = "PASS"
                print("  ✅ MCP server reachable")
            else:
                results["mcp"] = "SKIP"
                print("  ⚠️  MCP server not reachable")
    except Exception as e:
        results["mcp"] = "SKIP"
        print(f"  ⚠️  MCP server unavailable: {e}")

    # Calculate results
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print("\n" + "=" * 50)
    print("E2E TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Overall: {'PASS' if passed == total else 'PARTIAL'}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors[:3]:
            print(f"  • {error}")

    # Save report
    report = {
        "timestamp": time.time(),
        "results": results,
        "errors": errors,
        "summary": {"passed": passed, "total": total, "success_rate": success_rate},
    }

    report_file = Path("tests/e2e_results.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved: {report_file}")

    return success_rate >= 80  # 80% success threshold


if __name__ == "__main__":
    success = asyncio.run(run_e2e_tests())
    sys.exit(0 if success else 1)
