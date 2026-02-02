"""Pydantic models for LinkedIn post repurposing feature."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class LinkedInContentRequest(BaseModel):
    """Request model for analyzing LinkedIn post content."""
    content: str = Field(..., description="Pasted LinkedIn post text", min_length=10, max_length=10000)


class ContentAnalysisResult(BaseModel):
    """Result of analyzing LinkedIn post content."""
    original_content: str
    cleaned_content: str
    themes: list[str] = Field(default_factory=list, description="Main topics discussed (max 5)")
    tone: str = Field(description="One of: professional, casual, motivational, technical, humorous")
    content_type: str = Field(description="One of: story, tips, announcement, opinion, case-study")
    key_points: list[str] = Field(default_factory=list, description="Core messages/takeaways (max 5)")
    entities: list[str] = Field(default_factory=list, description="People, companies, technologies mentioned")
    hashtags: list[str] = Field(default_factory=list, description="Extracted hashtags from original")


class LinkedInAnalyzeResponse(BaseModel):
    """Response model for LinkedIn content analysis."""
    success: bool
    data: Optional[ContentAnalysisResult] = None
    error: Optional[str] = None


# Repurpose style options
RepurposeStyle = Literal["same", "professional", "casual", "storytelling"]
RepurposeFormat = Literal["expanded", "condensed", "thread"]


class RepurposeRequest(BaseModel):
    """Request model for repurposing LinkedIn content."""
    original_content: str = Field(..., description="Original LinkedIn post content")
    analysis: ContentAnalysisResult = Field(..., description="Content analysis result")
    target_style: RepurposeStyle = Field(default="same", description="Target tone/style")
    target_format: RepurposeFormat = Field(default="expanded", description="Output format")


class ImageContext(BaseModel):
    """Context for image generation from repurposed content."""
    content_type: str
    headline: str
    subtitle: Optional[str] = None
    recommended_styles: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)


class RepurposeResponse(BaseModel):
    """Response model for repurposed content."""
    success: bool
    repurposed_content: Optional[str] = None
    suggested_hashtags: list[str] = Field(default_factory=list)
    image_context: Optional[ImageContext] = None
    error: Optional[str] = None
    retry_after: Optional[int] = None
