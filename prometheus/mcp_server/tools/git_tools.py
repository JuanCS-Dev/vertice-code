"""
Git Tools for MCP Server
Git workflow toolkit with modular design

This module imports and re-exports git tools from specialized modules
to maintain backwards compatibility while enforcing modular design.

Git operations are split across specialized modules:
- git_safety.py: Safety validation and utilities
- git_status_tools.py: Status, diff, and log operations
- git_advanced_tools.py: Commit, branch, and merge operations
"""

# Import from specialized modules to maintain functionality
# This module now serves as a compatibility layer

# Import safety utilities
from . import git_safety  # noqa: F401

# Import status tools
from . import git_status_tools  # noqa: F401

# Import advanced tools
from . import git_advanced_tools  # noqa: F401

# Re-export for backwards compatibility (if needed)
# No direct implementations in this module
