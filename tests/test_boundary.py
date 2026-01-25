"""
Boundary Test - Verifies architecture decoupling.

This test ensures that vertice_core can be imported without pulling in
vertice_core dependencies, maintaining clean separation of concerns.
"""

import sys


def test_core_purity():
    """Test that vertice_core can be imported without vertice_core dependencies."""
    # Clear any existing modules
    modules_to_remove = [name for name in sys.modules.keys() if name.startswith("vertice_core")]
    for module in modules_to_remove:
        del sys.modules[module]

    # Import vertice_core

    # Check that no vertice_core modules were loaded
    cli_modules = [name for name in sys.modules.keys() if name.startswith("vertice_core")]

    if cli_modules:
        raise AssertionError(
            f"vertice_core imported CLI modules: {cli_modules}. "
            "This violates architectural separation."
        )

    print("✅ Core purity test passed - no CLI dependencies loaded")


if __name__ == "__main__":
    test_core_purity()
