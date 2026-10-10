"""Standardized error schemas for API responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Consistent error payload across all endpoints."""
    detail: str = Field(..., description="Human-readable error explanation")
    error_code: str = Field(..., description="Machine-readable error categorization")
    suggestions: Optional[List[str]] = Field(default=None, description="Suggested remedy or recovery steps")
