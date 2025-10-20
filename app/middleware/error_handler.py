"""
Error handling middleware
Based on the C# ErrorHandlerMiddleware
"""

import logging
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.custom_exceptions import RentMeException, to_http_exception

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """Global error handling middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        try:
            await self.app(scope, receive, send)
        except RentMeException as exc:
            logger.error(f"RentMeException: {exc.message}")
            response = JSONResponse(
                status_code=exc.status_code,
                content={
                    "status_code": exc.status_code,
                    "status_message": exc.message,
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "data": None
                }
            )
            await response(scope, receive, send)
        except RequestValidationError as exc:
            logger.error(f"Validation error: {exc}")
            response = JSONResponse(
                status_code=422,
                content={
                    "status_code": 422,
                    "status_message": "Validation error",
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "data": None,
                    "errors": exc.errors()
                }
            )
            await response(scope, receive, send)
        except StarletteHTTPException as exc:
            logger.error(f"HTTPException: {exc.detail}")
            response = JSONResponse(
                status_code=exc.status_code,
                content={
                    "status_code": exc.status_code,
                    "status_message": exc.detail,
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "data": None
                }
            )
            await response(scope, receive, send)
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={
                    "status_code": 500,
                    "status_message": "Internal server error",
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "data": None
                }
            )
            await response(scope, receive, send)
