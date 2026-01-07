"""
Chat API router placeholder
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/")
async def chat_root() -> Dict[str, str]:
    """Chat API root endpoint"""
    return {"message": "Chat API"}
