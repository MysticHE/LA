"""Image generation API routes with input validation and audit logging.

Provides endpoints for generating images for LinkedIn posts with comprehensive
input validation for security (OWASP A03 compliance).

Size limits:
- Post content: 10KB max (413 Payload Too Large)
- Custom prompt: 2KB max (413 Payload Too Large)

Dimension validation:
- Only allows: 1200x627, 1080x1080, 1200x1200 (400 Bad Request for others)

Prompt security:
- Malicious pattern detection and rejection (400 Bad Request)

Rate limiting:
- 20 requests per minute per session (applied via middleware)

Audit logging:
- All image generation requests are logged with metadata
- No sensitive data (API keys, prompt content) in audit logs
"""

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from typing import Optional

from src.models.image_schemas import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageDimensions,
    ImageStyle,
    ContentType,
    MAX_POST_CONTENT_SIZE,
    MAX_PROMPT_SIZE,
    VALID_DIMENSIONS,
)
from src.validators.prompt_validator import PromptValidator
from src.analyzers.content_analyzer import ContentAnalyzer
from src.analyzers.content_classifier import ContentClassifier
from src.generators.image_generator.style_recommender import StyleRecommender
from src.generators.image_generator.prompt_builder import get_prompt_builder
from src.services.gemini_client import GeminiClient, GeminiAPIError, RateLimitError
from src.services.audit_logger import get_audit_logger, AuditStatus
from src.api.gemini_routes import get_gemini_key_storage

# Create router for image generation endpoints
router = APIRouter(prefix="/generate", tags=["image-generation"])

# Global service instances
_prompt_validator = PromptValidator(strict_mode=True)
_content_analyzer = ContentAnalyzer()
_content_classifier = ContentClassifier()
_style_recommender = StyleRecommender()


def get_prompt_validator() -> PromptValidator:
    """Get the prompt validator instance."""
    return _prompt_validator


def get_content_analyzer() -> ContentAnalyzer:
    """Get the content analyzer instance."""
    return _content_analyzer


def get_content_classifier() -> ContentClassifier:
    """Get the content classifier instance."""
    return _content_classifier


def get_style_recommender() -> StyleRecommender:
    """Get the style recommender instance."""
    return _style_recommender


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

    Flow:
    1. Validate session and Gemini API key connection
    2. Analyze post content (themes, technologies, sentiment)
    3. Classify content type
    4. Recommend image style (unless override provided)
    5. Generate image via Gemini API
    6. Log audit entry with request metadata
    7. Return image with metadata

    Args:
        request: The FastAPI request object.
        image_request: The image generation request with validated inputs.
        x_session_id: Session ID from header.

    Returns:
        ImageGenerationResponse with generated image or error.

    Raises:
        HTTPException: 400 for invalid inputs, 401 for auth issues, 429 for rate limit.
    """
    session_id = x_session_id or "default"
    gemini_storage = get_gemini_key_storage()
    audit = get_audit_logger()

    # Check Gemini API key connection
    api_key = gemini_storage.retrieve(session_id)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Not connected to Gemini. Please connect your Gemini API key first."
        )

    # Additional custom prompt validation for malicious patterns
    if image_request.custom_prompt:
        validator = get_prompt_validator()
        validation_result = validator.validate(image_request.custom_prompt)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=validation_result.error_message or "Invalid prompt"
            )

    # Step 1: Analyze the post content
    analyzer = get_content_analyzer()
    try:
        analysis = analyzer.analyze(image_request.post_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2: Classify the content type
    classifier = get_content_classifier()
    classification = classifier.classify(analysis, image_request.post_content)

    # Step 3: Get style recommendation (or use override)
    recommender = get_style_recommender()
    recommendation = recommender.recommend(
        classification.content_type,
        analysis.technologies,
        analysis
    )

    # Use style override if provided, otherwise use first recommended style
    if image_request.style:
        selected_style = image_request.style
    else:
        selected_style = ImageStyle(recommendation.styles[0]) if recommendation.styles else ImageStyle.MINIMALIST

    # Step 4: Build the prompt using Nano Banana optimized builder
    if image_request.custom_prompt:
        prompt = image_request.custom_prompt
    else:
        prompt_builder = get_prompt_builder()
        prompt = prompt_builder.build_prompt(
            post_content=image_request.post_content,
            style=selected_style,
            content_type=classification.content_type,
            dimensions=image_request.dimensions.value,
            technologies=analysis.technologies,
            keywords=analysis.keywords,
            visual_elements=analysis.suggested_visual_elements,
            sentiment=analysis.sentiment,
        )

    # Step 5: Generate the image
    client = GeminiClient(api_key)
    try:
        result = await client.generate_image(
            prompt=prompt,
            dimensions=image_request.dimensions.value,
        )

        if result.success:
            # Log successful image generation (no prompt content in audit log)
            audit.log_image_generation(
                session_id=session_id,
                status=AuditStatus.SUCCESS,
                dimensions=image_request.dimensions.value,
                style=selected_style.value,
                content_type=classification.content_type.value,
            )

            return ImageGenerationResponse(
                success=True,
                image_base64=result.image_base64,
                content_type=classification.content_type,
                recommended_style=selected_style,
                dimensions=image_request.dimensions.value,
                prompt_used=prompt,
            )
        else:
            # Log failed image generation
            audit.log_image_generation(
                session_id=session_id,
                status=AuditStatus.FAILURE,
                dimensions=image_request.dimensions.value,
                style=selected_style.value,
                content_type=classification.content_type.value,
                error_message=result.error or "Failed to generate image",
            )

            return ImageGenerationResponse(
                success=False,
                error=result.error or "Failed to generate image",
                dimensions=image_request.dimensions.value,
                content_type=classification.content_type,
                recommended_style=selected_style,
                prompt_used=prompt,
            )

    except RateLimitError as e:
        # Log rate limit error
        import logging
        logging.warning(f"[RATE LIMIT] Gemini API blocked request - retry_after={e.retry_after}s")
        audit.log_image_generation(
            session_id=session_id,
            status=AuditStatus.FAILURE,
            dimensions=image_request.dimensions.value,
            style=selected_style.value,
            content_type=classification.content_type.value,
            error_message="Rate limit exceeded",
            request_metadata={"retry_after": e.retry_after},
        )

        raise HTTPException(
            status_code=429,
            detail=f"{e.message} (Gemini API limit)",
            headers={"Retry-After": str(e.retry_after)}
        )
    except GeminiAPIError as e:
        # Log API error
        audit.log_image_generation(
            session_id=session_id,
            status=AuditStatus.FAILURE,
            dimensions=image_request.dimensions.value,
            style=selected_style.value,
            content_type=classification.content_type.value,
            error_message=e.message,
        )

        # Return as error response, not exception
        return ImageGenerationResponse(
            success=False,
            error=e.message,
            dimensions=image_request.dimensions.value,
            content_type=classification.content_type,
            recommended_style=selected_style,
            prompt_used=prompt,
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
