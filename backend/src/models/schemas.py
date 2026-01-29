from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum


class InsightType(str, Enum):
    """Type of project insight."""
    STRENGTH = "strength"
    CONSIDERATION = "consideration"
    HIGHLIGHT = "highlight"


class ProjectInsight(BaseModel):
    """A single insight about the project."""
    type: InsightType
    title: str
    description: str
    icon: str


class Provider(str, Enum):
    """Available AI providers for content generation."""
    CLAUDE = "claude"
    OPENAI = "openai"


class PostStyle(str, Enum):
    PROBLEM_SOLUTION = "problem-solution"
    TIPS_LEARNINGS = "tips-learnings"
    TECHNICAL_SHOWCASE = "technical-showcase"


class RepositoryOwnership(str, Enum):
    """Whether the user owns the repository or discovered it."""
    OWN = "own"
    DISCOVERED = "discovered"


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL")
    token: Optional[str] = Field(None, description="GitHub token for private repos")


class TechStackItem(BaseModel):
    name: str
    category: str  # language, framework, library, tool


class Feature(BaseModel):
    name: str
    description: str


class AnalysisResult(BaseModel):
    repo_name: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    tech_stack: list[TechStackItem]
    features: list[Feature]  # Merged features + highlights
    readme_summary: Optional[str]  # Fallback text summary
    ai_summary: Optional[str] = None  # AI-generated summary
    file_structure: list[str]
    insights: list[ProjectInsight] = []  # Only strengths + considerations


class GenerateRequest(BaseModel):
    analysis: AnalysisResult
    style: PostStyle = PostStyle.PROBLEM_SOLUTION


class GeneratedPrompt(BaseModel):
    style: PostStyle
    prompt: str
    instructions: str


class TemplateInfo(BaseModel):
    id: PostStyle
    name: str
    description: str


class AnalyzeResponse(BaseModel):
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None


class GenerateResponse(BaseModel):
    success: bool
    data: Optional[GeneratedPrompt] = None
    error: Optional[str] = None
