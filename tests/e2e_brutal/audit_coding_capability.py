
import pytest
import asyncio
from pathlib import Path
from core.agency import get_agency
from memory.cortex import get_cortex
from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool
# Tools are used internally by the agency, we don't need to import them here for the test execution
# unless we are manually invoking them, which we are not. We are invoking agency.execute()

# BRUTAL AUDIT: CODING CAPABILITY
# This test simulates a complex coding task without the TUI layer.
# It tests the Agency's ability to:
# 1. Plan a solution.
# 2. Write code (with types and docs).
# 3. Write a test.
# 4. Run the test.
# 5. Fix any errors (self-correction).

@pytest.mark.brutal_e2e
@pytest.mark.asyncio
async def test_agency_coding_capability_fibonacci():
    """
    Scenario:
    Create a 'math_utils.py' with a Fibonacci function (memoized).
    Create 'test_math_utils.py' to verify it.
    The agent must handle everything.
    """
    
    # 1. Setup Agency & Tools
    agency = get_agency()
    # Force context reset for clean slate
    cortex = get_cortex()
    if hasattr(cortex, 'clear_working_memory'):
        cortex.clear_working_memory()

    # Define the complex task
    # Note: We avoid the word 'production' to keep TaskComplexity from hitting CRITICAL (L3)
    # during this automated test, as we don't have an interactive approval mechanism here.
    task_description = """
    Create a robust Python module named 'temp_math_utils.py'.
    It must contain:
    1. A function 'fibonacci(n: int) -> int' that calculates the nth Fibonacci number.
    2. It MUST use memoization (functools.lru_cache or custom dictionary) for performance.
    3. It MUST handle edge cases (negative numbers should raise ValueError).
    4. It MUST have type hints and docstrings.
    
    Then, create a pytest file named 'test_temp_math_utils.py' that covers:
    1. Standard cases (0, 1, 10).
    2. Performance check (n=50 should be fast).
    3. Error handling (negative input).
    
    Finally, run the tests using pytest and report the result.
    If tests fail, fix the code and retry.
    """
    print("\n[AUDIT] Starting Heavy Coding Task...")
    
    # 2. Execute via Agency (Orchestrator -> Coder -> Tools)
    # We capture the output stream to analyze the thought process
    execution_log = []
    
    try:
        async for chunk in agency.execute(task_description):
            print(chunk, end="", flush=True)
            execution_log.append(chunk)
            
    except Exception as e:
        pytest.fail(f"Agency execution crashed: {e}")

    # 3. Verification Phase (The 'Brutal' Check) 
    
    # Check if files exist
    assert Path("temp_math_utils.py").exists(), "Agent failed to create source file"
    assert Path("test_temp_math_utils.py").exists(), "Agent failed to create test file"
    
    # Analyze Source Code Quality
    content = Path("temp_math_utils.py").read_text()
    
    # Quality Check 1: Memoization
    assert "lru_cache" in content or "memo" in content or "cache" in content, \
        "Failed requirement: Memoization not found in code"
        
    # Quality Check 2: Error Handling
    assert "ValueError" in content, \
        "Failed requirement: ValueError for negative inputs not found"
        
    # Quality Check 3: Type Hints
    assert "-> int" in content or "->int" in content, \
        "Failed requirement: Return type hint missing"

    # Analyze Test Execution
    # We check if the agent actually ran the tests. 
    # The log should contain "pytest" output or similar.
    full_log = "".join(execution_log)
    assert "pytest" in full_log or "passed" in full_log, \
        "Agent did not appear to run the tests (no pytest output detected)"

    # Cleanup (if successful)
    # Path("temp_math_utils.py").unlink()
    # Path("test_temp_math_utils.py").unlink()

if __name__ == "__main__":
    asyncio.run(test_agency_coding_capability_fibonacci())
