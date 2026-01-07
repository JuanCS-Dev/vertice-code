"""
Application Exceptions
"""

from fastapi import HTTPException


class AppException(HTTPException):
    """Base application exception"""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
