"""
Custom exceptions for the RentMe API
Based on the C# exception classes
"""

from fastapi import HTTPException
from typing import Optional


class RentMeException(Exception):
    """Base exception for RentMe API"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ApiException(RentMeException):
    """General API exception"""
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        super().__init__(message, status_code)


class ValidationException(RentMeException):
    """Validation exception"""
    def __init__(self, message: str = "Validation error", status_code: int = 400):
        super().__init__(message, status_code)


class ValidationRequiredParameter(ValidationException):
    """Required parameter validation exception"""
    def __init__(self, parameter_name: str):
        message = f"Required parameter '{parameter_name}' is missing or invalid"
        super().__init__(message, 400)


class UnauthorizedException(RentMeException):
    """Unauthorized access exception"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, 401)


class ForbiddenException(RentMeException):
    """Forbidden access exception"""
    def __init__(self, message: str = "Forbidden access"):
        super().__init__(message, 403)


class NotFoundException(RentMeException):
    """Resource not found exception"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class InternalServerException(RentMeException):
    """Internal server error exception"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)


# Convert to FastAPI HTTPException
def to_http_exception(exc: RentMeException) -> HTTPException:
    """Convert RentMeException to FastAPI HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message
    )
