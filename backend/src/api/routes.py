from fastapi import APIRouter, HTTPException
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

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest):
    """Analyze a GitHub repository and extract key information."""
    try:
        analyzer = GitHubAnalyzer(token=request.token)
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
