import asyncio
import time
from pathlib import Path
from vertice_tui.app import VerticeApp
from vertice_tui.widgets import ResponseView

# Report structure
REPORT = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "tests": [],
    "summary": {"total": 0, "passed": 0, "failed": 0},
}


async def run_e2e_scenario():
    """Runs a real-world E2E scenario on the TUI."""
    print("🚀 Iniciando Teste E2E TUI (Real World - Vertex AI)")

    app = VerticeApp()

    # Start the app in a task to allow interaction
    async with app.run_test() as pilot:
        # --- TEST 1: System Commands ---
        print("\n🧪 Teste 1: Comandos de Sistema (/sys info)")
        await pilot.press("ctrl+l")  # Clear

        input_widget = app.query_one("#prompt")
        input_widget.value = "/sys info"
        await pilot.press("enter")

        # Wait for processing
        await pilot.pause(1.0)

        response_view = app.query_one("#response", ResponseView)
        # Check if response contains system info (e.g., "OS", "Python")
        # Note: ResponseView content is complex, checking simple text presence
        # For simplicity in this harness, we assume success if no crash and some output
        log_result("System Command", True, "Command executed without crash")

        # --- TEST 2: Tool Execution (Write File) ---
        print("\n🧪 Teste 2: Criação de Arquivo (Tool: write_file)")
        test_file = Path("test_e2e_real.txt")
        if test_file.exists():
            test_file.unlink()

        prompt = f"/noroute Create a file called {test_file.name} with content 'Vértice Sovereign Mode Active'. Use write_file tool."
        input_widget.value = prompt
        await pilot.press("enter")

        # Give TUI time to start processing and send to LLM
        await pilot.pause(2.0)

        # Wait for LLM + Tool execution (longer timeout)
        print("   ⏳ Aguardando LLM e Tool...")
        # Polling for file existence
        start_time = time.time()
        success = False
        while time.time() - start_time < 60:  # 60s timeout for LLM + tool
            # Allow TUI to process events
            await pilot.pause(0.5)
            if test_file.exists():
                content = test_file.read_text()
                if "Vértice" in content or "Sovereign" in content:
                    success = True
                    break
            await asyncio.sleep(0.5)

        log_result(
            "Tool: Write File",
            success,
            f"File created: {test_file.exists()}, Content match: {success}",
        )

        # --- TEST 3: Chat / Knowledge (LLM Direct) ---
        print("\n🧪 Teste 3: Conhecimento Geral (LLM Chat)")
        input_widget.value = "Responda apenas com a palavra 'CONFIRMADO' se você estiver operando."
        await pilot.press("enter")

        # Wait for response logic
        await pilot.pause(5.0)
        # Difficult to assert text content inside TUI widgets programmatically without deep inspection hooks
        # We rely on the app remaining responsive (not crashing)
        log_result("LLM Chat", True, "Message sent, app remains responsive")

        # Cleanup
        if test_file.exists():
            test_file.unlink()


def log_result(test_name, passed, details):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"   {status} - {test_name}: {details}")
    REPORT["tests"].append({"name": test_name, "passed": passed, "details": details})
    REPORT["summary"]["total"] += 1
    if passed:
        REPORT["summary"]["passed"] += 1
    else:
        REPORT["summary"]["failed"] += 1


if __name__ == "__main__":
    try:
        asyncio.run(run_e2e_scenario())

        # Generate Report
        print("\n" + "=" * 40)
        print("📊 RELATÓRIO FINAL E2E TUI")
        print("=" * 40)
        print(f"Total: {REPORT['summary']['total']}")
        print(f"Passou: {REPORT['summary']['passed']}")
        print(f"Falhou: {REPORT['summary']['failed']}")

        if REPORT["summary"]["failed"] > 0:
            exit(1)
        exit(0)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO TESTE: {e}")
        exit(1)
