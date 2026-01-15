#!/usr/bin/env python
"""
TUI Import Audit Script.

Scans all Python files in the TUI and checks for import errors.
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

# Add project directories to path
PROJECT_ROOT = Path("/media/juan/DATA/Vertice-Code")
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

TUI_DIR = SRC_DIR / "vertice_tui"


def get_imports_from_file(filepath: Path) -> List[str]:
    """Extract all import statements from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"PARSE_ERROR: {e}"]
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def check_import(module_name: str) -> Tuple[bool, str]:
    """Check if a module can be imported."""
    try:
        # Skip relative imports and standard library
        if module_name.startswith('.'):
            return True, "relative"
        
        # Try to find the module
        spec = importlib.util.find_spec(module_name.split('.')[0])
        if spec is not None:
            return True, "found"
        else:
            return False, "not found"
    except (ModuleNotFoundError, ImportError, ValueError) as e:
        return False, str(e)


def audit_tui_imports():
    """Audit all imports in the TUI directory."""
    print("=" * 70)
    print("TUI IMPORT AUDIT")
    print("=" * 70)
    print()
    
    all_imports: Dict[str, List[str]] = {}
    failed_imports: Dict[str, List[Tuple[str, str]]] = {}
    
    # Find all Python files
    python_files = list(TUI_DIR.rglob("*.py"))
    print(f"Found {len(python_files)} Python files in {TUI_DIR}")
    print()
    
    for filepath in python_files:
        relative_path = filepath.relative_to(TUI_DIR)
        imports = get_imports_from_file(filepath)
        
        if imports and imports[0].startswith("PARSE_ERROR"):
            print(f"❌ PARSE ERROR: {relative_path}")
            print(f"   {imports[0]}")
            continue
        
        all_imports[str(relative_path)] = imports
        
        for imp in imports:
            success, reason = check_import(imp)
            if not success:
                if str(relative_path) not in failed_imports:
                    failed_imports[str(relative_path)] = []
                failed_imports[str(relative_path)].append((imp, reason))
    
    # Report
    print("-" * 70)
    print("IMPORT FAILURES")
    print("-" * 70)
    
    if not failed_imports:
        print("✅ No import failures detected!")
    else:
        for filepath, failures in sorted(failed_imports.items()):
            print(f"\n📁 {filepath}")
            for module, reason in failures:
                print(f"   ❌ {module}")
                if "not found" not in reason.lower():
                    print(f"      └─ {reason[:80]}")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files scanned: {len(python_files)}")
    print(f"Files with import issues: {len(failed_imports)}")
    
    # Unique problematic modules
    all_failed = set()
    for failures in failed_imports.values():
        for module, _ in failures:
            all_failed.add(module.split('.')[0])
    
    if all_failed:
        print(f"\nProblematic top-level modules: {', '.join(sorted(all_failed))}")
    
    return failed_imports


if __name__ == "__main__":
    failed = audit_tui_imports()
    sys.exit(1 if failed else 0)
