"""LinkedIn post repurposing routes."""

from fastapi import APIRouter, HTTPException, Header, Response
from typing import Optional

from src.models.linkedin_models import (
    LinkedInContentRequest,
    LinkedInAnalyzeResponse,
    ContentAnalysisResult,
    RepurposeRequest,
    RepurposeResponse,
)
from src.models.schemas import Provider
from src.analyzers.linkedin_analyzer import LinkedInAnalyzer
from src.generators.repurpose_generator import (
    RepurposeGenerator,
    extract_image_context,
    suggest_hashtags,
)
from src.services.claude_client import ClaudeClient
from src.services.openai_client import OpenAIClient
from src.api.claude_routes import get_key_storage
from src.api.openai_routes import get_openai_key_storage

router = APIRouter(prefix="/linkedin", tags=["linkedin-repurpose"])


@router.post("/analyze", response_model=LinkedInAnalyzeResponse)
async def analyze_linkedin_content(
    request: LinkedInContentRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> LinkedInAnalyzeResponse:
    """Analyze pasted LinkedIn post content using AI.

    Extracts themes, tone, content type, key points, entities, and hashtags.
    Uses AI analysis when an API key is available, falls back to keyword-based.

    Args:
        request: The LinkedIn content to analyze.
        x_session_id: Session ID from header.

    Returns:
        LinkedInAnalyzeResponse with analysis results.
    """
    try:
        session_id = x_session_id or "default"
        ai_client = None

        # Try to get an AI client (Claude first, then OpenAI)
        claude_storage = get_key_storage()
        openai_storage = get_openai_key_storage()

        if claude_storage.exists(session_id):
            api_key = claude_storage.retrieve(session_id)
            if api_key:
                ai_client = ClaudeClient(api_key=api_key)
        elif openai_storage.exists(session_id):
            api_key = openai_storage.retrieve(session_id)
            if api_key:
                ai_client = OpenAIClient(api_key=api_key)

        analyzer = LinkedInAnalyzer(ai_client=ai_client)
        result = analyzer.analyze(request.content)
        return LinkedInAnalyzeResponse(success=True, data=result)
    except ValueError as e:
        return LinkedInAnalyzeResponse(success=False, error=str(e))
    except Exception as e:
        return LinkedInAnalyzeResponse(success=False, error=f"Analysis failed: {str(e)}")


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_linkedin_content(
    request: RepurposeRequest,
    response: Response,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    provider: Provider = Provider.CLAUDE,
) -> RepurposeResponse:
    """Repurpose LinkedIn content with AI.

    Transforms the content based on target style and format while
    preserving the core value and insights.

    Args:
        request: Repurpose request with content, analysis, and targets.
        response: FastAPI response for headers.
        x_session_id: Session ID from header for key lookup.
        provider: AI provider to use (claude or openai).

    Returns:
        RepurposeResponse with repurposed content.

    Raises:
        HTTPException: 401 if not connected, 429 if rate limited.
    """
    session_id = x_session_id or "default"

    # Select storage based on provider
    if provider == Provider.OPENAI:
        storage = get_openai_key_storage()
        provider_name = "OpenAI"
    else:
        storage = get_key_storage()
        provider_name = "Claude"

    # Check if user has a connected API key
    if not storage.exists(session_id):
        raise HTTPException(
            status_code=401,
            detail=f"Not connected to {provider_name}. Please connect your API key first."
        )

    # Retrieve the API key
    api_key = storage.retrieve(session_id)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Failed to retrieve API key. Please reconnect."
        )

    # Build prompts for repurposing
    system_prompt, user_prompt = RepurposeGenerator.build_prompts(
        original_content=request.original_content,
        analysis=request.analysis,
        target_style=request.target_style,
        target_format=request.target_format,
    )

    # Generate repurposed content
    if provider == Provider.OPENAI:
        client = OpenAIClient(api_key=api_key)
        result = client.generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    else:
        client = ClaudeClient(api_key=api_key)
        result = client.generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    # Handle rate limit
    if not result.success and result.retry_after is not None:
        response.headers["Retry-After"] = str(result.retry_after)
        raise HTTPException(
            status_code=429,
            detail=result.error or "Rate limit exceeded",
            headers={"Retry-After": str(result.retry_after)}
        )

    # Handle other errors
    if not result.success:
        return RepurposeResponse(
            success=False,
            error=result.error,
        )

    repurposed_content = result.content or ""

    # Extract image context for optional image generation
    image_context = extract_image_context(repurposed_content, request.analysis)

    # Suggest hashtags
    suggested_hashtags = suggest_hashtags(request.analysis, repurposed_content)

    return RepurposeResponse(
        success=True,
        repurposed_content=repurposed_content,
        suggested_hashtags=suggested_hashtags,
        image_context=image_context,
    )
