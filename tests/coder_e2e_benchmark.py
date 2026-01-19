import asyncio
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.getcwd())


async def run_coder_benchmark():
    """Run an E2E benchmark for the Coder agent via Agency."""
    print("=" * 60)
    print("🚀 VERTICE-CODE: AGENCY E2E BENCHMARK (CODER)")
    print("=" * 60)

    try:
        from core.agency import Agency

        # 1. Setup Agency
        agency = Agency()
        print("✅ Agency initialized.")

        # 2. Define Task
        test_file = "benchmark_fib.py"
        if os.path.exists(test_file):
            os.remove(test_file)

        task_request = (
            f"Create a high-quality Python module named '{test_file}' that implements "
            "the Fibonacci sequence calculation using recursion with memoization. "
            "Requirements: use type hints, include a comprehensive docstring, "
            "and add a main block that demonstrates usage for N=10 and N=50. "
            "IMPORTANT: Use the write_file tool to actually save the file to disk."
        )

        print(f"\n📝 Request: {task_request[:100]}...")

        # 3. Execute via Agency
        print("\n🧠 Executing Agency Pipeline...")
        start_time = time.time()

        # We use stream to see progress if possible, but execute is fine
        async for chunk in agency.execute(task_request, stream=True):
            if isinstance(chunk, str):
                # Print without newline if it looks like a stream
                print(chunk, end="", flush=True)
            else:
                # Meta info or structured data
                pass

        duration = time.time() - start_time
        print(f"\n\n⏱️ Duration: {duration:.2f}s")

        # 4. Analyze results
        print("\n📊 ANALYSIS:")

        # Check if file was created
        if os.path.exists(test_file):
            print(f"✅ File Created: {test_file}")
            content = Path(test_file).read_text()

            # Syntax check
            import ast

            try:
                ast.parse(content)
                print("✅ Syntax: Valid Python")
            except SyntaxError as e:
                print(f"❌ Syntax: FAILED ({e})")

            # Logic check
            checks = {
                "Memoization": "memo" in content.lower(),
                "Type Hints": "int" in content and "->" in content,
                "Docstring": '"""' in content or "'''" in content,
                "Main Block": "__main__" in content,
            }

            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check}")

            # Quality score simulation
            score = sum(checks.values()) / len(checks) * 10
            print(f"\n🏆 Quality Score: {score:.1f}/10")

            # Print code preview
            print("\n📝 Code Preview (first 15 lines):")
            lines = content.splitlines()[:15]
            print("\n".join(lines))

        else:
            print("❌ File NOT Created.")
            print(
                "\nDiagnóstico: O agente pode ter apenas gerado o código em texto mas não invocado a tool."
            )

        # Cleanup
        if os.path.exists(test_file):
            # os.remove(test_file) # Leave it for the user to see if they want
            pass

    except Exception as e:
        print(f"\n💥 CRITICAL FAILURE: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_coder_benchmark())
