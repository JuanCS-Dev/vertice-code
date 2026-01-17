#!/usr/bin/env python3
"""
Verify Vertice CLI Entry Points
===============================
Simulates `pip install .` + `vertice --help` behavior to catch import errors.
"""
import sys
import os
import traceback

# Add src to path to simulate installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))


def test_cli_import():
    print("Testing 'vertice' entry point...")
    try:
        from vertice_cli.main import app

        print("✅ Successfully imported vertice_cli.main.app")
    except ImportError as e:
        print(f"❌ Failed to import CLI app: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error importing CLI app: {e}")
        traceback.print_exc()
        sys.exit(1)


def test_tui_import():
    print("Testing 'vertice_tui' import...")
    try:
        # Check if textual is installed (it should be)
        import textual

        print(f"✅ Textual {textual.__version__} found.")

        # Try importing the TUI launcher
        from vertice_cli.ui_launcher import launch_tui

        print("✅ Successfully imported vertice_cli.ui_launcher.launch_tui")
    except ImportError as e:
        print(f"❌ Failed to import TUI components: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print(f"Python: {sys.version}")
    print(f"Path: {sys.path[0]}")

    test_cli_import()
    test_tui_import()

    print("\n🎉 CLI Entry Point Verification PASSED.")
    sys.exit(0)
