"""Gemini authentication Pydantic models/schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class GeminiAuthRequest(BaseModel):
    """Request model for Gemini API key authentication."""

    api_key: str = Field(
        ...,
        min_length=1,
        description="Google Gemini API key for authentication"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate API key is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty or whitespace")
        return v.strip()


class GeminiAuthResponse(BaseModel):
    """Response model for Gemini authentication status."""

    connected: bool = Field(
        ...,
        description="Whether the Gemini API key is connected and valid"
    )
    masked_key: Optional[str] = Field(
        None,
        description="Masked API key showing only last 4 characters (e.g., '****abcd')"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if authentication failed"
    )
