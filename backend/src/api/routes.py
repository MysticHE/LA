from typing import Optional

from fastapi import APIRouter, Header
from src.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    GenerateRequest,
    GenerateResponse,
    TemplateInfo,
    PostStyle,
)
from src.analyzers.github_analyzer import GitHubAnalyzer
from src.generators.prompt_builder import PromptBuilder
from src.api.openai_routes import get_openai_key_storage
from src.services.openai_client import OpenAIClient

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(
    request: AnalyzeRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """Analyze a GitHub repository and extract key information."""
    try:
        session_id = x_session_id or "default"

        # Get OpenAI client for AI-powered feature extraction if available
        openai_client = None
        storage = get_openai_key_storage()
        if storage.exists(session_id):
            api_key = storage.retrieve(session_id)
            if api_key:
                openai_client = OpenAIClient(api_key=api_key)

        analyzer = GitHubAnalyzer(token=request.token, openai_client=openai_client)
        result = await analyzer.analyze(request.url)
        return AnalyzeResponse(success=True, data=result)
    except ValueError as e:
        return AnalyzeResponse(success=False, error=str(e))
    except Exception as e:
        return AnalyzeResponse(success=False, error=f"Analysis failed: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_prompt(request: GenerateRequest):
    """Generate a LinkedIn post prompt from analysis results."""
    try:
        builder = PromptBuilder()
        prompt = builder.build(request.analysis, request.style)
        return GenerateResponse(success=True, data=prompt)
    except Exception as e:
        return GenerateResponse(success=False, error=f"Generation failed: {str(e)}")


@router.get("/templates", response_model=list[TemplateInfo])
async def get_templates():
    """Get available post style templates."""
    return [
        TemplateInfo(
            id=PostStyle.PROBLEM_SOLUTION,
            name="Problem-Solution",
            description="Start with a relatable problem, then present your project as the solution",
        ),
        TemplateInfo(
            id=PostStyle.TIPS_LEARNINGS,
            name="Tips & Learnings",
            description="Share key insights and lessons learned while building the project",
        ),
        TemplateInfo(
            id=PostStyle.TECHNICAL_SHOWCASE,
            name="Technical Showcase",
            description="Highlight the architecture, tech stack, and technical decisions",
        ),
    ]
