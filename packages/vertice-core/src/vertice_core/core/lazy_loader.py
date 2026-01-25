"""Intelligent lazy loading system."""

import asyncio
import importlib
from typing import Any, Dict


class LazyLoader:
    """Lazy module and component loader."""

    # Module cache
    _cache: Dict[str, Any] = {}

    # Import map - módulos que podem ser lazy loaded
    # Maps component name to module path
    _LAZY_MODULES = {
        "llm": "vertice_core.core.llm",  # Loads module, client accessed via property
        "tools": "vertice_core.plugins.tools_plugin",
        "tui": "vertice_core.plugins.tui_plugin",
        "intelligence": "vertice_core.plugins.intelligence_plugin",
        "devsquad": "vertice_core.plugins.devsquad_plugin",
        "mcp": "vertice_core.core.mcp_client",
    }

    async def load(self, component: str) -> Any:
        """Load component on-demand."""
        if component in self._cache:
            return self._cache[component]

        # Import assíncrono (run in executor para não bloquear)
        module_path = self._LAZY_MODULES.get(component)
        if not module_path:
            raise ValueError(f"Unknown component: {component}")

        loop = asyncio.get_event_loop()

        # Run import in thread pool to avoid blocking the event loop
        # This is critical for responsiveness during background loading
        try:
            module = await loop.run_in_executor(None, lambda: importlib.import_module(module_path))

            self._cache[component] = module
            return module
        except ImportError as e:
            print(f"\n\033[91mError loading component {component}: {e}\033[0m")
            raise
        except Exception as e:
            print(f"\n\033[91mUnexpected error loading {component}: {e}\033[0m")
            raise

    async def preload(self, *components):
        """Preload components in background."""
        # Create tasks for all components
        tasks = [self.load(c) for c in components]

        # Run concurrently, ignoring errors (they will be caught when accessed for real)
        await asyncio.gather(*tasks, return_exceptions=True)

    def is_loaded(self, component: str) -> bool:
        """Check if component is already loaded."""
        return component in self._cache
