import asyncio
import sys
import os
import shutil
from typing import Any
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append("/media/juan/DATA/Vertice-Code/src")

from vertice_tui.core.autoaudit.service import AutoAuditService, ScenarioResult, AuditReport
from vertice_tui.core.autoaudit.scenarios import AuditScenario, Expectation, ScenarioCategory

# --- TEST TARGET ---
BROKEN_FILE = "/media/juan/DATA/Vertice-Code/src/broken_example.py"
BROKEN_CONTENT = """
def calculate_sum(a, b)
    return a + b  # Syntax Error: missing colon
"""

def setup_broken_file():
    with open(BROKEN_FILE, "w") as f:
        f.write(BROKEN_CONTENT)
    print(f"Created broken file at: {BROKEN_FILE}")

def cleanup_broken_file():
    if os.path.exists(BROKEN_FILE):
        os.remove(BROKEN_FILE)
        print(f"Cleaned up: {BROKEN_FILE}")

# Mock Components
class MockView:
    def __init__(self):
        self.chunks = []
        self.logs = []
    
    def add_system_message(self, msg):
        self.logs.append(msg)
        
    def add_error(self, msg):
        self.logs.append(f"[ERROR] {msg}")
    
    def add_response_panel(self, text, title):
        print(f"\n[PANEL '{title}'] initialized")
        
    def append_chunk(self, chunk):
        print(f"{chunk}", end="")
        self.chunks.append(chunk)

class MockApp:
    def __init__(self):
        self.bridge = MagicMock()
        self.router = AsyncMock()
        self._handle_chat = AsyncMock()

# Scenario that "fails" by detecting the syntax error
REAL_FAILING_SCENARIO = AuditScenario(
    id="qa_syntax_check",
    category=ScenarioCategory.CODING,
    description="Check syntax of broken_example.py",
    prompt="Check syntax of src/broken_example.py",
    expectations=[Expectation.HANDLES_ERROR],
    timeout_seconds=5
)

async def test_fix_quality():
    print("--- STARTING QUALITY ASSURANCE TEST ---")
    setup_broken_file()
    
    app = MockApp()
    view = MockView()
    
    # Initialize service
    service = AutoAuditService(app, view, scenarios=[REAL_FAILING_SCENARIO])
    
    # We simulate the Scenario Execution detecting the error
    # In a real run, a tool would catch this. Here we mock the detection part
    # but let the HEALING part (Prometheus + Coder) run effectively against the real file.
    async def mock_execute(scenario):
        return ScenarioResult(
            scenario_id=scenario.id,
            status="FAILURE",
            start_time=0,
            end_time=1,
            latency_ms=1000,
            error_message="SyntaxError in src/broken_example.py",
            exception_trace=f"File '{BROKEN_FILE}', line 2\n    def calculate_sum(a, b)\n                          ^\nSyntaxError: expected ':'"
        )
    
    service._execute_scenario = mock_execute
    
    service._execute_scenario = mock_execute
    
    # --- REAL AGENT EXECUTION ---
    # User confirms Vertex AI is functional. We trust the Code.
    # No Mocks.
    
    # TRIGGER HEALING
    try:
        await service.run()
    except Exception as e:
        print(f"Service crashed: {e}")
    
    print("\n\n--- QUALITY ANALYSIS ---")
    
    # 1. Verify File Content
    with open(BROKEN_FILE, "r") as f:
        content = f.read()
    
    print(f"Current File Content:\n{content}")
    
    if "def calculate_sum(a, b):" in content:
        print("✅ QUALITY CHECK 1: Syntax Fixed (Colon added)")
    else:
        print("❌ QUALITY CHECK 1: Syntax NOT Fixed")
        
    # 2. Verify Execution
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("broken_example", BROKEN_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        res = module.calculate_sum(10, 20)
        if res == 30:
            print("✅ QUALITY CHECK 2: Code Execution Verified (Result=30)")
        else:
             print(f"❌ QUALITY CHECK 2: Execution Result Wrong: {res}")
    except Exception as e:
        print(f"❌ QUALITY CHECK 2: Execution Failed: {e}")

    cleanup_broken_file()

if __name__ == "__main__":
    asyncio.run(test_fix_quality())
