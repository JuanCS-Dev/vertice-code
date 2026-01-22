import asyncio
import sys
from typing import Any
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append("/media/juan/DATA/Vertice-Code/src")

from vertice_tui.core.autoaudit.service import AutoAuditService, ScenarioResult, AuditReport
from vertice_tui.core.autoaudit.scenarios import AuditScenario, Expectation, ScenarioCategory

# Mock Components
class MockView:
    def __init__(self):
        self.chunks = []
        self.logs = []
    
    def add_system_message(self, msg):
        print(f"[SYSTEM]: {msg}")
        self.logs.append(msg)
        
    def add_error(self, msg):
        print(f"[ERROR]: {msg}")
        self.logs.append(msg)
        
    def add_response_panel(self, text, title):
        print(f"\n[PANEL '{title}']: {text}")
        
    def append_chunk(self, chunk):
        print(f"{chunk}", end="")
        self.chunks.append(chunk)

class MockApp:
    def __init__(self):
        self.bridge = MagicMock()
        self.router = AsyncMock()
        self._handle_chat = AsyncMock()

# Mock Scenario that fails
FAILING_SCENARIO = AuditScenario(
    id="test_fail_001",
    category=ScenarioCategory.SECURITY,
    description="Forced Failure Test",
    prompt="DO FAIL",
    expectations=[Expectation.HANDLES_ERROR],
    timeout_seconds=1
)

async def test_hybrid_healing():
    print("--- STARTING HYBRID SELF-HEALING TEST ---")
    
    app = MockApp()
    view = MockView()
    
    # Initialize service with failing scenario
    service = AutoAuditService(app, view, scenarios=[FAILING_SCENARIO])
    
    # Mock _execute_scenario to fail immediately
    async def mock_execute(scenario):
        return ScenarioResult(
            scenario_id=scenario.id,
            status="FAILURE",
            start_time=0,
            end_time=1,
            latency_ms=1000,
            error_message="Simulated Fatal Error for Testing",
            exception_trace="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise Exception('Boom')\nException: Boom"
        )
    
    service._execute_scenario = mock_execute
    
    # Run Service
    await service.run()
    
    print("\n\n--- TEST ANALYSIS ---")
    log_str = str(view.logs)
    
    checks = {
        "Prometheus Triggered": "🚑 **Prometheus Self-Healing Triggered**" in log_str,
        "Coder Activated": "🛠️ **Coder Agent Activated**" in log_str,
        "Diagnosis Panel": "[PANEL '🔥 Prometheus Diagnosis']" in str(sys.stdout), # Hard to check mocked print, relying on logs
    }
    
    print("Checks:", checks)
    
    if all(checks.values()):
        print("✅ SUCCESS: Hybrid Workflow Complete")
    else:
        # Check logs for Coder activation
        if "🛠️ **Coder Agent Activated**" in log_str:
             print("✅ Coder Activated")
        else:
             print("❌ Coder NOT Activated")

if __name__ == "__main__":
    asyncio.run(test_hybrid_healing())
