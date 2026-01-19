import asyncio
import time
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from vertice_tui.core.history_manager import HistoryManager  # noqa: E402


async def measure_history_io_latency():
    print("\n🔬 DIAGNOSTIC: HistoryManager I/O Blocking Analysis")
    print("==================================================")

    # Setup temp file to simulate history
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        history_path = Path(tmp.name)

    # Pre-fill history to simulate real usage
    logger_history = HistoryManager(history_file=history_path, max_commands=1000)
    for i in range(1000):
        logger_history.commands.append(f"command_{i} --flag value")
    logger_history._save_history()

    manager = HistoryManager(history_file=history_path)

    # Measure blocking time of add_command
    # usage: on_input_submitted calls add_command -> _save_history (sync)

    print(f"Stats: {len(manager.commands)} commands in history.")

    bloat_sizes = [100, 500, 1000, 5000]

    for size in bloat_sizes:
        # Bloat history
        manager.commands = [f"cmd_{i}" * 5 for i in range(size)]
        manager.max_commands = size

        start_time = time.perf_counter()

        # CRITICAL SECTION: This runs on Main Thread in app.py
        manager.add_command(f"new_command_{time.time()}")

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        status = "❌ BLOCKING" if duration_ms > 16.0 else "✅ SAFE"
        if duration_ms < 1.0:
            status = "⚡ INSTANT"

        print(f"History Size {size:4d}: {duration_ms:8.4f} ms | {status}")

    history_path.unlink()


async def simulate_import_latency():
    print("\n🔬 DIAGNOSTIC: Lazy Import Overhead (Router)")
    print("===========================================")

    # We can't easily un-import modules, but we can measure the 'import' statement overhead
    # of a heavy module if we haven't imported it yet.
    # Since we are in the same process, we'll simulate a heavy synchronous operation
    # mimicking a large import or initialization (e.g. 50ms).

    start = time.perf_counter()
    # Simulate Router lazy loading a heavy handler
    time.sleep(0.05)
    end = time.perf_counter()

    print(f"Simulated Lazy Load: {(end - start)*1000:.4f} ms (Synchronous Freeze)")


if __name__ == "__main__":
    asyncio.run(measure_history_io_latency())
    # asyncio.run(simulate_import_latency())
