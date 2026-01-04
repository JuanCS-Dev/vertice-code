#!/bin/bash
# Jules Environment Setup Script
# This script runs in Jules VM before task execution

# Don't exit on error - be resilient
set +e

echo "=== Vertice-Code Environment Setup ==="

# Install project in dev mode
echo "Installing project dependencies..."
pip install -e ".[dev]" --quiet 2>/dev/null || pip install -e ".[dev]"

# Install additional tools for validation
echo "Installing validation tools..."
pip install black ruff mypy --quiet 2>/dev/null || true

# Verify installation
echo "Verifying installation..."
python -c "import vertice_cli; print(f'vertice_cli: OK')" 2>/dev/null || echo "vertice_cli: WARN - import issues"
python -c "import vertice_tui; print(f'vertice_tui: OK')" 2>/dev/null || echo "vertice_tui: WARN - import issues"
python -c "import vertice_core; print(f'vertice_core: OK')" 2>/dev/null || echo "vertice_core: WARN - import issues"

# Verify tools
echo "Verifying tools..."
black --version 2>/dev/null || echo "black: NOT AVAILABLE"
ruff --version 2>/dev/null || echo "ruff: NOT AVAILABLE"

# Test validation script
echo "Testing validation script..."
python scripts/pre_release_validation.py --quick --no-report 2>/dev/null && echo "Validation script: OK" || echo "Validation script: WARN - has issues to fix"

echo "=== Environment ready (with warnings above if any) ==="
