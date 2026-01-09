#!/usr/bin/env python3
"""
E2E TUI Test - Alternative Implementation

Uses Bridge.chat() directly instead of TUI pilot which has async execution issues.
This test verifies the complete tool execution pipeline works correctly.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.getcwd())

# Report structure
REPORT = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "tests": [],
    "summary": {"total": 0, "passed": 0, "failed": 0}
}


def log_result(test_name: str, passed: bool, details: str):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"   {status} - {test_name}: {details}")
    REPORT["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    REPORT["summary"]["total"] += 1
    if passed:
        REPORT["summary"]["passed"] += 1
    else:
        REPORT["summary"]["failed"] += 1


async def run_e2e_tests():
    """Run E2E tests using Bridge.chat() directly."""
    print("🚀 E2E TEST - Bridge.chat() Direct")
    print("=" * 50)
    
    # Initialize Bridge
    from vertice_tui.core.bridge import Bridge
    bridge = Bridge()
    print(f"✓ Bridge initialized with {bridge.tools.get_tool_count()} tools")
    print()
    
    # --- TEST 1: LLM Chat (Basic) ---
    print("🧪 Teste 1: LLM Chat Básico")
    try:
        response = []
        async for chunk in bridge.chat("Respond with just 'OK' if operational.", auto_route=False):
            response.append(chunk)
        full_response = "".join(response)
        success = len(full_response) > 0
        log_result("LLM Chat", success, f"Response length: {len(full_response)} chars")
    except Exception as e:
        log_result("LLM Chat", False, f"Error: {e}")
    
    # --- TEST 2: Tool Execution (Write File) ---
    print("\n🧪 Teste 2: Tool write_file")
    test_file = Path("test_e2e_bridge.txt")
    if test_file.exists():
        test_file.unlink()
    
    try:
        response = []
        prompt = f"Create a file named {test_file.name} with content 'Vértice E2E Pass'. Use write_file tool."
        async for chunk in bridge.chat(prompt, auto_route=False):
            response.append(chunk)
        
        # Wait a moment for file system
        await asyncio.sleep(0.5)
        
        file_exists = test_file.exists()
        content_match = False
        if file_exists:
            content = test_file.read_text()
            content_match = "Vértice" in content or "E2E" in content
            test_file.unlink()
        
        success = file_exists and content_match
        log_result("Tool write_file", success, f"File: {file_exists}, Content: {content_match}")
    except Exception as e:
        log_result("Tool write_file", False, f"Error: {e}")
    
    # --- TEST 3: Tool Execution via ToolBridge ---
    print("\n🧪 Teste 3: ToolBridge.execute_tool() Direto")
    test_file2 = Path("test_toolbridge.txt")
    if test_file2.exists():
        test_file2.unlink()
    
    try:
        result = await bridge.tools.execute_tool(
            "write_file",
            path=str(test_file2),
            content="ToolBridge Direct Test"
        )
        file_exists = test_file2.exists()
        if file_exists:
            test_file2.unlink()
        
        success = result.get("success", False) and file_exists
        log_result("ToolBridge Direct", success, f"Result: {result.get('success')}, File: {file_exists}")
    except Exception as e:
        log_result("ToolBridge Direct", False, f"Error: {e}")
    
    # Report
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL E2E")
    print("=" * 50)
    print(f"Total: {REPORT['summary']['total']}")
    print(f"Passou: {REPORT['summary']['passed']}")
    print(f"Falhou: {REPORT['summary']['failed']}")
    
    return REPORT['summary']['failed'] == 0


if __name__ == "__main__":
    success = asyncio.run(run_e2e_tests())
    exit(0 if success else 1)
