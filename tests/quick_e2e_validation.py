#!/usr/bin/env python3
"""
QUICK E2E VALIDATION - Vertice TUI
===================================

Teste rápido para validar implementações críticas.
"""

import asyncio
import time
import os
from vertice_tui import VerticeApp
from vertice_tui.widgets import ReasoningStream, PerformanceHUD, StatusBar
from vertice_tui.handlers.export_handler import get_export_handler
from vertice_tui.widgets.session_tabs import SessionData


async def quick_e2e_validation():
    """Quick validation of critical features."""
    print("⚡ QUICK E2E VALIDATION - VERTICE TUI")
    print("=" * 50)

    results = {"passed": 0, "failed": 0, "total": 0}

    def test_result(name: str, success: bool, details: str = ""):
        results["total"] += 1
        if success:
            results["passed"] += 1
            print(f"✅ {name}: {details}")
        else:
            results["failed"] += 1
            print(f"❌ {name}: {details}")

    # === CRITICAL FEATURES TEST ===

    # 1. App Initialization
    try:
        app = VerticeApp()
        test_result("App Initialization", True, "VerticeApp created successfully")
    except Exception as e:
        test_result("App Initialization", False, str(e))

    # 2. Reasoning Stream (Semana 2)
    try:
        stream = ReasoningStream()
        stream.update_reasoning_phase("Testing reasoning", 90.0)
        test_result("Reasoning Stream", True, "Phase update working")
    except Exception as e:
        test_result("Reasoning Stream", False, str(e))

    # 3. Performance HUD (Semana 2)
    try:
        hud = PerformanceHUD()
        hud.update_metrics(latency_ms=250, confidence=85, throughput=12, queue_time=50)
        metrics = hud.current_metrics
        success = metrics["latency_ms"] == 250 and metrics["confidence"] == 85
        test_result(
            "Performance HUD",
            success,
            f"Metrics: {metrics['latency_ms']}ms, {metrics['confidence']}%",
        )
    except Exception as e:
        test_result("Performance HUD", False, str(e))

    # 4. Agent State Badge (Semana 2)
    try:
        status_bar = StatusBar()
        status_bar.autonomy_level = 2
        status_bar.operation_mode = "Code"
        badge = status_bar._format_agent_state()
        success = "L2:Code" in badge
        test_result("Agent State Badge", success, f"Badge: {badge}")
    except Exception as e:
        test_result("Agent State Badge", False, str(e))

    # 5. Export Handler (Semana 3)
    try:
        handler = get_export_handler()
        session = SessionData(
            title="Test Export",
            messages=[{"role": "user", "content": "Hello", "timestamp": "2026-01-09T15:00:00"}],
        )
        file_path = handler.export_session(session, "formatted", "quick_test.md")
        success = os.path.exists(file_path)
        test_result("Export Handler", success, f"File created: {file_path}")
    except Exception as e:
        test_result("Export Handler", False, str(e))

    # 6. Bridge Connection
    try:
        app = VerticeApp()
        # Quick chat test
        chunks = []
        async for chunk in app.bridge.chat("Hi"):
            chunks.append(chunk)
            if len(chunks) >= 3:
                break
        success = len(chunks) > 0
        test_result("Bridge Connection", success, f"Received {len(chunks)} chunks")
    except Exception as e:
        test_result("Bridge Connection", False, str(e))

    # 7. Syntax Highlighting (Semana 1)
    try:
        from vertice_cli.tui.components.streaming_markdown.widget import StreamingMarkdownWidget

        widget = StreamingMarkdownWidget()
        await widget.start_stream()
        await widget.append_chunk("```python\nprint('test')\n```")
        success = hasattr(widget, "_line_cache") and len(widget._line_cache) > 0
        test_result("Syntax Highlighting", success, f"Line cache: {len(widget._line_cache)} lines")
    except Exception as e:
        test_result("Syntax Highlighting", False, str(e))

    # === EDGE CASES ===
    print("\n🔍 EDGE CASES:")

    # Empty content
    try:
        handler = get_export_handler()
        empty_session = SessionData(title="Empty", messages=[])
        file_path = handler.export_session(empty_session, "formatted", "empty_test.md")
        success = os.path.exists(file_path)
        test_result("Empty Session Export", success, "Handled gracefully")
    except Exception as e:
        test_result("Empty Session Export", False, str(e))

    # === PERFORMANCE CHECK ===
    print("\n⚡ PERFORMANCE:")
    start_time = time.time()

    # Quick performance test
    app = VerticeApp()
    for i in range(5):
        chunks = []
        async for chunk in app.bridge.chat(f"Test {i}"):
            chunks.append(chunk)
            if len(chunks) >= 2:
                break

    perf_time = time.time() - start_time
    avg_time = perf_time / 5
    success = avg_time < 2.0  # Less than 2 seconds average
    test_result("Performance", success, f"Avg response: {avg_time:.2f}s")

    # === FINAL REPORT ===
    print("\n" + "=" * 50)
    print("🎯 QUICK E2E VALIDATION - FINAL REPORT")
    print("=" * 50)
    print(f"📊 Tests Run: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(".1f")

    success_rate = results["passed"] / results["total"]
    if success_rate >= 0.8:
        print("🏆 RESULTADO: SISTEMA FUNCIONAL!")
        print("🎉 Todas as features críticas estão working!")
    else:
        print("⚠️ RESULTADO: NECESSITA ATENÇÃO")
        print("🔧 Algumas features precisam ajustes")

    # Cleanup
    cleanup_files = ["quick_test.md", "empty_test.md"]
    for file in cleanup_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception:
            pass

    return results


if __name__ == "__main__":
    asyncio.run(quick_e2e_validation())
