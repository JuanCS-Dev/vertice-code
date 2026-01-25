"""Helper to create default registry instance."""

from vertice_core.tools.base import ToolRegistry
from vertice_core.tools.catalog import get_catalog


def get_default_registry() -> ToolRegistry:
    """Create and populate default tool registry via ToolCatalog."""
    # CLI default: Defaults + Prometheus (auto-init)
    return get_catalog(include_web=False, include_parity=False, include_prometheus=True)
