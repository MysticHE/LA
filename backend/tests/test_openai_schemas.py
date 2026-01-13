"""Tests for OpenAI authentication and generation Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.models.openai_schemas import (
    OpenAIAuthRequest,
    OpenAIAuthResponse,
    OpenAIGenerateRequest,
    OpenAIGenerateResponse,
    OpenAIModel,
)
from src.models.schemas import (
    AnalysisResult,
    PostStyle,
    TechStackItem,
    Feature,
)


class TestOpenAIAuthRequest:
    """Tests for OpenAIAuthRequest model."""

    def test_valid_api_key(self):
        """Test that valid API key starting with sk- is accepted."""
        # Construct a valid key with proper length (40-200 chars)
        valid_key = "sk-" + "x" * 45  # 48 chars total
        request = OpenAIAuthRequest(api_key=valid_key)
        assert request.api_key == valid_key

    def test_api_key_is_required(self):
        """Test that api_key is a required field."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("api_key",) for e in errors)
        assert any(e["type"] == "missing" for e in errors)

    def test_api_key_cannot_be_empty(self):
        """Test that empty api_key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest(api_key="")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_key_cannot_be_whitespace_only(self):
        """Test that whitespace-only api_key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest(api_key="   ")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_key_must_start_with_sk(self):
        """Test that API key must start with 'sk-'."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest(api_key="invalid-key-format-" + "x" * 30)

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("sk-" in str(e.get("msg", "")) for e in errors)

    def test_api_key_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped from api_key."""
        valid_key = "sk-" + "x" * 45
        request = OpenAIAuthRequest(api_key=f"  {valid_key}  ")
        assert request.api_key == valid_key

    def test_api_key_too_short(self):
        """Test that API key shorter than 40 chars is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest(api_key="sk-short")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_key_too_long(self):
        """Test that API key longer than 200 chars is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthRequest(api_key="sk-" + "x" * 200)

        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestOpenAIAuthResponse:
    """Tests for OpenAIAuthResponse model."""

    def test_connected_response(self):
        """Test connected response with masked key."""
        response = OpenAIAuthResponse(
            connected=True,
            masked_key="sk-...xyz9"
        )
        assert response.connected is True
        assert response.masked_key == "sk-...xyz9"
        assert response.error is None

    def test_disconnected_response(self):
        """Test disconnected response."""
        response = OpenAIAuthResponse(connected=False)
        assert response.connected is False
        assert response.masked_key is None
        assert response.error is None

    def test_error_response(self):
        """Test error response."""
        response = OpenAIAuthResponse(
            connected=False,
            error="Invalid API key"
        )
        assert response.connected is False
        assert response.error == "Invalid API key"

    def test_connected_field_is_required(self):
        """Test that connected field is required."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAuthResponse()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("connected",) for e in errors)


class TestOpenAIModel:
    """Tests for OpenAIModel enum."""

    def test_gpt_4o_value(self):
        """Test GPT-4O enum value."""
        assert OpenAIModel.GPT_4O.value == "gpt-4o"

    def test_gpt_4_value(self):
        """Test GPT-4 enum value."""
        assert OpenAIModel.GPT_4.value == "gpt-4"

    def test_gpt_35_turbo_value(self):
        """Test GPT-3.5-turbo enum value."""
        assert OpenAIModel.GPT_35_TURBO.value == "gpt-3.5-turbo"


class TestOpenAIGenerateRequest:
    """Tests for OpenAIGenerateRequest model."""

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
        request = OpenAIGenerateRequest(
            analysis=sample_analysis,
            style=PostStyle.TIPS_LEARNINGS,
            model=OpenAIModel.GPT_4
        )
        assert request.analysis.repo_name == "test-repo"
        assert request.style == PostStyle.TIPS_LEARNINGS
        assert request.model == OpenAIModel.GPT_4

    def test_analysis_field_is_required(self):
        """Test that analysis field is required."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIGenerateRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("analysis",) for e in errors)

    def test_default_style(self, sample_analysis):
        """Test that style defaults to PROBLEM_SOLUTION."""
        request = OpenAIGenerateRequest(analysis=sample_analysis)
        assert request.style == PostStyle.PROBLEM_SOLUTION

    def test_default_model(self, sample_analysis):
        """Test that model defaults to GPT_4O."""
        request = OpenAIGenerateRequest(analysis=sample_analysis)
        assert request.model == OpenAIModel.GPT_4O

    def test_all_style_values(self, sample_analysis):
        """Test that all PostStyle values are accepted."""
        for style in PostStyle:
            request = OpenAIGenerateRequest(
                analysis=sample_analysis,
                style=style
            )
            assert request.style == style

    def test_all_model_values(self, sample_analysis):
        """Test that all OpenAIModel values are accepted."""
        for model in OpenAIModel:
            request = OpenAIGenerateRequest(
                analysis=sample_analysis,
                model=model
            )
            assert request.model == model

    def test_invalid_model_value(self, sample_analysis):
        """Test that invalid model value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIGenerateRequest(
                analysis=sample_analysis,
                model="gpt-5-invalid"
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("model",) for e in errors)


class TestOpenAIGenerateResponse:
    """Tests for OpenAIGenerateResponse model."""

    def test_success_response(self):
        """Test successful generation response."""
        response = OpenAIGenerateResponse(
            success=True,
            content="Here's a great LinkedIn post about this repo...",
            style=PostStyle.TECHNICAL_SHOWCASE,
            model=OpenAIModel.GPT_4O
        )
        assert response.success is True
        assert response.content is not None
        assert response.style == PostStyle.TECHNICAL_SHOWCASE
        assert response.model == OpenAIModel.GPT_4O
        assert response.error is None
        assert response.retry_after is None

    def test_error_response(self):
        """Test error generation response."""
        response = OpenAIGenerateResponse(
            success=False,
            error="Rate limit exceeded"
        )
        assert response.success is False
        assert response.content is None
        assert response.error == "Rate limit exceeded"

    def test_rate_limit_response(self):
        """Test rate limit response with retry_after."""
        response = OpenAIGenerateResponse(
            success=False,
            error="Rate limit exceeded",
            retry_after=60
        )
        assert response.success is False
        assert response.retry_after == 60

    def test_success_field_is_required(self):
        """Test that success field is required."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIGenerateResponse()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("success",) for e in errors)
