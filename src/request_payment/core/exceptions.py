"""Exception handling for RequestPayment system."""

from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback


class RequestPaymentException(Exception):
    """Base exception for RequestPayment system."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(RequestPaymentException):
    """Raised when validation fails."""
    pass





async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions.
    
    Args:
        request: The incoming request.
        exc: The HTTP exception.
        
    Returns:
        JSONResponse: The error response.
    """
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            }
        }
    )


def serialize_validation_errors(errors):
    """安全地序列化驗證錯誤"""
    serialized_errors = []
    for error in errors:
        serialized_error = {}
        for key, value in error.items():
            if key == "ctx" and isinstance(value, dict):
                # 處理 ctx 中的所有不可序列化對象
                serialized_ctx = {}
                for ctx_key, ctx_value in value.items():
                    try:
                        # 嘗試JSON序列化，如果失敗則轉為字符串
                        import json
                        json.dumps(ctx_value)
                        serialized_ctx[ctx_key] = ctx_value
                    except (TypeError, ValueError):
                        serialized_ctx[ctx_key] = str(ctx_value)
                serialized_error[key] = serialized_ctx
            elif key == "input":
                # 確保input也可以序列化
                try:
                    import json
                    json.dumps(value)
                    serialized_error[key] = value
                except (TypeError, ValueError):
                    serialized_error[key] = str(value)
            else:
                # 處理其他可能的不可序列化值
                try:
                    import json
                    json.dumps(value)
                    serialized_error[key] = value
                except (TypeError, ValueError):
                    serialized_error[key] = str(value)
        serialized_errors.append(serialized_error)
    return serialized_errors

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions.
    
    Args:
        request: The incoming request.
        exc: The validation exception.
        
    Returns:
        JSONResponse: The error response.
    """
    logger.error(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation failed",
                "type": "validation_error",
                "details": serialize_validation_errors(exc.errors())
            }
        }
    )


async def request_payment_exception_handler(request: Request, exc: RequestPaymentException) -> JSONResponse:
    """Handle RequestPayment exceptions.
    
    Args:
        request: The incoming request.
        exc: The RequestPayment exception.
        
    Returns:
        JSONResponse: The error response.
    """
    logger.error(f"RequestPayment exception: {exc.__class__.__name__} - {exc.message}")
    
    # Map exception types to HTTP status codes
    status_map = {
        ValidationException: status.HTTP_400_BAD_REQUEST,
    }
    
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": exc.message,
                "type": exc.__class__.__name__.lower(),
                "details": exc.details
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.
    
    Args:
        request: The incoming request.
        exc: The exception.
        
    Returns:
        JSONResponse: The error response.
    """
    logger.error(f"Unhandled exception: {exc.__class__.__name__} - {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the application.
    
    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RequestPaymentException, request_payment_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 