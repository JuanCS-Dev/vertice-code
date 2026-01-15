
import subprocess
import time
import re
import argparse
import sys

def run_benchmark(scenario="complex_feature", iterations=3):
    print(f"🧪 Starting Prompt Optimization Benchmark for '{scenario}'")
    print(f"   Iterations: {iterations}")
    print("-" * 50)
    
    successes = 0
    total_time = 0
    
    for i in range(iterations):
        start = time.time()
        # Run measure_quality.py in a subprocess to isolate state
        # Note: We need --real to actually test the prompt's effect on the LLM
        # But if no API key, we might fail.
        # This script assumes a working environment.
        
        cmd = [sys.executable, "scripts/e2e/measure_quality.py", "--real", "--scenario", scenario]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            duration = time.time() - start
            total_time += duration
            
            output = result.stdout
            
            # Check for success
            if "✅ SCENARIO PASSED" in output:
                successes += 1
                status = "PASS"
            else:
                status = "FAIL"
                
            print(f"Run {i+1}: {status} ({duration:.1f}s)")
            
            # Extract token usage if available (requires bridge support to print it)
            # Future improvement.
            
        except subprocess.TimeoutExpired:
            print(f"Run {i+1}: TIMEOUT")
            
    print("-" * 50)
    print(f"🏆 Results: {successes}/{iterations} Succeeded")
    print(f"⏱️ Avg Time: {total_time/iterations:.1f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="complex_feature")
    parser.add_argument("--iter", type=int, default=3)
    args = parser.parse_args()
    
    run_benchmark(args.scenario, args.iter)
