"""
Base Generator Protocol - Interface for infrastructure generators.

All generators implement this protocol for consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict


class BaseGenerator(ABC):
    """Abstract base class for infrastructure generators."""

    @abstractmethod
    async def generate(self, task_request: str) -> Dict[str, Any]:
        """Generate infrastructure configuration.

        Args:
            task_request: User's request description

        Returns:
            Dict containing generated configuration and metadata
        """
        pass

    @abstractmethod
    async def generate_streaming(self, task_request: str) -> AsyncIterator[Dict[str, Any]]:
        """Generate infrastructure configuration with streaming output.

        Args:
            task_request: User's request description

        Yields:
            StreamingChunk dicts with progress updates and generated config
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Generator name for identification."""
        pass
