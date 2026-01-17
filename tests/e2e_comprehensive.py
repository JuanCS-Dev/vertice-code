#!/usr/bin/env python3
"""
COMPREHENSIVE E2E TEST SUITE - VERTICE TUI BACKEND (BRIDGE)
===========================================================

This suite verifies the core capability of the Vertice system:
1. Orchestration (Auto-Routing)
2. Tool Execution (Write/Read)
3. Agent Logic
4. Streaming Response

It bypasses the Textual UI layer to test the logical core directly.
"""

import asyncio
import os
import sys
import time
import logging
import ast

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

# Configuration
TEST_FILE = "e2e_fibonacci.py"
LOG_FILE = "e2e_test.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger("E2E")


class E2EValidator:
    """Validates test results."""

    @staticmethod
    def validate_python_file(path: str) -> bool:
        """Check if file exists and has valid syntax."""
        if not os.path.exists(path):
            logger.error(f"❌ File {path} does not exist.")
            return False

        try:
            content = open(path).read()
            ast.parse(content)
            logger.info(f"✅ File {path} has valid Python syntax.")
            return True
        except SyntaxError as e:
            logger.error(f"❌ File {path} has invalid syntax: {e}")
            return False


class ScenarioRunner:
    def __init__(self):
        # Import inside method to avoid import errors if env not ready
        from vertice_tui.core.bridge import Bridge

        print("⚡ Initializing Bridge (System Core)...")
        self.bridge = Bridge()
        self.results = {"passed": 0, "failed": 0}

    async def run_scenario(self, name: str, prompt: str, validation_fn=None):
        """Run a single chat scenario."""
        print(f"\n🧪 SCENARIO: {name}")
        print(f"   Prompt: {prompt[:80]}..." if len(prompt) > 80 else f"   Prompt: {prompt}")
        print("   " + "-" * 40)

        response_buffer = []
        start_time = time.time()

        try:
            # We enforce auto_route=True to test orchestration
            stream = self.bridge.chat(prompt, auto_route=True)

            async for chunk in stream:
                print(chunk, end="", flush=True)
                response_buffer.append(chunk)

            print("\n   " + "-" * 40)
            duration = time.time() - start_time
            print(f"   ⏱️  Duration: {duration:.2f}s")

            full_response = "".join(response_buffer)

            # Validation
            success = True
            if validation_fn:
                success = validation_fn(full_response)

            if success:
                print(f"   ✅ PASS: {name}")
                self.results["passed"] += 1
            else:
                print(f"   ❌ FAIL: {name}")
                self.results["failed"] += 1

        except Exception as e:
            print(f"\n   ❌ CRITICAL ERROR in {name}: {e}")
            import traceback

            traceback.print_exc()
            self.results["failed"] += 1

    def cleanup(self):
        """Cleanup test artifacts."""
        if os.path.exists(TEST_FILE):
            os.unlink(TEST_FILE)
            print(f"🧹 Cleaned up {TEST_FILE}")


async def main():
    print("🚀 STARTING VERTICE COMPREHENSIVE E2E AUDIT")
    print("===========================================")

    runner = ScenarioRunner()

    # --- SCENARIO 1: TOOL EXECUTION (CODE GENERATION) ---
    def validate_code_gen(response):
        return E2EValidator.validate_python_file(TEST_FILE)

    prompt_1 = (
        f"Create a Python script named '{TEST_FILE}' that calculates the "
        "Fibonacci sequence up to the 10th term. Print the result. "
        "Use the write_file tool."
    )

    await runner.run_scenario("Code Gen & File Write", prompt_1, validate_code_gen)

    # --- SCENARIO 2: ORCHESTRATION & READING ---
    def validate_read(response):
        # We expect the model to mention it read the file or to show the content
        return "def" in response or "fibonacci" in response.lower() or "import" in response

    prompt_2 = f"Read the file '{TEST_FILE}' and explain briefly what it does."

    await runner.run_scenario("Context Awareness & File Read", prompt_2, validate_read)

    # --- FINAL REPORT ---
    print("\n📊 E2E AUDIT REPORT")
    print("===================")
    print(f"Total Tests: {runner.results['passed'] + runner.results['failed']}")
    print(f"PASSED:      {runner.results['passed']}")
    print(f"FAILED:      {runner.results['failed']}")

    runner.cleanup()

    if runner.results["failed"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user.")
        sys.exit(130)
