"""
Debug Fix Scenario
Target: Fix a script that hangs forever (infinite loop).
"""

SETUP_FILES = {
    "broken_loop.py": """
import time

def count_to_five():
    i = 0
    while i < 5:
        print(i)
        # Forgot to increment i!
        time.sleep(0.1)

if __name__ == "__main__":
    count_to_five()
"""
}

PROMPT = """
The file 'broken_loop.py' hangs forever. Please fix the bug.
Do not delete the file, just modify it to work correctly.
"""

EXPECTED_FILES = ["broken_loop.py"]


def check_fix():
    # Runtime verification: Run the script with a timeout.
    # If it finishes in <1s, it's fixed. If it timeouts, it's still broken.
    import subprocess
    import sys

    try:
        # Run subprocess with timeout
        subprocess.run(
            [sys.executable, "broken_loop.py"], timeout=2, check=True, capture_output=True
        )
        return True
    except subprocess.TimeoutExpired:
        return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


VALIDATION_RULES = [lambda: check_fix()]
