"""Image generation API routes with input validation.

Provides endpoints for generating images for LinkedIn posts with comprehensive
input validation for security (OWASP A03 compliance).

Size limits:
- Post content: 10KB max (413 Payload Too Large)
- Custom prompt: 2KB max (413 Payload Too Large)

Dimension validation:
- Only allows: 1200x627, 1080x1080, 1200x1200 (400 Bad Request for others)

Prompt security:
- Malicious pattern detection and rejection (400 Bad Request)
"""

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from typing import Optional

from src.models.image_schemas import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageDimensions,
    ImageStyle,
    MAX_POST_CONTENT_SIZE,
    MAX_PROMPT_SIZE,
    VALID_DIMENSIONS,
)
from src.validators.prompt_validator import PromptValidator

# Create router for image generation endpoints
router = APIRouter(prefix="/generate", tags=["image-generation"])

# Global prompt validator instance
_prompt_validator = PromptValidator(strict_mode=True)


def get_prompt_validator() -> PromptValidator:
    """Get the prompt validator instance."""
    return _prompt_validator


@router.post("/image", response_model=ImageGenerationResponse)
async def generate_image(
    request: Request,
    image_request: ImageGenerationRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> ImageGenerationResponse:
    """Generate an image for a LinkedIn post.

    Validates all inputs before processing:
    - Post content size (max 10KB)
    - Custom prompt size (max 2KB)
    - Dimensions (must be valid LinkedIn dimensions)
    - Prompt safety (no malicious patterns)

    Args:
        request: The FastAPI request object.
        image_request: The image generation request with validated inputs.
        x_session_id: Session ID from header.

    Returns:
        ImageGenerationResponse with generated image or error.

    Raises:
        HTTPException: 400 for invalid inputs, 401 for auth issues.
    """
    session_id = x_session_id or "default"

    # Additional custom prompt validation for malicious patterns
    if image_request.custom_prompt:
        validator = get_prompt_validator()
        validation_result = validator.validate(image_request.custom_prompt)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=validation_result.error_message or "Invalid prompt"
            )

    # TODO: Implement actual image generation with Gemini client
    # For now, return a placeholder response indicating the request was validated
    return ImageGenerationResponse(
        success=False,
        error="Image generation service not yet implemented",
        dimensions=image_request.dimensions.value
    )


@router.post("/image/validate")
async def validate_image_request(
    request: Request,
    image_request: ImageGenerationRequest
) -> dict:
    """Validate an image generation request without generating.

    Useful for pre-flight validation of user inputs.

    Args:
        request: The FastAPI request object.
        image_request: The image generation request to validate.

    Returns:
        Validation result with details.

    Raises:
        HTTPException: 400 for invalid inputs.
    """
    validator = get_prompt_validator()
    result = {
        "valid": True,
        "post_content_size": len(image_request.post_content.encode("utf-8")),
        "dimensions": image_request.dimensions.value,
        "prompt_validation": None
    }

    # Validate custom prompt if provided
    if image_request.custom_prompt:
        prompt_result = validator.validate(image_request.custom_prompt)
        result["prompt_validation"] = {
            "valid": prompt_result.is_valid,
            "detected_patterns": prompt_result.detected_patterns,
            "error": prompt_result.error_message
        }
        if not prompt_result.is_valid:
            result["valid"] = False
            raise HTTPException(
                status_code=400,
                detail=prompt_result.error_message or "Invalid prompt"
            )

    return result


def validate_dimension_string(dimension: str) -> bool:
    """Validate a dimension string is in the allowed set.

    Args:
        dimension: Dimension string like "1200x627".

    Returns:
        True if valid, False otherwise.
    """
    return dimension in VALID_DIMENSIONS
