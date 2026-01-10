"""
Enterprise Pilot Management Package
===================================

Comprehensive management system for enterprise pilot programs.

This package provides:
- Strategic customer selection and qualification
- Pilot program lifecycle management
- Success manager assignment and tracking
- Onboarding workflow automation
- Progress monitoring and reporting

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

__version__ = "1.0.0"

from .pilot_selector import (
    PilotCustomerSelector,
    PilotProgramManager,
    PilotProgram,
    PilotCustomerProfile,
    SuccessManager,
    PilotSelectionCriteria,
    PilotStatus,
    CustomerTier,
    IndustrySector,
    ContactInfo,
)

__all__ = [
    "PilotCustomerSelector",
    "PilotProgramManager",
    "PilotProgram",
    "PilotCustomerProfile",
    "SuccessManager",
    "PilotSelectionCriteria",
    "PilotStatus",
    "CustomerTier",
    "IndustrySector",
    "ContactInfo",
]
