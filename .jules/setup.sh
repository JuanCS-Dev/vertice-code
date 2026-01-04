#!/bin/bash
# Jules Environment Setup Script
# This script runs in Jules VM before task execution

set -e

echo "=== Vertice-Code Environment Setup ==="

# Install project in dev mode
pip install -e ".[dev]" --quiet

# Verify installation
python -c "import vertice_cli; print(f'vertice_cli loaded: {vertice_cli.__file__}')"

# Install pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    pre-commit install --install-hooks || true
fi

echo "=== Environment ready ==="
