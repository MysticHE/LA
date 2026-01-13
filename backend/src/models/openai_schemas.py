"""OpenAI authentication and generation Pydantic models/schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
from .schemas import AnalysisResult, PostStyle


class OpenAIModel(str, Enum):
    """Available OpenAI models for content generation."""
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"


class OpenAIAuthRequest(BaseModel):
    """Request model for OpenAI API key authentication."""

    api_key: str = Field(
        ...,
        min_length=1,
        description="OpenAI API key for authentication (starts with 'sk-')"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate API key format and strip whitespace."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty or whitespace")
        v = v.strip()
        # OpenAI keys start with 'sk-' and have reasonable length
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        if len(v) < 40 or len(v) > 200:
            raise ValueError("OpenAI API key must be between 40 and 200 characters")
        return v


class OpenAIAuthResponse(BaseModel):
    """Response model for OpenAI authentication status."""

    connected: bool = Field(
        ...,
        description="Whether the OpenAI API key is connected and valid"
    )
    masked_key: Optional[str] = Field(
        None,
        description="Masked API key showing only last 4 characters (e.g., 'sk-...abcd')"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if authentication failed"
    )


class OpenAIGenerateRequest(BaseModel):
    """Request model for OpenAI-powered LinkedIn post generation."""

    analysis: AnalysisResult = Field(
        ...,
        description="Repository analysis result to generate content from"
    )
    style: PostStyle = Field(
        default=PostStyle.PROBLEM_SOLUTION,
        description="Post style template to use for generation"
    )
    model: OpenAIModel = Field(
        default=OpenAIModel.GPT_4O,
        description="OpenAI model to use for generation"
    )


class OpenAIGenerateResponse(BaseModel):
    """Response model for OpenAI-generated content."""

    success: bool = Field(
        ...,
        description="Whether content generation was successful"
    )
    content: Optional[str] = Field(
        None,
        description="Generated LinkedIn post content"
    )
    style: Optional[PostStyle] = Field(
        None,
        description="Post style that was used for generation"
    )
    model: Optional[OpenAIModel] = Field(
        None,
        description="OpenAI model that was used for generation"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying (for rate limit errors)"
    )
