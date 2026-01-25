"""
Vertice Core - Backward Compatibility Layer

Re-exports everything from vertice_core for backward compatibility.
This module is deprecated; import from vertice_core directly.

Usage:
    from core import Agency, get_agency  # Still works, but deprecated
    # Preferred: from vertice_core import Agency, get_agency
"""

# Re-export everything from vertice_core
from vertice_core import *

# Additional imports for backward compatibility
