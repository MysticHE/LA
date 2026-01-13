"""AI content generation routes."""

from fastapi import APIRouter, HTTPException, Header, Response
from typing import Optional

from src.models.claude_schemas import (
    ClaudeGenerateRequest,
    ClaudeGenerateResponse,
)
from src.models.schemas import Provider
from src.services.claude_client import ClaudeClient
from src.services.openai_client import OpenAIClient
from src.generators.ai_prompt_generator import AIPromptGenerator
from src.api.claude_routes import get_key_storage
from src.api.openai_routes import get_openai_key_storage

# Create router for generation endpoints
router = APIRouter(prefix="/generate", tags=["ai-generation"])


@router.post("/ai-post", response_model=ClaudeGenerateResponse)
async def generate_ai_post(
    request: ClaudeGenerateRequest,
    response: Response,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> ClaudeGenerateResponse:
    """Generate a LinkedIn post using the specified AI provider.

    Args:
        request: The generation request with analysis, style, and optional provider.
        response: FastAPI response object for setting headers.
        x_session_id: Session ID from header for key lookup.

    Returns:
        ClaudeGenerateResponse with generated content or error.

    Raises:
        HTTPException: 401 if not connected, 429 if rate limited.
    """
    session_id = x_session_id or "default"

    # Select storage based on provider
    if request.provider == Provider.OPENAI:
        storage = get_openai_key_storage()
        provider_name = "OpenAI"
    else:
        storage = get_key_storage()
        provider_name = "Claude"

    # Check if user has a connected API key for the provider
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

    # Generate prompts using the AI prompt generator
    system_prompt, user_prompt = AIPromptGenerator.generate_prompt(
        analysis=request.analysis,
        style=request.style
    )

    # Create client and generate content based on provider
    if request.provider == Provider.OPENAI:
        client = OpenAIClient(api_key=api_key)
        # Pass model if specified, otherwise use default
        model = request.model.value if request.model else None
        result = client.generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model
        )
    else:
        client = ClaudeClient(api_key=api_key)
        result = client.generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

    # Handle rate limit with 429 response
    if not result.success and result.retry_after is not None:
        response.headers["Retry-After"] = str(result.retry_after)
        raise HTTPException(
            status_code=429,
            detail=result.error or "Rate limit exceeded",
            headers={"Retry-After": str(result.retry_after)}
        )

    # Handle other errors
    if not result.success:
        return ClaudeGenerateResponse(
            success=False,
            content=None,
            style=request.style,
            error=result.error,
        )

    # Success case
    return ClaudeGenerateResponse(
        success=True,
        content=result.content,
        style=request.style,
        error=None,
    )
