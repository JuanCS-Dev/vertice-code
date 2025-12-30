"""
Vertice Core - Agency Foundation

Central module for the Vertice multi-agent system.

Usage:
    from core import Agency, get_agency
    agency = get_agency()
"""

from .agency import Agency, AgencyConfig, get_agency

__all__ = [
    "Agency",
    "AgencyConfig",
    "get_agency",
]
