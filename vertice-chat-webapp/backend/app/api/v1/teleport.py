"""
Teleport API router placeholder
"""

from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/")
async def teleport_root() -> Dict[str, str]:
    """Teleport API root endpoint"""
    return {"message": "Teleport API"}
