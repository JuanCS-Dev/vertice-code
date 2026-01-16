#!/usr/bin/env python3
"""
Open Responses E2E Test Runner

Executa suíte completa de testes E2E para Open Responses.
Gera relatório detalhado com resultados.

Uso:
    python run_openresponses_e2e.py
    python run_openresponses_e2e.py --component tui
    python run_openresponses_e2e.py --component cli
    python run_openresponses_e2e.py --component webapp
    python run_openresponses_e2e.py --component integration
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from __init__ import get_e2e_tester


def run_component_tests(component: str, tester):
    """Run tests for a specific component."""
    print(f"\n🚀 Running {component.upper()} tests...")

    import subprocess
    import sys

    if component == "tui":
        # Run TUI tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/e2e/openresponses/test_tui_e2e.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd="/media/juan/DATA/Vertice-Code",
        )

    elif component == "cli":
        # Run CLI tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/e2e/openresponses/test_cli_e2e.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd="/media/juan/DATA/Vertice-Code",
        )

    elif component == "webapp":
        # Run WebApp tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/e2e/openresponses/test_webapp_e2e.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd="/media/juan/DATA/Vertice-Code",
        )

    elif component == "integration":
        # Run Integration tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/e2e/openresponses/test_integration_e2e.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd="/media/juan/DATA/Vertice-Code",
        )

    else:
        return False

    # Print output for visibility
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def run_all_tests(tester):
    """Run all E2E tests."""
    print("🎯 OPEN RESPONSES E2E TEST SUITE")
    print("=" * 50)

    components = ["tui", "cli", "webapp", "integration"]
    results = {}

    for component in components:
        try:
            success = run_component_tests(component, tester)
            results[component] = success
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{component.upper()}: {status}")
        except Exception as e:
            print(f"{component.upper()}: ❌ ERROR - {str(e)}")
            results[component] = False

    # Generate final report
    print("\n" + "=" * 50)
    print("📊 FINAL REPORT")
    print("=" * 50)

    # Summary
    total_components = len(components)
    passed_components = sum(1 for r in results.values() if r)
    failed_components = total_components - passed_components

    print(f"Components Tested: {total_components}")
    print(f"Passed: {passed_components}")
    print(f"Failed: {failed_components}")

    success_rate = (passed_components / total_components) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {component.upper()}: {status}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if failed_components == 0:
        print("  🎉 All tests passed! Open Responses is production-ready.")
        print("  🚀 Ready for full deployment across all interfaces.")
    else:
        print("  ⚠️  Some tests failed. Check component configurations:")
        if not results.get("tui", True):
            print("     - TUI: Verify event parsing and ResponseView integration")
        if not results.get("cli", True):
            print("     - CLI: Check provider Open Responses support")
        if not results.get("webapp", True):
            print("     - WebApp: Verify streaming endpoints and SSE protocol")
        if not results.get("integration", True):
            print("     - Integration: Check cross-component communication")

    print("\n" + "=" * 50)

    return passed_components == total_components


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Open Responses E2E Test Runner")
    parser.add_argument(
        "--component",
        choices=["tui", "cli", "webapp", "integration", "all"],
        default="all",
        help="Component to test (default: all)",
    )
    parser.add_argument(
        "--webapp-url", default="http://localhost:3000", help="WebApp base URL for testing"
    )

    args = parser.parse_args()

    # Initialize tester
    tester = get_e2e_tester()
    tester.base_url = args.webapp_url

    await tester.setup()

    try:
        if args.component == "all":
            success = run_all_tests(tester)
        else:
            success = run_component_tests(args.component, tester)

        # Generate detailed report
        report = tester.generate_report()
        print("\n" + report)

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {str(e)}")
        sys.exit(1)
    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())
