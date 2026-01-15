#!/usr/bin/env python3
"""Check nesting depth - Pre-commit hook for TECH_DEBT_PLAN compliance.

Ensures code doesn't exceed 10 levels of nesting to maintain readability.

Part of Prevention Guardrails - Series A Tech Debt Plan.
"""
import ast
import sys
from pathlib import Path
from typing import Tuple

MAX_NESTING = 10


class NestingVisitor(ast.NodeVisitor):
    """AST visitor to calculate maximum nesting depth."""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        self.violations: list[Tuple[int, int]] = []  # (line, depth)

    def _enter_block(self, node):
        """Enter a nesting block."""
        self.current_depth += 1
        if self.current_depth > MAX_NESTING:
            self.violations.append((node.lineno, self.current_depth))
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_FunctionDef(self, node):
        self._enter_block(node)

    def visit_AsyncFunctionDef(self, node):
        self._enter_block(node)

    def visit_ClassDef(self, node):
        self._enter_block(node)

    def visit_If(self, node):
        self._enter_block(node)

    def visit_For(self, node):
        self._enter_block(node)

    def visit_AsyncFor(self, node):
        self._enter_block(node)

    def visit_While(self, node):
        self._enter_block(node)

    def visit_With(self, node):
        self._enter_block(node)

    def visit_AsyncWith(self, node):
        self._enter_block(node)

    def visit_Try(self, node):
        self._enter_block(node)

    def visit_Match(self, node):
        self._enter_block(node)


def check_nesting(filepath: str) -> bool:
    """Check if file nesting is under MAX_NESTING.

    Returns True if file passes, False if it has violations.
    """
    path = Path(filepath)

    # Skip non-Python files
    if path.suffix != ".py":
        return True

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=filepath)
        visitor = NestingVisitor()
        visitor.visit(tree)

        if visitor.violations:
            print(f"FAIL: {filepath} has excessive nesting:")
            for line, depth in visitor.violations[:3]:  # Show first 3
                print(f"  Line {line}: depth {depth} (max: {MAX_NESTING})")
            return False
        return True
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {filepath}:{e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"ERROR: Could not check {filepath}: {e}")
        return False


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Usage: check_nesting.py <file1> [file2] ...")
        sys.exit(1)

    failed = False
    for filepath in sys.argv[1:]:
        if not check_nesting(filepath):
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
