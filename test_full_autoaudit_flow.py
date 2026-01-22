import asyncio
import sys
import os
import tempfile
from pathlib import Path

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
        self.bridge = type("MockBridge", (), {})()
        self.router = type("MockRouter", (), {"stream_chat": lambda *args, **kwargs: None})()
        self._handle_chat = lambda *args: None


# Create a temporary broken file with multiple quality issues
BROKEN_FILE_CONTENT = """
def calculate_sum(a, b)
    # Missing colon in function definition
    # Also, no type hints, no docstring
    return a + b

class Calculator:
    def multiply(x, y):  # Missing self
        return x * y

# Unused import
import os

# Syntax error: unclosed parenthesis
def bad_function(:
    pass

# Logic error: infinite loop
def infinite_loop():
    while True:
        pass
"""

FIXED_FILE_CONTENT = '''
def calculate_sum(a: int, b: int) -> int:
    """
    Calculate the sum of two integers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

class Calculator:
    def multiply(self, x: int, y: int) -> int:
        return x * y

# Logic error fixed: added break condition
def finite_loop():
    count = 0
    while count < 10:
        count += 1
'''


def create_broken_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(BROKEN_FILE_CONTENT)
        return f.name


def cleanup_file(filepath):
    if os.path.exists(filepath):
        os.unlink(filepath)


async def test_full_autoaudit_flow():
    print("=== TESTING FULL AUTOAUDIT FLOW ===")
    print("Creating broken Python file with multiple quality issues...")

    broken_file = create_broken_file()
    print(f"Broken file: {broken_file}")

    # Scenario that detects syntax errors
    syntax_scenario = AuditScenario(
        id="syntax_check",
        category=ScenarioCategory.CODING,
        description="Check Python syntax",
        prompt=f"Check syntax of {broken_file}",
        expectations=[Expectation.HANDLES_ERROR],
        timeout_seconds=10,
    )

    # Scenario that detects quality issues
    quality_scenario = AuditScenario(
        id="quality_check",
        category=ScenarioCategory.CODING,
        description="Check code quality",
        prompt=f"Analyze code quality of {broken_file}",
        expectations=[Expectation.HANDLES_ERROR],
        timeout_seconds=10,
    )

    app = MockApp()
    view = MockView()

    service = AutoAuditService(app, view, scenarios=[syntax_scenario, quality_scenario])

    # Mock scenario execution to simulate failures
    async def mock_execute(scenario):
        if "syntax" in scenario.id:
            return ScenarioResult(
                scenario_id=scenario.id,
                status="FAILURE",
                start_time=0,
                end_time=1,
                latency_ms=1000,
                error_message="Multiple syntax errors detected",
                exception_trace=f"SyntaxError in {broken_file}: missing colons, unclosed parentheses",
            )
        elif "quality" in scenario.id:
            return ScenarioResult(
                scenario_id=scenario.id,
                status="FAILURE",
                start_time=0,
                end_time=1,
                latency_ms=1000,
                error_message="Code quality issues detected",
                exception_trace=f"Quality issues in {broken_file}: missing type hints, docstrings, unused imports, logic errors",
            )
        return ScenarioResult(
            scenario_id=scenario.id, status="SUCCESS", start_time=0, end_time=1, latency_ms=100
        )

    service._execute_scenario = mock_execute

    print("\nRunning AutoAudit Service...")
    try:
        await service.run()
    except Exception as e:
        print(f"Service run failed: {e}")

    print("\n=== QUALITY VALIDATION ===")

    # Read final file content
    with open(broken_file, "r") as f:
        final_content = f.read()

    print(f"Final file content:\n{final_content}")

    # Quality Checks
    quality_score = 0
    total_checks = 8

    # 1. Syntax fixed
    try:
        compile(final_content, broken_file, "exec")
        print("✅ Syntax Check: PASSED - Code compiles without errors")
        quality_score += 1
    except SyntaxError as e:
        print(f"❌ Syntax Check: FAILED - {e}")

    # 2. Function definition fixed
    if "def calculate_sum(a, b):" in final_content:
        print("✅ Function Definition: PASSED - Colon added")
        quality_score += 1
    else:
        print("❌ Function Definition: FAILED - Still missing colon")

    # 3. Class method fixed
    if "def multiply(self, x, y):" in final_content:
        print("✅ Class Method: PASSED - Self parameter added")
        quality_score += 1
    else:
        print("❌ Class Method: FAILED - Missing self")

    # 4. Parentheses fixed
    if "def bad_function():" in final_content or "def bad_function(" not in final_content:
        print("✅ Parentheses: PASSED - Syntax error fixed")
        quality_score += 1
    else:
        print("❌ Parentheses: FAILED - Still has syntax error")

    # 5. Type hints added
    if ": int" in final_content and "-> int" in final_content:
        print("✅ Type Hints: PASSED - Added to functions")
        quality_score += 1
    else:
        print("❌ Type Hints: FAILED - Missing type annotations")

    # 6. Docstrings added
    if '"""' in final_content:
        print("✅ Docstrings: PASSED - Documentation added")
        quality_score += 1
    else:
        print("❌ Docstrings: FAILED - No docstrings")

    # 7. Unused imports removed
    if "import os" not in final_content:
        print("✅ Unused Imports: PASSED - Removed unnecessary imports")
        quality_score += 1
    else:
        print("❌ Unused Imports: FAILED - Still has unused import")

    # 8. Logic error fixed
    if "while count < 10:" in final_content and "infinite_loop" not in final_content:
        print("✅ Logic Error: PASSED - Infinite loop fixed")
        quality_score += 1
    else:
        print("❌ Logic Error: FAILED - Still has infinite loop")

    print(f"\n=== FINAL SCORE: {quality_score}/{total_checks} ===")
    percentage = (quality_score / total_checks) * 100
    print(".1f")

    if percentage >= 90:
        print("🎉 EXCELLENT: High-quality auto-correction achieved!")
    elif percentage >= 75:
        print("👍 GOOD: Satisfactory auto-correction with minor issues")
    elif percentage >= 50:
        print("⚠️  FAIR: Auto-correction partially successful")
    else:
        print("❌ POOR: Auto-correction needs significant improvement")

    cleanup_file(broken_file)


if __name__ == "__main__":
    asyncio.run(test_full_autoaudit_flow())
