"""
Command Handlers module for JuanCS Dev-Code.

Provides the CommandRouter for dispatching slash commands.

Phase 5.2: Added BaseHandler for reducing duplication.
"""

from .router import CommandRouter
from .base import BaseHandler

__all__ = ["CommandRouter", "BaseHandler"]
