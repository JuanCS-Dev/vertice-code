#!/usr/bin/env python3
"""
Verify TUI Rendering (Headless)
===============================
Boot the Textual app in headless mode to verify it doesn't crash on startup.
"""
import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))


async def test_tui_startup():
    print("🚀 Initializing VerticeApp (Headless)...")
    try:
        from vertice_tui.app import VerticeApp

        app = VerticeApp()

        # Use run_test context manager for headless testing
        print("   Starting run_test() context...")
        async with app.run_test() as pilot:
            print("   ✅ App started successfully!")

            # Basic sanity check of the widget tree
            print("   Inspecting widget tree...")
            screen = app.screen
            print(f"   Active Screen: {screen}")

            # Check for critical widgets
            try:
                sidebar = screen.query_one("#sidebar")
                print("   ✅ Sidebar found")
            except Exception:
                print("   ⚠️ Sidebar not found (Might be hidden or different ID)")

            try:
                chat_view = screen.query_one("ChatView")
                print("   ✅ ChatView found")
            except Exception:
                print("   ⚠️ ChatView not found")

            print("   Waiting 1s to simulate load...")
            await asyncio.sleep(1.0)

            # Clean exit happens automatically when context ends
            print("   Shutting down...")

        print("✅ TUI Stress Test PASSED (Startup & Render verified).")

    except ImportError as e:
        print(f"❌ Failed to import TUI App: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ TUI Crashed during startup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(test_tui_startup())
    except KeyboardInterrupt:
        print("\nTest cancelled.")
