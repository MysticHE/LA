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
