"""Claude authentication and generation Pydantic models/schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from .schemas import AnalysisResult, PostStyle, Provider, RepositoryOwnership
from .openai_schemas import OpenAIModel


class ClaudeAuthRequest(BaseModel):
    """Request model for Claude API key authentication."""

    api_key: str = Field(
        ...,
        min_length=1,
        description="Anthropic Claude API key for authentication"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate API key is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty or whitespace")
        return v.strip()


class ClaudeAuthResponse(BaseModel):
    """Response model for Claude authentication status."""

    connected: bool = Field(
        ...,
        description="Whether the Claude API key is connected and valid"
    )
    masked_key: Optional[str] = Field(
        None,
        description="Masked API key showing only last 4 characters (e.g., '****abcd')"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if authentication failed"
    )


class ClaudeGenerateRequest(BaseModel):
    """Request model for AI-powered LinkedIn post generation."""

    analysis: AnalysisResult = Field(
        ...,
        description="Repository analysis result to generate content from"
    )
    style: PostStyle = Field(
        default=PostStyle.PROBLEM_SOLUTION,
        description="Post style template to use for generation"
    )
    provider: Provider = Field(
        default=Provider.CLAUDE,
        description="AI provider to use for generation (claude or openai)"
    )
    model: Optional[OpenAIModel] = Field(
        default=None,
        description="OpenAI model to use when provider is 'openai'. Ignored for Claude."
    )
    ownership: RepositoryOwnership = Field(
        default=RepositoryOwnership.OWN,
        description="Whether this is your own project or one you discovered"
    )


class ClaudeGenerateResponse(BaseModel):
    """Response model for AI-generated content."""

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
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying (for rate limit errors)"
    )
