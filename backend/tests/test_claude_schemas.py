"""Tests for Claude authentication and generation Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.models.claude_schemas import (
    ClaudeAuthRequest,
    ClaudeAuthResponse,
    ClaudeGenerateRequest,
    ClaudeGenerateResponse,
)
from src.models.schemas import (
    AnalysisResult,
    PostStyle,
    TechStackItem,
    Feature,
)


class TestClaudeAuthRequest:
    """Tests for ClaudeAuthRequest model."""

    def test_valid_api_key(self):
        """Test that valid API key is accepted."""
        request = ClaudeAuthRequest(api_key="sk-ant-api03-valid-key-xyz")
        assert request.api_key == "sk-ant-api03-valid-key-xyz"

    def test_api_key_is_required(self):
        """Test that api_key is a required field."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeAuthRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("api_key",) for e in errors)
        assert any(e["type"] == "missing" for e in errors)

    def test_api_key_cannot_be_empty(self):
        """Test that empty api_key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeAuthRequest(api_key="")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_key_cannot_be_whitespace_only(self):
        """Test that whitespace-only api_key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeAuthRequest(api_key="   ")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_key_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped from api_key."""
        request = ClaudeAuthRequest(api_key="  sk-valid-key  ")
        assert request.api_key == "sk-valid-key"


class TestClaudeAuthResponse:
    """Tests for ClaudeAuthResponse model."""

    def test_connected_response(self):
        """Test connected response with masked key."""
        response = ClaudeAuthResponse(
            connected=True,
            masked_key="****xyz9"
        )
        assert response.connected is True
        assert response.masked_key == "****xyz9"
        assert response.error is None

    def test_disconnected_response(self):
        """Test disconnected response."""
        response = ClaudeAuthResponse(connected=False)
        assert response.connected is False
        assert response.masked_key is None
        assert response.error is None

    def test_error_response(self):
        """Test error response."""
        response = ClaudeAuthResponse(
            connected=False,
            error="Invalid API key"
        )
        assert response.connected is False
        assert response.error == "Invalid API key"

    def test_connected_field_is_required(self):
        """Test that connected field is required."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeAuthResponse()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("connected",) for e in errors)


class TestClaudeGenerateRequest:
    """Tests for ClaudeGenerateRequest model."""

    @pytest.fixture
    def sample_analysis(self) -> AnalysisResult:
        """Create a sample analysis result for testing."""
        return AnalysisResult(
            repo_name="test-repo",
            description="A test repository",
            stars=100,
            forks=25,
            language="Python",
            tech_stack=[
                TechStackItem(name="FastAPI", category="framework"),
                TechStackItem(name="Python", category="language"),
            ],
            features=[
                Feature(name="API Endpoints", description="REST API endpoints"),
            ],
            readme_summary="A great test repo",
            file_structure=["src/", "tests/", "README.md"]
        )

    def test_valid_generate_request(self, sample_analysis):
        """Test valid generate request."""
        request = ClaudeGenerateRequest(
            analysis=sample_analysis,
            style=PostStyle.TIPS_LEARNINGS
        )
        assert request.analysis.repo_name == "test-repo"
        assert request.style == PostStyle.TIPS_LEARNINGS

    def test_analysis_field_is_required(self):
        """Test that analysis field is required."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeGenerateRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("analysis",) for e in errors)

    def test_default_style(self, sample_analysis):
        """Test that style defaults to PROBLEM_SOLUTION."""
        request = ClaudeGenerateRequest(analysis=sample_analysis)
        assert request.style == PostStyle.PROBLEM_SOLUTION

    def test_all_style_values(self, sample_analysis):
        """Test that all PostStyle values are accepted."""
        for style in PostStyle:
            request = ClaudeGenerateRequest(
                analysis=sample_analysis,
                style=style
            )
            assert request.style == style


class TestClaudeGenerateResponse:
    """Tests for ClaudeGenerateResponse model."""

    def test_success_response(self):
        """Test successful generation response."""
        response = ClaudeGenerateResponse(
            success=True,
            content="Here's a great LinkedIn post about this repo...",
            style=PostStyle.TECHNICAL_SHOWCASE
        )
        assert response.success is True
        assert response.content is not None
        assert response.style == PostStyle.TECHNICAL_SHOWCASE
        assert response.error is None
        assert response.retry_after is None

    def test_error_response(self):
        """Test error generation response."""
        response = ClaudeGenerateResponse(
            success=False,
            error="Rate limit exceeded"
        )
        assert response.success is False
        assert response.content is None
        assert response.error == "Rate limit exceeded"

    def test_rate_limit_response(self):
        """Test rate limit response with retry_after."""
        response = ClaudeGenerateResponse(
            success=False,
            error="Rate limit exceeded",
            retry_after=60
        )
        assert response.success is False
        assert response.retry_after == 60

    def test_success_field_is_required(self):
        """Test that success field is required."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeGenerateResponse()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("success",) for e in errors)
