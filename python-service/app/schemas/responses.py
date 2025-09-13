"""Standard API response schemas and utilities."""
from typing import Any, Dict, Optional
import json
from pydantic import BaseModel
from enum import Enum


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class StandardResponse(BaseModel):
    """Standard API response format."""
    status: ResponseStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    
    class Config:
        use_enum_values = True


class HealthStatus(BaseModel):
    """Health check response model."""
    service: str
    version: str
    status: str
    timestamp: str
    dependencies: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Error detail model for enhanced error reporting."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


def _stringify(value: Any) -> Optional[str]:
    """Convert non-string values to JSON strings when possible."""
    if value is None or isinstance(value, str):
        return value
    try:
        return json.dumps(value)
    except TypeError:
        return str(value)


def create_success_response(
    data: Any = None,
    message: Optional[str] = None
) -> StandardResponse:
    """Create a standard success response."""
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        message=message
    )


def create_error_response(
    error: Any,
    data: Optional[Any] = None,
    message: Optional[Any] = None
) -> StandardResponse:
    """Create a standard error response."""
    return StandardResponse(
        status=ResponseStatus.ERROR,
        error=_stringify(error),
        data=data,
        message=_stringify(message)
    )


def create_warning_response(
    message: str,
    data: Optional[Any] = None
) -> StandardResponse:
    """Create a standard warning response."""
    return StandardResponse(
        status=ResponseStatus.WARNING,
        data=data,
        message=message
    )