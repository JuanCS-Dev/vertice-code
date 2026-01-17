"""
Artifacts API router placeholder
"""

from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/")
async def artifacts_root() -> Dict[str, str]:
    """Artifacts API root endpoint"""
    return {"message": "Artifacts API"}
