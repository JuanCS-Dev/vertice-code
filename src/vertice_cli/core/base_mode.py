"""Base mode classes for different operational modes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging


@dataclass
class ModeContext:
    """Context for mode operations."""

    cwd: str
    env: Dict[str, str]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseMode(ABC):
    """Base class for operational modes."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active = False

    @abstractmethod
    async def activate(self, context: Optional[ModeContext] = None) -> bool:
        """Activate the mode."""
        pass

    @abstractmethod
    async def deactivate(self) -> bool:
        """Deactivate the mode."""
        pass

    @abstractmethod
    async def process_action(self, action: Dict[str, Any], context: ModeContext) -> Dict[str, Any]:
        """Process an action within this mode."""
        pass
