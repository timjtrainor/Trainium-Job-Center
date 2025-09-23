"""Custom exceptions for the LinkedIn recommended jobs crew service."""
from __future__ import annotations

from typing import Any, Dict, Optional


class LinkedInRecommendedJobsError(RuntimeError):
    """Base error for LinkedIn recommended jobs failures."""

    def __init__(self, message: str, *, request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id
        self.details = details or {}


class MCPConnectionError(LinkedInRecommendedJobsError):
    """Raised when the MCP gateway cannot be reached."""


class ToolExecutionError(LinkedInRecommendedJobsError):
    """Raised when underlying MCP tools fail to return data."""


class CrewExecutionError(LinkedInRecommendedJobsError):
    """Raised when CrewAI orchestration fails to complete."""


__all__ = [
    "LinkedInRecommendedJobsError",
    "MCPConnectionError",
    "ToolExecutionError",
    "CrewExecutionError",
]
