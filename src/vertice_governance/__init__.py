"""
vertice_governance: Constitutional AI & Wisdom Framework.

This package contains governance systems for AI safety:
    - justica: Constitutional governance and violation prevention
    - sofia: Wise counselor based on Early Christianity virtues

Both frameworks are pure Python stdlib with zero external dependencies.

Usage:
    from vertice_governance import JusticaAgent, SofiaAgent
    from vertice_governance.justica import ConstitutionValidator
    from vertice_governance.sofia import WisdomEngine
"""

from .justica import JusticaAgent
from .sofia import SofiaAgent

__all__ = ['JusticaAgent', 'SofiaAgent', 'justica', 'sofia']
__version__ = '1.0.0'
