#!/usr/bin/env python3
"""
TESTE: Semana 3 - Export & Safety Features
==========================================

Testa Export Handler, Export Modal, e Tecla de Pânico.
"""

import asyncio
from vertice_tui.handlers.export_handler import ExportHandler
from vertice_tui.widgets.session_tabs import SessionData
from vertice_tui.widgets.export_modal import ExportModal


async def test_semana_3():
    """Test Semana 3 implementations."""
    print("🚀 TESTING SEMANA 3 - EXPORT & SAFETY")
    print("=" * 50)

    all_passed = True

    # === TESTE 1: Export Handler ===
    print("\n📤 TESTE 1: Export Handler")

    try:
        handler = ExportHandler()

        # Create test session
        session = SessionData(
            title="Test Export Session",
            messages=[
                {"role": "user", "content": "Hello world", "timestamp": "2026-01-09T15:00:00"},
                {
                    "role": "assistant",
                    "content": "Hi! How can I help?",
                    "timestamp": "2026-01-09T15:00:01",
                },
                {
                    "role": "user",
                    "content": "Create a Python function",
                    "timestamp": "2026-01-09T15:00:02",
                },
                {
                    "role": "assistant",
                    "content": "def hello():\n    return 'world'",
                    "timestamp": "2026-01-09T15:00:03",
                },
            ],
        )

        # Test formatted export
        handler.export_session(session, "formatted", "test_formatted.md")
        print("✅ Formatted export successful")

        # Test raw export
        handler.export_session(session, "raw", "test_raw.md")
        print("✅ Raw export successful")

        # Verify files were created
        import os

        if os.path.exists("test_formatted.md"):
            print("✅ Formatted file created")
            with open("test_formatted.md", "r") as f:
                content = f.read()
                if "---" in content and "title:" in content:
                    print("✅ Frontmatter included")
                else:
                    print("❌ Frontmatter missing")
                    all_passed = False
        else:
            print("❌ Formatted file not created")
            all_passed = False

    except Exception as e:
        print(f"❌ Export Handler test failed: {e}")
        all_passed = False

    # === TESTE 2: Export Modal ===
    print("\n📋 TESTE 2: Export Modal")

    try:
        # Test modal instantiation
        sessions = [session]
        ExportModal(sessions, session.id)
        print("✅ Export Modal instantiated")

        # Test with empty sessions
        ExportModal([], None)
        print("✅ Empty modal handled")

    except Exception as e:
        print(f"❌ Export Modal test failed: {e}")
        all_passed = False

    # === TESTE 3: Safety UX (Panic Button) ===
    print("\n🚨 TESTE 3: Safety UX (Panic Button)")

    try:
        # Test that the binding exists in app
        from vertice_tui.app import VerticeApp

        app = VerticeApp()

        # Check if panic button action exists
        if hasattr(app, "action_panic_button"):
            print("✅ Panic button action exists")
        else:
            print("❌ Panic button action missing")
            all_passed = False

        # Test emergency stop logic
        app.is_processing = True
        app.action_panic_button()
        print("✅ Emergency stop triggered")

    except Exception as e:
        print(f"❌ Safety UX test failed: {e}")
        all_passed = False

    # === CLEANUP ===
    print("\n🧹 CLEANUP")
    try:
        import os

        for file in ["test_formatted.md", "test_raw.md"]:
            if os.path.exists(file):
                os.remove(file)
                print(f"✅ Cleaned up {file}")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    # === FINAL RESULTS ===
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 SEMANA 3 INTEGRATION TEST: SUCESSO TOTAL!")
        print("✅ Export Handler: Markdown com Frontmatter working")
        print("✅ Export Modal: UI para seleção de templates ready")
        print("✅ Safety UX: Tecla de Pânico implementada")
        print("✅ PKM Integration: Frontmatter para Obsidian/Notion")
    else:
        print("⚠️ SEMANA 3 INTEGRATION TEST: ALGUNS PROBLEMAS DETECTADOS")
        print("🔧 Revisar implementações com falha")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_semana_3())
    exit(0 if success else 1)
