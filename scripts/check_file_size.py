#!/usr/bin/env python3
"""Check file size - Pre-commit hook for TECH_DEBT_PLAN compliance.

Ensures Python files stay under 1000 lines to maintain maintainability.

Part of Prevention Guardrails - Series A Tech Debt Plan.
"""
import sys
from pathlib import Path

MAX_LINES = 1000

# Files that are allowed to exceed the limit (legacy, with justification)
EXCEPTIONS = {
    "vertice_cli/shell_main.py",  # Core shell - refactor in progress
    "vertice_tui/app.py",  # TUI main - complex state management
}


def check_file_size(filepath: str) -> bool:
    """Check if file is under MAX_LINES.

    Returns True if file passes, False if it exceeds limit.
    """
    path = Path(filepath)

    # Skip non-Python files
    if path.suffix != ".py":
        return True

    # Skip exceptions
    rel_path = str(path)
    for exc in EXCEPTIONS:
        if rel_path.endswith(exc):
            return True

    try:
        with open(path, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        if line_count > MAX_LINES:
            print(f"FAIL: {filepath} has {line_count} lines (max: {MAX_LINES})")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Could not check {filepath}: {e}")
        return False


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Usage: check_file_size.py <file1> [file2] ...")
        sys.exit(1)

    failed = False
    for filepath in sys.argv[1:]:
        if not check_file_size(filepath):
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
