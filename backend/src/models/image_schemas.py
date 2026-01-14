"""Schemas for image generation and content analysis."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Sentiment(str, Enum):
    """Sentiment classification for content."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    INSPIRATIONAL = "inspirational"
    INFORMATIVE = "informative"


class ContentType(str, Enum):
    """LinkedIn content type classification."""
    TUTORIAL = "tutorial"
    ANNOUNCEMENT = "announcement"
    TIPS = "tips"
    STORY = "story"
    TECHNICAL = "technical"
    CAREER = "career"


class ClassificationResult(BaseModel):
    """Result of content type classification."""

    content_type: ContentType = Field(
        description="The classified content type"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the classification (0.0 to 1.0)"
    )


class ContentAnalysis(BaseModel):
    """Result of analyzing LinkedIn post content."""

    themes: list[str] = Field(
        default_factory=list,
        description="Main themes extracted from the content"
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies mentioned in the content"
    )
    sentiment: Sentiment = Field(
        default=Sentiment.NEUTRAL,
        description="Overall sentiment of the content"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms for image generation"
    )
    suggested_visual_elements: list[str] = Field(
        default_factory=list,
        description="Visual elements that could represent the content"
    )
