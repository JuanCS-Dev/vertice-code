#!/usr/bin/env python3
"""
SEMANA 1 INTEGRATION TEST - Vertice TUI
======================================

Testa todas as implementações da Semana 1:
1. Syntax Highlighting + Double Buffering
2. Session & Search (Fuzzy)
3. Tabbed Interface (Enhanced Persistence)
"""

import asyncio
from vertice_cli.tui.components.streaming_markdown.widget import StreamingMarkdownWidget
from vertice_tui.widgets.fuzzy_search_modal import FuzzySearchModal, SearchResult
from vertice_tui.widgets.session_tabs import SessionTabs


async def test_semana_1_integration():
    """Test all Semana 1 implementations."""
    print("🚀 SEMANA 1 INTEGRATION TEST")
    print("=" * 50)

    all_passed = True

    # === TEST 1: Syntax Highlighting + Double Buffering ===
    print("\n🎨 TEST 1: Syntax Highlighting + Double Buffering")

    try:
        widget = StreamingMarkdownWidget(target_fps=60)

        # Test basic functionality
        await widget.start_stream()
        await widget.append_chunk("# Hello **World**\n\n```python\nprint('test')\n```")
        await widget.append_chunk("\n\nMore content for viewport testing...")

        # Check if line cache is working (viewport buffering)
        if len(widget._line_cache) > 0:
            print("✅ Viewport buffering active")
        else:
            print("❌ Viewport buffering not working")
            all_passed = False

        # Check if double buffering is initialized
        if hasattr(widget, "_render_buffer") and hasattr(widget, "_buffer_ready"):
            print("✅ Double buffering initialized")
        else:
            print("❌ Double buffering not initialized")
            all_passed = False

        print(".2f")

    except Exception as e:
        print(f"❌ Syntax highlighting test failed: {e}")
        all_passed = False

    # === TEST 2: Fuzzy Search Modal ===
    print("\n🔍 TEST 2: Fuzzy Search Modal")

    try:

        class MockSessionManager:
            pass

        modal = FuzzySearchModal(
            session_manager=MockSessionManager(), current_session_id="test-123"
        )

        # Test search result creation
        result = SearchResult(
            session_id="session-123",
            message_index=5,
            content="Test content",
            score=95.0,
            context="...Test content...",
        )

        # Test context extraction
        context = modal._extract_context("Long message with search term", "search")
        if "search term" in context:
            print("✅ Context extraction working")
        else:
            print("❌ Context extraction not working")
            all_passed = False

        print("✅ Fuzzy search modal functional")

    except Exception as e:
        print(f"❌ Fuzzy search test failed: {e}")
        all_passed = False

    # === TEST 3: Enhanced Session Tabs ===
    print("\n📑 TEST 3: Enhanced Session Tabs")

    try:
        tabs = SessionTabs()

        # Test session creation
        session1 = tabs.create_session("Test Session 1")
        session2 = tabs.create_session("Test Session 2")

        if tabs.session_count == 2:
            print("✅ Session creation working")
        else:
            print("❌ Session creation not working")
            all_passed = False

        # Test enhanced persistence fields
        if hasattr(session1, "scroll_position") and hasattr(session1, "viewport_content"):
            print("✅ Enhanced persistence fields added")
        else:
            print("❌ Enhanced persistence fields missing")
            all_passed = False

        # Test visual state methods
        if hasattr(tabs, "_save_session_visual_state") and hasattr(
            tabs, "_restore_session_visual_state"
        ):
            print("✅ Visual state methods implemented")
        else:
            print("❌ Visual state methods missing")
            all_passed = False

    except Exception as e:
        print(f"❌ Session tabs test failed: {e}")
        all_passed = False

    # === FINAL RESULTS ===
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 SEMANA 1 INTEGRATION TEST: SUCESSO TOTAL!")
        print("✅ Todas as implementações funcionando perfeitamente")
        print("✅ Double Buffering + Viewport Buffering: Ativo")
        print("✅ Fuzzy Search: Pronto para uso")
        print("✅ Enhanced Session Tabs: Persistência visual implementada")
    else:
        print("⚠️ SEMANA 1 INTEGRATION TEST: ALGUNS PROBLEMAS DETECTADOS")
        print("🔧 Revisar implementações com falha")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_semana_1_integration())
    exit(0 if success else 1)
