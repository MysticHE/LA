"""Schemas for image generation and content analysis."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


# Size limits in bytes
MAX_POST_CONTENT_SIZE = 10 * 1024  # 10KB
MAX_PROMPT_SIZE = 2 * 1024  # 2KB


class ImageModel(str, Enum):
    """Available image generation models."""
    NANO_BANANA_PRO = "gemini-3-pro-image"  # Nano Banana Pro (default)
    IMAGEN_4_ULTRA = "imagen-4.0-ultra-generate-001"  # Imagen 4 Ultra
    IMAGEN_4_STANDARD = "imagen-4.0-generate-001"  # Imagen 4 Standard
    IMAGEN_4_FAST = "imagen-4.0-fast-generate-001"  # Imagen 4 Fast
    NANO_BANANA = "gemini-2.5-flash-image"  # Nano Banana


class ImageStyle(str, Enum):
    """Available image styles for LinkedIn post images."""
    INFOGRAPHIC = "infographic"
    MINIMALIST = "minimalist"
    CONCEPTUAL = "conceptual"
    ABSTRACT = "abstract"
    PHOTOREALISTIC = "photorealistic"
    ILLUSTRATED = "illustrated"
    DIAGRAM = "diagram"
    GRADIENT = "gradient"
    FLAT_DESIGN = "flat_design"
    ISOMETRIC = "isometric"
    TECH_THEMED = "tech_themed"
    PROFESSIONAL = "professional"


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


class StyleRecommendation(BaseModel):
    """Recommended image styles for a content type."""

    styles: list[str] = Field(
        min_length=3,
        description="Ordered list of recommended image styles (best first)"
    )
    content_type: ContentType = Field(
        description="The content type these styles are recommended for"
    )
    tech_influenced: bool = Field(
        default=False,
        description="Whether recommendations were influenced by technology stack"
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


class ImageDimensions(str, Enum):
    """LinkedIn-optimized image dimensions."""
    LINK_POST = "1200x627"  # Standard link post
    SQUARE = "1080x1080"  # Square format
    LARGE_SQUARE = "1200x1200"  # Large square format


# Valid dimension strings for quick validation
VALID_DIMENSIONS = {d.value for d in ImageDimensions}


class ImageGenerationRequest(BaseModel):
    """Request model for image generation with validated inputs."""

    post_content: str = Field(
        ...,
        min_length=1,
        description="LinkedIn post content to generate an image for"
    )
    custom_prompt: Optional[str] = Field(
        None,
        description="Optional custom prompt for image generation"
    )
    dimensions: ImageDimensions = Field(
        default=ImageDimensions.LINK_POST,
        description="Image dimensions (1200x627, 1080x1080, or 1200x1200)"
    )
    style: Optional[ImageStyle] = Field(
        None,
        description="Optional image style override"
    )
    model: ImageModel = Field(
        default=ImageModel.NANO_BANANA_PRO,
        description="Image generation model to use"
    )

    @field_validator("post_content")
    @classmethod
    def validate_post_content_size(cls, v: str) -> str:
        """Validate post content does not exceed maximum size."""
        if not v or not v.strip():
            raise ValueError("Post content cannot be empty or whitespace")
        v = v.strip()
        # Check size in bytes (UTF-8 encoded)
        content_size = len(v.encode("utf-8"))
        if content_size > MAX_POST_CONTENT_SIZE:
            raise ValueError(
                f"Post content exceeds maximum size of {MAX_POST_CONTENT_SIZE // 1024}KB"
            )
        return v

    @field_validator("custom_prompt")
    @classmethod
    def validate_custom_prompt_size(cls, v: Optional[str]) -> Optional[str]:
        """Validate custom prompt does not exceed maximum size."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        # Check size in bytes (UTF-8 encoded)
        prompt_size = len(v.encode("utf-8"))
        if prompt_size > MAX_PROMPT_SIZE:
            raise ValueError(
                f"Custom prompt exceeds maximum size of {MAX_PROMPT_SIZE // 1024}KB"
            )
        return v


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""

    success: bool = Field(
        ...,
        description="Whether image generation was successful"
    )
    image_base64: Optional[str] = Field(
        None,
        description="Base64-encoded generated image"
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Detected content type of the post"
    )
    recommended_style: Optional[ImageStyle] = Field(
        None,
        description="Recommended image style based on content"
    )
    dimensions: Optional[str] = Field(
        None,
        description="Dimensions of the generated image"
    )
    prompt_used: Optional[str] = Field(
        None,
        description="The prompt that was used for image generation"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying (for rate limit errors)"
    )
