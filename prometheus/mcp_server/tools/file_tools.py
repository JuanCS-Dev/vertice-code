"""
File Tools for MCP Server
File system operations toolkit with modular design

This module imports and re-exports file tools from specialized modules
to maintain backwards compatibility while enforcing modular design.

File operations are split across specialized modules:
- file_rw_tools.py: Basic read/write operations
- file_mgmt_tools.py: File management (delete, move, copy, etc.)
"""

# Import from specialized modules to maintain functionality
# This module now serves as a compatibility layer

# Import read/write tools
from . import file_rw_tools  # noqa: F401

# Import management tools
from . import file_mgmt_tools  # noqa: F401

# Import directory tools
from . import file_dir_tools  # noqa: F401

# Re-export for backwards compatibility (if needed)
# No direct implementations in this module
